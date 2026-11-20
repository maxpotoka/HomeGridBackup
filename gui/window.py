import time
from core.i18n import tr, apply_widget_i18n
# ==============================================================================
# [ФАЙЛ: gui/window.py (v1.140 | 20.11.2026 22:08) — ГЛАВНОЕ ОКНО HOMEGRIDAPP И ФОНОВЫЙ ЦИКЛ UI]
# ==============================================================================
import os
import threading
import tkinter as tk
from core.config import SCRIPT_VER, BUILD_DATE, DEFAULT_BACKUP_DIR, commit_state
from core.files import open_folder_native, choose_folder_native
from core.network import normalize_server_url, run_connect_task, run_scan_task
from core.backup import run_backup_task
from gui.styles import UI_SCALE_LABELS, THEMES, _calc_screen_metrics, ToolTip
from gui.widgets import StyledProgressBar
from gui.tray import HAS_TRAY, _start_tray_thread
from gui.dialogs import DialogsMixin

class HomeGridApp(DialogsMixin):
    def __init__(self, root, engine):
        self.root = root
        self.root.withdraw()
        self.engine = engine
        self.metrics = _calc_screen_metrics(
            root,
            self.engine.state.get("ui_scale", "auto"),
            self.engine.state.get("ui_font", 0)
        )
        self.last_log_len = 0
        self._last_log_item = None
        self.last_modal_id = None
        self.hw_notice_shown = False
        self._srv_typing_timer = None
        self._resize_timer = None
        self._last_live_wh = (0, 0)
        self._ignore_resize_until = time.time() + 1.0

        self.root.title(f"HomeGrid Backup v{SCRIPT_VER} (від {BUILD_DATE})")
        m = self.metrics
        self.root.geometry(f"{m['win_w']}x{m['win_h']}+{m['pos_x']}+{m['pos_y']}")
        self.root.minsize(min(620, m['win_w']), min(420, m['win_h']))
        import sys
        import tkinter.font as _tkf
        _fams = set(_tkf.families(self.root)) if sys.platform.startswith("linux") else set()
        self._base_fam = "Helvetica Neue" if sys.platform == "darwin" else (next((fn for fn in ("Ubuntu", "DejaVu Sans", "Liberation Sans", "Noto Sans") if fn in _fams), "Sans") if sys.platform.startswith("linux") else "Segoe UI")
        self._mono_fam = "Menlo" if sys.platform == "darwin" else ("DejaVu Sans Mono" if sys.platform.startswith("linux") else "Consolas")
        self.F_MAIN = _tkf.Font(root=self.root, family=self._base_fam, size=m["font_sz"])
        self.F_BOLD = _tkf.Font(root=self.root, family=self._base_fam, size=m["font_sz"], weight="bold")
        self.F_SUB = _tkf.Font(root=self.root, family=self._base_fam, size=max(8, m["font_sz"] - 1))
        self.F_CAP = _tkf.Font(root=self.root, family=self._base_fam, size=max(8, m["font_sz"] - 2), weight="bold")
        self.F_TITLE = _tkf.Font(root=self.root, family=self._base_fam, size=m["font_sz"] + 4, weight="bold")
        self._watch_pending = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.var_srv = tk.StringVar(value=self.engine.state.get("server", ""))
        self.var_dir = tk.StringVar(value=self.engine.state.get("backup_dir", ""))
        self.var_mirror = tk.StringVar(value=self.engine.state.get("mirror_dir", ""))
        self.var_net = tk.StringVar(value="Не перевірено")
        self.var_disk = tk.StringVar(value="0 архівів (0 МБ)")
        self.var_last_bkp = tk.StringVar(value="Перевірка...")
        self.var_strat = tk.StringVar(value="")
        self.var_stage = tk.StringVar(value=self.engine.stage)
        self.var_pct = tk.StringVar(value="0%")

        if sys.platform == "darwin":
            self.root.bind_class("Entry", "<Command-v>", lambda e: e.widget.event_generate("<<Paste>>"))
            self.root.bind_class("Entry", "<Command-c>", lambda e: e.widget.event_generate("<<Copy>>"))
            self.root.bind_class("Entry", "<Command-x>", lambda e: e.widget.event_generate("<<Cut>>"))
            self.root.bind_class("Entry", "<Command-a>", lambda e: (e.widget.select_range(0, "end"), "break")[1])
        elif sys.platform.startswith("linux"):
            def _x11_ctrl_key(e):
                if not (e.state & 0x4):
                    return
                kc_map = {54: "<<Copy>>", 55: "<<Paste>>", 53: "<<Cut>>"}
                if e.keycode in kc_map:
                    e.widget.event_generate(kc_map[e.keycode])
                    return "break"
                if e.keycode == 38:
                    e.widget.select_range(0, "end")
                    return "break"
            self.root.bind_class("Entry", "<KeyPress>", _x11_ctrl_key, add="+")
        self._build_ui()
        self.apply_theme_and_mode()
        self.root.deiconify()
        self.root.resizable(True, True)
        self.root.minsize(620, 420)
        self.root.update_idletasks()
        self._last_live_wh = (self.root.winfo_width(), self.root.winfo_height())
        self.root.after(250, self._watch_size)
        self.root.after(300, self._poll_ui)

    def _warmup_ttk_styles(self):
        try:
            tw = tk.Toplevel(self.root)
            tw.withdraw()
            tw.geometry("1x1+-100+-100")
            tw.update_idletasks()
            tw.destroy()
        except Exception:
            pass

    def _watch_size(self):
        try:
            if not self.root.winfo_exists():
                return
            if time.time() >= getattr(self, "_ignore_resize_until", 0) and self.root.state() != "iconic":
                w, h = self.root.winfo_width(), self.root.winfo_height()
                if w >= 500 and h >= 350:
                    if (w, h) != self._last_live_wh:
                        self._last_live_wh = (w, h)
                        self._watch_pending = (w, h)
                    elif self._watch_pending is not None:
                        pw, ph = self._watch_pending
                        self._watch_pending = None
                        self._on_live_resize_done(pw, ph)
        except Exception:
            pass
        self.root.after(200, self._watch_size)

    def _on_live_resize_done(self, cw, ch):
        m = self.metrics
        ow = cw + (m["outer_w"] - m["win_w"])
        oh = ch + (m["outer_h"] - m["win_h"])
        st = self.engine.state
        if st.get("ui_font", 0) != 0 or st.get("ui_scale", "auto") != "auto":
            st["ui_font"] = 0
            st["ui_scale"] = "auto"
            commit_state(st)
        self.apply_theme_and_mode(resize_win=False, live_outer_wh=(ow, oh))
        self.root.update_idletasks()
        self._last_live_wh = (self.root.winfo_width(), self.root.winfo_height())

    def show_window(self):
        import sys
        self._ignore_resize_until = time.time() + 0.7
        try:
            if self.root.state() in ("iconic", "withdrawn"):
                self.root.deiconify()
                self.root.state("normal")
            if not sys.platform.startswith("linux"):
                self.root.attributes("-topmost", True)
                self.root.update_idletasks()
                self.root.attributes("-topmost", False)
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def on_window_close(self):
        import sys
        if sys.platform == "darwin":
            if bool(self.engine.state.get("minimize_to_tray", True)):
                self.root.iconify()
                self.engine.log("Вікно згорнуто у Dock (програма продовжує роботу).", "info")
                return
            if getattr(self, "_exit_confirm_open", False):
                from gui.tray import _force_quit_app
                _force_quit_app(self.engine)
                return
            self._exit_confirm_open = True
            self.confirm_exit()
            return
        keep_tray = bool(self.engine.state.get("minimize_to_tray", True))
        if keep_tray and HAS_TRAY:
            try:
                if self.engine.tray_icon is None:
                    _start_tray_thread(self.engine)
                if self.engine.tray_icon is not None:
                    self.root.withdraw()
                    self.engine.log("Вікно згорнуто у системний трей (програма продовжує роботу).", "info")
                    return
            except Exception:
                pass
        self.confirm_exit()

    def _get_palette(self):
        t_name = self.engine.state.get("theme", "dark")
        if self.engine.state.get("lite_mode", False):
            return {
                "bg": "#000000", "panel": "#050505", "card": "#0a0a0a", "border": "#4b5563",
                "text": "#f3f4f6", "muted": "#9ca3af", "blue": "#1d4ed8", "green": "#047857",
                "amber": "#b45309", "red": "#b91c1c", "cyan": "#38bdf8",
                "inp_bg": "#000000", "log_bg": "#000000", "btn_txt": "#ffffff", "green_txt": "#ffffff",
                "font": "Consolas", "relief": "solid"
            }
        return THEMES.get(t_name, THEMES["dark"])

    def _on_srv_key_release(self, event=None):
        if event and event.keysym in ("BackSpace", "Delete", "Left", "Right", "Home", "End", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return
        if self._srv_typing_timer:
            try:
                self.root.after_cancel(self._srv_typing_timer)
            except Exception:
                pass
        self._srv_typing_timer = self.root.after(800, self._apply_srv_autofill)

    def _build_ui(self):
        py, px = self.metrics["pad_y"], self.metrics["pad_x"]
        fs = self.metrics["font_sz"]
        self.header = tk.Frame(self.root, padx=px, pady=py, bd=1, relief="solid")
        self.header.pack(side="top", fill="x")

        hdr_left = tk.Frame(self.header)
        hdr_left.pack(side="left", fill="x", expand=True)
        self.lbl_title = tk.Label(hdr_left, text="HomeGrid Backup", font=("Segoe UI", fs + 4, "bold"))
        self.lbl_title.pack(anchor="w")
        self.lbl_sub = tk.Label(hdr_left, text="", font=("Segoe UI", 1))

        hdr_right = tk.Frame(self.header)
        hdr_right.pack(side="right")
        self.btn_mode = tk.Button(hdr_right, text="Графіка (1920×1080) ▾", command=self.open_mode_menu, padx=10, pady=4, cursor="hand2")
        self.btn_mode.pack(side="left", padx=(6, 0))
        ToolTip(self.btn_mode, "Оберіть режим (Графіка / LITE) або роздільну здатність вікна")

        self.footer = tk.Frame(self.root, padx=px, pady=py, bd=1, relief="solid")
        self.footer.pack(side="bottom", fill="x")

        self.body = tk.Frame(self.root, padx=px, pady=py)
        self.body.pack(side="top", fill="both", expand=True)

        self.card_conn = tk.Frame(self.body, padx=px, pady=py, bd=1, relief="solid")
        self.card_conn.pack(fill="x", pady=(0, py))
        self.lbl_c1 = tk.Label(self.card_conn, text="Підключення до сервера та папки збереження", font=("Segoe UI", fs, "bold"))
        self.lbl_c1.pack(anchor="w", pady=(0, 4))

        conn_grid = tk.Frame(self.card_conn)
        conn_grid.pack(fill="x", pady=(2, 0))
        conn_grid.columnconfigure(1, weight=1)
        for c_btn in (2, 3, 4):
            conn_grid.columnconfigure(c_btn, weight=0, uniform="b")

        self.l_srv = tk.Label(conn_grid, text="Адреса:", anchor="w", font=("Segoe UI", fs))
        self.l_srv.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        self.ent_srv = tk.Entry(conn_grid, width=1, textvariable=self.var_srv, bd=1, relief="solid", font=("Segoe UI", fs))
        self.ent_srv.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=2, ipady=2)
        self.btn_hist = tk.Button(conn_grid, text="Історія", command=self.open_history_modal, padx=8, pady=2, cursor="hand2")
        self.btn_hist.grid(row=0, column=2, sticky="ew", padx=(0, 4), pady=2)
        self.btn_conn = tk.Button(conn_grid, text="Підключити", command=self.do_connect, padx=10, pady=2, cursor="hand2")
        self.btn_conn.grid(row=0, column=3, sticky="ew", padx=(0, 4), pady=2)
        self.btn_scan = tk.Button(conn_grid, text="Автопошук", command=self.do_scan, padx=8, pady=2, cursor="hand2")
        self.btn_scan.grid(row=0, column=4, sticky="ew", pady=2)
        self.btn_pick_lan = tk.Button(conn_grid, text="Виявлені (0)", command=self.open_discovered_menu, state="disabled", padx=8, pady=2, cursor="hand2")
        ToolTip(self.btn_pick_lan, "Список серверів, виявлених під час останнього сканування локальної мережі")
        self.ent_srv.bind("<Return>", lambda e: (self._apply_srv_autofill(), self.do_connect()))
        self.ent_srv.bind("<FocusOut>", lambda e: self._apply_srv_autofill())
        self.ent_srv.bind("<KeyRelease>", self._on_srv_key_release)

        self.l_dir = tk.Label(conn_grid, text="Папка:", anchor="w", font=("Segoe UI", fs))
        self.l_dir.grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        self.ent_dir = tk.Entry(conn_grid, width=1, textvariable=self.var_dir, bd=1, relief="solid", font=("Segoe UI", fs))
        self.ent_dir.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=2, ipady=2)
        self.btn_dir = tk.Button(conn_grid, text="Папка архівів...", command=self.choose_dir, padx=8, pady=2, cursor="hand2")
        self.btn_dir.grid(row=1, column=2, columnspan=2, sticky="ew", padx=(0, 4), pady=2)
        self.btn_open_dir = tk.Button(conn_grid, text="Відкрити папку", command=self.open_backup_folder, padx=8, pady=2, cursor="hand2")
        self.btn_open_dir.grid(row=1, column=4, sticky="ew", pady=2)
        self.ent_dir.bind("<FocusOut>", lambda e: self.save_dir_manual())

        self.l_mir = tk.Label(conn_grid, text="Дзеркало:", anchor="w", font=("Segoe UI", fs))
        self.l_mir.grid(row=2, column=0, sticky="w", padx=(0, 6), pady=2)
        self.ent_mir = tk.Entry(conn_grid, width=1, textvariable=self.var_mirror, state="disabled", bd=1, relief="solid", font=("Segoe UI", fs))
        self.ent_mir.grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=2, ipady=2)
        self.btn_mir = tk.Button(conn_grid, text="Папка дзеркала...", command=self.choose_mirror, state="disabled", padx=8, pady=2)
        self.btn_mir.grid(row=2, column=2, columnspan=2, sticky="ew", padx=(0, 4), pady=2)
        self.var_mir_en = tk.BooleanVar(value=bool(self.engine.state.get("mirror_enabled", False)) and bool(self.var_mirror.get().strip()))
        self.chk_mir_tog = tk.Checkbutton(conn_grid, text="Увімкнено", variable=self.var_mir_en, command=self.toggle_mirror, cursor="hand2")
        self.chk_mir_tog.grid(row=2, column=4, sticky="w", pady=2)
        self.ent_mir.bind("<FocusOut>", lambda e: self.save_mirror_manual())

        self.card_stat = tk.Frame(self.body, padx=12, pady=py, bd=1, relief="solid")
        self.card_stat.pack(fill="x", pady=(0, py))
        stat_row = tk.Frame(self.card_stat)
        stat_row.pack(fill="x")

        stat_row.columnconfigure(0, weight=1)
        stat_row.columnconfigure(1, weight=0)

        t2 = tk.Frame(stat_row)
        t2.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.t2_cap = tk.Label(t2, text="ЛОКАЛЬНЕ СХОВИЩЕ:", font=("Segoe UI", max(8, fs - 1), "bold"))
        self.t2_cap.pack(side="left", padx=(0, 6))
        self.t2_val = tk.Label(t2, textvariable=self.var_disk, font=("Segoe UI", fs, "bold"))
        self.t2_val.pack(side="left")

        t3 = tk.Frame(stat_row)
        t3.grid(row=1, column=0, sticky="w", padx=(0, 12), pady=(3, 0))
        self.t3_cap = tk.Label(t3, text="ОСТАННІЙ АРХІВ:", font=("Segoe UI", max(8, fs - 1), "bold"))
        self.t3_cap.pack(side="left", padx=(0, 6))
        self.t3_val = tk.Label(t3, textvariable=self.var_last_bkp, font=("Segoe UI", fs, "bold"))
        self.t3_val.pack(side="left")

        self.stat_btns = tk.Frame(stat_row)
        self.stat_btns.grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.btn_stats = tk.Button(self.stat_btns, text="Статистика", command=self.open_stats_modal, padx=10, pady=5, cursor="hand2")
        self.btn_stats.pack(side="left", padx=(0, 6))
        self.btn_ops_hist = tk.Button(self.stat_btns, text="Журнал операцій", command=self.open_ops_history, padx=10, pady=5, cursor="hand2")
        self.btn_ops_hist.pack(side="left", padx=(0, 6))
        self.btn_analyze = tk.Button(self.stat_btns, text="Аналіз GFS / SHA-256", command=self.open_analyze, padx=12, pady=5, cursor="hand2")
        self.btn_analyze.pack(side="left")
        ToolTip(self.btn_analyze, "Відкрити список архівів, керування мітками KEEP та перевірку цілісності SHA-256")

        self.card_prog = tk.Frame(self.body, padx=12, pady=py, bd=1, relief="solid")
        self.card_prog.pack(fill="x", pady=(0, py))
        p_top = tk.Frame(self.card_prog)
        p_top.pack(fill="x", pady=(0, 4))
        self.lbl_stage = tk.Label(p_top, textvariable=self.var_stage, font=("Segoe UI", fs, "bold"))
        self.lbl_stage.pack(side="left")
        self.lbl_pct = tk.Label(p_top, textvariable=self.var_pct, font=("Segoe UI", fs, "bold"))
        self.lbl_pct.pack(side="right")
        self.lbl_pill = tk.Label(p_top, text="Очікування", padx=8, pady=1, bd=1, relief="solid", font=("Segoe UI", max(8, fs - 1), "bold"))
        self.lbl_pill.pack(side="right", padx=(0, 10))
        self.pbar = StyledProgressBar(self.card_prog, height=18)
        self.pbar.pack(fill="x")

        self.card_log = tk.Frame(self.body, padx=12, pady=py, bd=1, relief="solid")
        self.card_log.pack(fill="both", expand=True)
        log_hdr = tk.Frame(self.card_log)
        log_hdr.pack(fill="x", pady=(0, 4))
        self.lbl_c4 = tk.Label(log_hdr, text="Системний лог", font=("Segoe UI", fs, "bold"))
        self.lbl_c4.pack(side="left")
        self.btn_clear_log = tk.Button(log_hdr, text="Очистити", command=self.clear_log_view, padx=8, pady=1, cursor="hand2")
        self.btn_clear_log.pack(side="right")

        log_wrap = tk.Frame(self.card_log)
        log_wrap.pack(fill="both", expand=True)
        self.txt_log = tk.Text(log_wrap, height=10, wrap="word", state="disabled", font=("Segoe UI", fs), bd=1, relief="solid", padx=10, pady=6, spacing1=1, spacing3=1)
        sb = tk.Scrollbar(log_wrap, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_log.pack(side="left", fill="both", expand=True)
        self.txt_log.bind("<Configure>", lambda _e: self._center_log_vertically(), add="+")

        self.btn_start = tk.Button(self.footer, text="ЗАПУСТИТИ БЕКАП", command=self.do_backup, font=("Segoe UI", fs, "bold"), padx=16, pady=5, cursor="hand2")
        self.btn_start.pack(side="left", padx=(0, 10))
        self.btn_strat = tk.Button(self.footer, text="Налаштування", command=self.open_settings, padx=12, pady=5, cursor="hand2")
        self.btn_strat.pack(side="left", padx=8)
        self.btn_about = tk.Button(self.footer, text="Про програму", command=self.open_about, padx=12, pady=5, cursor="hand2")
        self.btn_about.pack(side="left", padx=8)
        self.btn_exit = tk.Button(self.footer, text="Вихід", command=self.confirm_exit, padx=14, pady=5, cursor="hand2")
        self.btn_exit.pack(side="right", padx=(8, 0))
        for w_tip, t_tip in (
            (self.ent_srv, "IP-адреса або URL сервера HomeGrid Monitor (додайте ! в кінці, щоб пропустити перевірку)"),
            (self.btn_hist, "Відкрити список раніше збережених адрес серверів"),
            (self.btn_conn, "Перевірити зв'язок із вказаним сервером та авторизуватися"),
            (self.btn_scan, "Автоматичний пошук серверів HomeGrid Monitor у локальній мережі"),
            (self.ent_dir, "Локальна папка для збереження ZIP-архівів та файлів .sha256"),
            (self.btn_dir, "Обрати іншу папку для збереження резервних копій"),
            (self.btn_open_dir, "Відкрити папку з архівами у файловому менеджері"),
            (self.ent_mir, "Додаткова папка для автоматичного дублювання кожного нового бекапу"),
            (self.btn_mir, "Обрати папку для дзеркального копіювання архівів"),
            (self.chk_mir_tog, "Увімкнути або вимкнути автоматичне копіювання у дзеркальну папку"),
            (self.btn_stats, "Зведена статистика копій за періодами та стан захисту SHA-256"),
            (self.btn_ops_hist, "Журнал останніх 25 операцій резервного копіювання"),
            (self.btn_clear_log, "Очистити поточні повідомлення у вікні системного логу"),
            (self.btn_start, "Запустити створення та перевірку нової резервної копії зараз"),
            (self.btn_strat, "Налаштування глибини GFS, розкладу, трею, мови та теми"),
            (self.btn_about, "Інформація про версію та можливості програми"),
            (self.btn_exit, "Завершити роботу програми та вийти"),
        ):
            ToolTip(w_tip, t_tip)

    def apply_theme_and_mode(self, resize_win=False, live_outer_wh=None):
        self.metrics = _calc_screen_metrics(
            self.root,
            self.engine.state.get("ui_scale", "auto"),
            self.engine.state.get("ui_font", 0),
            live_outer_wh=live_outer_wh
        )
        m = self.metrics
        if resize_win:
            try:
                if self.root.state() == "zoomed":
                    self.root.state("normal")
            except Exception:
                pass
            self.root.minsize(min(620, m["win_w"]), min(420, m["win_h"]))
            self.root.geometry(f"{m['win_w']}x{m['win_h']}+{m['pos_x']}+{m['pos_y']}")

        p = self._get_palette()
        fs = m["font_sz"]
        self.root._cur_font_sz = fs
        bpx, bpy = m["btn_px"], m["btn_py"]
        px, py = m["pad_x"], m["pad_y"]
        is_lite = bool(self.engine.state.get("lite_mode", False))
        cur_theme = self.engine.state.get("theme", "dark")
        import sys
        if sys.platform == "darwin":
            fam = "Menlo" if is_lite else "Helvetica Neue"
        elif sys.platform.startswith("linux"):
            import tkinter.font as _tkf; _fams = set(_tkf.families(self.root)) if not hasattr(self, "_lnx_f") else self._lnx_f; self._lnx_f = _fams; fam = "DejaVu Sans Mono" if is_lite else next((fn for fn in ("Ubuntu", "DejaVu Sans", "Liberation Sans", "Noto Sans") if fn in _fams), "Sans")
        else:
            fam = "Consolas" if is_lite else p.get("font", "Segoe UI")
        rel = "solid" if is_lite else p.get("relief", "solid")
        bd_w = 2 if rel in ("raised", "groove") else 1

        self.F_MAIN.configure(family=fam, size=fs)
        self.F_BOLD.configure(family=fam, size=fs)
        self.F_SUB.configure(family=fam, size=max(8, fs - 1))
        self.F_CAP.configure(family=fam, size=max(8, fs - 2))
        self.F_TITLE.configure(family=fam, size=fs + 4)
        f_main, f_bold, f_sub, f_cap = self.F_MAIN, self.F_BOLD, self.F_SUB, self.F_CAP

        try:
            self.root.option_add("*TCombobox*Listbox.font", f_main)
        except Exception:
            pass

        self.root.configure(bg=p["bg"])
        self.body.configure(bg=p["bg"], padx=px, pady=py)
        for frm in (self.header, self.card_conn, self.card_stat, self.card_prog, self.card_log, self.footer):
            frm.configure(bg=p["panel"], highlightbackground=p["border"], padx=px, pady=py, relief=rel, bd=bd_w)
        for parent_frm in (self.header, self.card_conn, self.card_stat, self.card_prog, self.card_log):
            for sub in parent_frm.winfo_children():
                if isinstance(sub, tk.Frame):
                    sub.configure(bg=p["panel"])
                    for sub2 in sub.winfo_children():
                        if isinstance(sub2, tk.Frame):
                            sub2.configure(bg=p["panel"])

        self.lbl_title.configure(bg=p["panel"], fg=p["text"], font=(fam, fs + 4, "bold"))
        self.lbl_sub.configure(bg=p["panel"], fg=p["muted"], font=f_sub)
        for lbl in (self.lbl_c1, self.lbl_c4, self.lbl_stage):
            lbl.configure(bg=p["panel"], fg=p["text"], font=f_bold)
        self.lbl_pct.configure(bg=p["panel"], fg=p["green"], font=f_bold)
        for lbl in (self.l_srv, self.l_dir, self.l_mir):
            lbl.configure(bg=p["panel"], fg=p["muted"], font=f_main)

        for ent in (self.ent_srv, self.ent_dir, self.ent_mir):
            ent.configure(bg=p["inp_bg"], fg=p["text"], insertbackground=p["text"], font=f_main)

        f_big = f_bold
        self.t2_cap.configure(bg=p["panel"], fg=p["muted"], font=f_cap)
        self.t2_val.configure(bg=p["panel"], fg=p["green"], font=f_big)
        if hasattr(self, "t3_cap"):
            self.t3_cap.configure(bg=p["panel"], fg=p["muted"], font=f_cap)
            self.t3_val.configure(bg=p["panel"], fg=p["cyan"], font=f_big)
        if hasattr(self, "lbl_pct"):
            self.lbl_pct.configure(bg=p["panel"], fg=p["green"], font=f_big)

        self.pbar.configure(height=max(20, fs + 9))
        self.txt_log.configure(bg=p["log_bg"], fg=p["text"], font=(fam, fs))
        self.txt_log.tag_configure("dim", foreground=p["muted"])
        self.txt_log.tag_configure("ok", foreground=p["text"])
        self.txt_log.tag_configure("warn", foreground=p["amber"])
        self.txt_log.tag_configure("err", foreground=p["red"])
        self.txt_log.tag_configure("info", foreground=p["text"])
        self.txt_log.tag_configure("b_ok", background="#dcfce7", foreground="#15803d", font=(fam, max(8, fs - 1), "bold"))
        self.txt_log.tag_configure("b_info", background="#dbeafe", foreground="#1d4ed8", font=(fam, max(8, fs - 1), "bold"))
        self.txt_log.tag_configure("b_warn", background="#fef3c7", foreground="#b45309", font=(fam, max(8, fs - 1), "bold"))
        self.txt_log.tag_configure("b_err", background="#fee2e2", foreground="#b91c1c", font=(fam, max(8, fs - 1), "bold"))

        dis_fg = p["muted"]
        for b in (self.btn_hist, self.btn_scan, self.btn_dir, self.btn_open_dir, self.btn_mir, self.btn_about):
            b.configure(bg=p["card"], fg=p["text"], disabledforeground=dis_fg, activebackground=p["border"], activeforeground=p["text"], font=f_main, padx=bpx, pady=bpy)

        self.btn_clear_log.configure(bg=p["card"], fg=p["muted"], disabledforeground=dis_fg, activebackground=p["border"], activeforeground=p["text"], font=f_sub, padx=max(6, bpx - 2), pady=1)
        self.btn_conn.configure(bg=p["blue"], fg=p["btn_txt"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)
        self.btn_start.configure(bg=p["green"], fg=p["green_txt"], disabledforeground=dis_fg, font=f_bold, padx=bpx + 4, pady=bpy + 1)
        for b in (self.btn_analyze, self.btn_ops_hist, self.btn_stats, self.btn_strat):
            b.configure(bg=p["card"], fg=p["cyan"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)
        self.btn_exit.configure(bg=p["panel"], fg=p["red"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)

        if hasattr(self, "btn_pick_lan"):
            self.btn_pick_lan.configure(bg=p["card"], fg=p["green"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)

        res_txt = f"{m['outer_w']}×{m['outer_h']}"
        mode_lbl = f"LITE ({res_txt}) ▾" if is_lite else f"Графіка ({res_txt}) ▾"
        self.btn_mode.configure(
            text=mode_lbl,
            bg=p["panel"], fg=p["muted"], relief="flat", bd=0, disabledforeground=dis_fg, font=f_sub, padx=6, pady=2
        )
        self._update_mirror_btn()
        try:
            if resize_win:
                self._ignore_resize_until = time.time() + 0.5
            self.root.update_idletasks()
            self.root.minsize(620, 420)
        except Exception:
            pass
        lang = self.engine.state.get("lang", "en")
        self.root._cur_lang = lang
        self.root.title(tr(f"HomeGrid Backup v{SCRIPT_VER} (від {BUILD_DATE})", lang))
        apply_widget_i18n(self.root, lang)


    def open_discovered_menu(self):
        found = getattr(self.engine, "discovered_servers", []) or []
        if not found:
            return
        p = self._get_palette()
        fs = self.metrics["font_sz"]
        menu = tk.Menu(self.root, tearoff=0, bg=p["panel"], fg=p["text"], activebackground=p["blue"], activeforeground="#ffffff", font=("Segoe UI", fs))
        for url, t_ms, a_ms in found:
            menu.add_command(
                label=f"📡 {url}   (TCP: {t_ms} мс, API: {a_ms} мс)",
                command=lambda u=url: self._select_discovered_server(u)
            )
        x = self.btn_pick_lan.winfo_rootx()
        y = self.btn_pick_lan.winfo_rooty() + self.btn_pick_lan.winfo_height()
        menu.tk_popup(x, y)

    def _select_discovered_server(self, url):
        self.var_srv.set(url)
        self.engine.state["server"] = url
        self._last_synced_srv = url
        self.engine.log(f"Обрано виявлений у мережі сервер: {url}", "ok")

    def open_mode_menu(self):
        p = self._get_palette()
        fs = self.metrics["font_sz"]
        menu = tk.Menu(self.root, tearoff=0, bg=p["panel"], fg=p["text"], activebackground=p["blue"], activeforeground="#ffffff", font=("Segoe UI", fs))
        lng = self.engine.state.get("lang", "en")
        menu.add_command(label=tr("✨ Повна графіка (стандартний режим)", lng), command=lambda: self._set_graphic_mode(False))
        menu.add_command(label=tr("⚡ Ультралегкий LITE-режим (швидкий текст)", lng), command=lambda: self._set_graphic_mode(True))
        menu.add_separator()
        cur_sc = self.engine.state.get("ui_scale", "auto")
        for code, lbl in UI_SCALE_LABELS:
            mark = "✔ " if code == cur_sc else "    "
            menu.add_command(label=f"{mark}{tr(lbl, lng)}", command=lambda c=code: self._set_screen_scale_quick(c))
        menu.add_separator()
        menu.add_command(label=tr("⚙️ Налаштування екрана та шрифту...", lng), command=self.open_settings)
        x = self.btn_mode.winfo_rootx()
        y = self.btn_mode.winfo_rooty() + self.btn_mode.winfo_height()
        menu.tk_popup(x, y)

    def _set_graphic_mode(self, is_lite):
        self.engine.state["lite_mode"] = bool(is_lite)
        commit_state(self.engine.state)
        self.apply_theme_and_mode(resize_win=True)

    def _set_screen_scale_quick(self, scale_code):
        self.engine.state["ui_scale"] = scale_code
        self.engine.state["ui_font"] = 0
        commit_state(self.engine.state)
        self.apply_theme_and_mode(resize_win=True)

    def _apply_srv_autofill(self):
        raw = self.var_srv.get().strip()
        if not raw:
            return
        norm, has_bang = normalize_server_url(raw)
        if norm:
            disp = f"{norm}!" if has_bang else norm
            if disp != raw:
                self.var_srv.set(disp)
                try:
                    self.ent_srv.icursor("end")
                except Exception:
                    pass

    def _update_mirror_btn(self):
        p = self._get_palette()
        fs = self.metrics["font_sz"]
        lang = self.engine.state.get("lang", "en")
        is_lite = bool(self.engine.state.get("lite_mode", False))
        fam = "Consolas" if is_lite else p.get("font", "Segoe UI")
        is_run = bool(getattr(self.engine, "is_running", False))
        checked = bool(self.engine.state.get("mirror_enabled", False))
        self.var_mir_en.set(checked)
        f_state = "disabled" if (is_run or not checked) else "normal"
        self.chk_mir_tog.configure(
            state="disabled" if is_run else "normal",
            text=tr("Увімкнено" if checked else "Вимкнено", lang),
            bg=p["panel"], fg=p["green"] if checked else p["muted"],
            selectcolor=p["inp_bg"], activebackground=p["panel"], activeforeground=p["text"],
            font=(fam, fs, "bold" if checked else "normal")
        )
        self.ent_mir.configure(
            state=f_state,
            bg=p["inp_bg"], fg=p["text"],
            disabledbackground=p["panel"], disabledforeground=p["muted"]
        )
        self.btn_mir.configure(
            state=f_state,
            cursor="hand2" if f_state == "normal" else ""
        )
    def open_backup_folder(self):
        bdir = self.var_dir.get().strip() or self.engine.state.get("backup_dir") or DEFAULT_BACKUP_DIR
        open_folder_native(bdir)

    def _center_log_vertically(self):
        try:
            if not hasattr(self, "txt_log") or not self.txt_log.winfo_exists():
                return
            box_h = self.txt_log.winfo_height()
            if box_h <= 24:
                return
            raw_txt = self.txt_log.get("1.0", "end-1c")
            if not raw_txt.strip():
                self.txt_log.tag_remove("vcenter", "1.0", "end")
                return
            lines = raw_txt.splitlines()
            line_cnt = len(lines)
            fs = self.metrics.get("font_sz", 10)
            line_h = max(18, int(fs * 1.9))
            content_h = line_cnt * line_h
            self.txt_log.tag_remove("vcenter", "1.0", "end")
            max_compact_h = int(185 * self.metrics.get('k', 1.0))
            if 0 < line_cnt <= 5 and content_h + 14 < box_h <= max_compact_h:
                top_pad = max(2, int((box_h - content_h) // 2) - 4)
                self.txt_log.tag_configure("vcenter", spacing1=top_pad)
                self.txt_log.tag_add("vcenter", "1.0", "1.end")
        except Exception:
            pass

    def clear_log_view(self):
        with self.engine.lock:
            self.engine.logs.clear()
        self.last_log_len = -1

    def do_connect(self):
        self._apply_srv_autofill()
        threading.Thread(target=run_connect_task, args=(self.engine, self.var_srv.get(), False), daemon=True).start()

    def do_scan(self):
        threading.Thread(target=run_scan_task, args=(self.engine,), daemon=True).start()

    def do_backup(self):
        self._apply_srv_autofill()
        self.save_mirror_manual()
        threading.Thread(target=run_backup_task, args=(self.engine, self.var_srv.get(), False, False, False), daemon=True).start()

    def reset_pins(self):
        if not self.engine.is_running:
            self.engine.state["session_token"] = self.engine.state["login_pin"] = self.engine.state["editor_pin"] = ""
            commit_state(self.engine.state)
            self.engine.log("Збережені PIN-коди та токен сесії очищено (Keyring / .env).", "warn")

    def choose_dir(self):
        chosen = choose_folder_native(self.engine.state["backup_dir"])
        if chosen:
            self.engine.state["backup_dir"] = chosen
            self.var_dir.set(chosen)
            commit_state(self.engine.state)
            self.engine.log(f"Папку збереження змінено на: {chosen}", "ok")

    def reset_dir(self):
        self.engine.state["backup_dir"] = os.path.normpath(DEFAULT_BACKUP_DIR)
        self.var_dir.set(self.engine.state["backup_dir"])
        commit_state(self.engine.state)
        self.engine.log(f"Папку збереження встановлено: {self.engine.state['backup_dir']}", "ok")

    def save_dir_manual(self):
        val = self.var_dir.get().strip()
        if val:
            self.engine.state["backup_dir"] = os.path.normpath(os.path.expanduser(val))
            commit_state(self.engine.state)

    def choose_mirror(self):
        if not bool(self.var_mir_en.get()):
            return
        start_d = self.engine.state.get("mirror_dir") or self.engine.state["backup_dir"]
        chosen = choose_folder_native(start_d)
        if chosen:
            self.engine.state["mirror_dir"] = chosen
            self.engine.state["mirror_enabled"] = True
            self.var_mirror.set(chosen)
            commit_state(self.engine.state)
            self._update_mirror_btn()
            self.engine.log(f"Папку дзеркального копіювання увімкнено: {chosen}", "ok")

    def toggle_mirror(self):
        en = bool(self.var_mir_en.get())
        self.engine.state["mirror_enabled"] = en
        commit_state(self.engine.state)
        self._update_mirror_btn()
        if en:
            try:
                self.ent_mir.focus_set()
                self.ent_mir.icursor("end")
            except Exception:
                pass

    def save_mirror_manual(self):
        val = self.var_mirror.get().strip()
        self.engine.state["mirror_dir"] = os.path.normpath(os.path.expanduser(val)) if val else ""
        self.engine.state["mirror_enabled"] = bool(self.var_mir_en.get()) and bool(self.engine.state["mirror_dir"])
        commit_state(self.engine.state)
        self._update_mirror_btn()
    def _poll_ui(self):
        try:
            st = self.engine.state
            srv_in_state = (st.get("server") or "").strip()
            last_synced = getattr(self, "_last_synced_srv", srv_in_state)
            if srv_in_state and srv_in_state != last_synced:
                self._last_synced_srv = srv_in_state
                if self.root.focus_get() != self.ent_srv:
                    self.var_srv.set(srv_in_state)

            now_m = time.monotonic()
            if now_m - getattr(self, '_last_disk_t', 0.0) >= 3.5 or not self.engine.is_running:
                self._last_disk_t = now_m
                self._cached_disk = self.engine.get_storage_stats()
            z_cnt, z_mb, free_gb = getattr(self, '_cached_disk', (0, 0.0, -1))
            free_txt = f" — Вільно: {free_gb} ГБ" if free_gb >= 0 else ""
            self.var_disk.set(tr(f"{z_cnt} архівів ({z_mb} МБ){free_txt}", st.get("lang", "en")))

            if hasattr(self.engine, "get_last_backup_info") and hasattr(self, "t3_val"):
                lb_txt, lb_st = self.engine.get_last_backup_info()
                self.var_last_bkp.set(tr(lb_txt, st.get("lang", "en")))
                p_cur = self._get_palette()
                self.t3_val.configure(fg=p_cur["green"] if lb_st == "ok" else (p_cur["amber"] if lb_st == "warn" else p_cur["muted"]))

            if hasattr(self, "lbl_pill"):
                p_cur = self._get_palette()
                ptype = getattr(self.engine, "pill_type", "idle")
                ptxt = getattr(self.engine, "pill_text", "") or "Очікування"
                if " | " in ptxt and ptype == "idle":
                    ptxt = "Очікування"
                pill_fg = {"ok": p_cur.get("pill_ok_fg", p_cur["green"]), "run": p_cur["cyan"], "warn": p_cur["amber"], "err": p_cur["red"]}.get(ptype, p_cur["muted"])
                pill_bg = p_cur.get("pill_ok_bg", p_cur["card"]) if ptype in ("ok", "idle") and "pill_ok_bg" in p_cur else p_cur["card"]
                bd_pill = 0 if "pill_ok_bg" in p_cur else 1
                self.lbl_pill.configure(text=tr(ptxt, st.get("lang", "en")), bg=pill_bg, fg=pill_fg, bd=bd_pill, highlightbackground=p_cur["border"], font=("Segoe UI", max(8, self.metrics["font_sz"] - 1), "bold"))

            self.var_stage.set(self.engine.stage)
            self.var_pct.set(tr("пошук...", st.get("lang", "en")) if self.engine.indeterminate else f"{self.engine.progress}%")
            _psig = (self.engine.progress, self.engine.indeterminate, self.engine.stage, st.get('progress_style', 'v8'), bool(st.get('lite_mode', False)))
            if getattr(self, '_last_psig', None) != _psig or self.engine.indeterminate:
                self._last_psig = _psig
                self.pbar.set_state(
                self.engine.progress,
                self.engine.indeterminate,
                st.get("progress_style", "v8"),
                bool(st.get("lite_mode", False)),
                self._get_palette(),
                self.engine.stage,
                    st.get("lang", "en")
                )

            btn_state = "disabled" if self.engine.is_running else "normal"
            for b in (self.btn_hist, self.btn_conn, self.btn_scan, self.btn_dir, self.btn_open_dir, self.btn_start, self.btn_strat):
                if str(b.cget("state")) != btn_state:
                    b.configure(state=btn_state)
            self._update_mirror_btn()
            disc = getattr(self.engine, "discovered_servers", []) or []
            if hasattr(self, "btn_pick_lan"):
                if len(disc) >= 1 and not self.engine.is_running:
                    self.btn_pick_lan.configure(text=tr(f"Виявлені ({len(disc)}) ▾", st.get("lang", "en")), state="normal")
                    if not self.btn_pick_lan.winfo_ismapped():
                        self.btn_pick_lan.grid(row=0, column=5, sticky="ew", padx=(4, 0), pady=2)
                elif self.btn_pick_lan.winfo_ismapped():
                    self.btn_pick_lan.grid_remove()

            logs = self.engine.logs
            if not logs and self.last_log_len != 0:
                self.txt_log.configure(state="normal")
                self.txt_log.delete("1.0", "end")
                self.txt_log.configure(state="disabled")
                self.last_log_len = 0
                self._last_log_item = None
            elif logs and (len(logs) != self.last_log_len or logs[-1] is not self._last_log_item):
                self.txt_log.configure(state="normal")
                if self._last_log_item is None or self.last_log_len <= 0:
                    items_to_add = logs
                    self.txt_log.delete("1.0", "end")
                else:
                    last_idx = -1
                    for idx in range(len(logs) - 1, -1, -1):
                        if logs[idx] is self._last_log_item:
                            last_idx = idx
                            break
                    if last_idx != -1:
                        items_to_add = logs[last_idx + 1:]
                    else:
                        self.txt_log.delete("1.0", "end")
                        items_to_add = logs
                for item in items_to_add:
                    lvl = item.get("level", "info")
                    b_map = {"ok": (" OK ", "b_ok"), "warn": ("WAIT", "b_warn"), "err": ("ERR ", "b_err")}
                    b_txt, b_tag = b_map.get(lvl, ("INFO", "b_info"))
                    self.txt_log.insert("end", f" {b_txt} ", b_tag)
                    self.txt_log.insert("end", f"  {item['ts']}   ", "dim")
                    self.txt_log.insert("end", f"{item['msg']}\n", lvl)
                line_cnt = int(self.txt_log.index("end-1c").split(".")[0])
                if line_cnt > 401:
                    self.txt_log.delete("1.0", f"{line_cnt - 400}.0")
                self.txt_log.see("end")
                self.txt_log.configure(state="disabled")
                self._center_log_vertically()
                self.last_log_len = len(logs)
                self._last_log_item = logs[-1]

            if getattr(self.engine, "show_hw_notice", False) and not self.hw_notice_shown:
                self.hw_notice_shown = True
                self.engine.show_hw_notice = False
                notice_txt = self.engine.state.get("hw_auto_notice", "")
                if notice_txt:
                    self.engine.log(notice_txt.replace("\n\n", " ").replace("\n", " "), "info")
                    self._show_engine_modal({
                        "type": "alert",
                        "title": "Автоматичне налаштування теми",
                        "text": notice_txt
                    })

            if self.engine.modal and self.engine.modal.get("id") != self.last_modal_id:
                self.last_modal_id = self.engine.modal["id"]
                if self.root.state() in ("iconic", "withdrawn"):
                    self.show_window()
                self._show_engine_modal(self.engine.modal)
        except Exception:
            pass
        lite = bool(self.engine.state.get("lite_mode", False))
        if self.engine.is_running:
            delay = 500 if lite else 300
        else:
            delay = 1000 if lite else 600
        self.root.after(delay, self._poll_ui)
