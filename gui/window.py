# ==============================================================================
# [ФАЙЛ: gui/window.py (v1.018 | 18.11.2026 20:23) — ГЛАВНОЕ ОКНО HOMEGRIDAPP И ФОНОВЫЙ ЦИКЛ UI]
# ==============================================================================
import os
import threading
import tkinter as tk
from core.config import SCRIPT_VER, BUILD_DATE, DEFAULT_BACKUP_DIR, commit_state
from core.files import open_folder_native, choose_folder_native
from core.network import normalize_server_url, run_connect_task, run_scan_task
from core.backup import run_backup_task
from gui.styles import THEME_LABELS, UI_SCALE_LABELS, THEMES, _calc_screen_metrics, ToolTip
from gui.widgets import StyledProgressBar
from gui.tray import HAS_TRAY, _start_tray_thread
from gui.dialogs import DialogsMixin

class HomeGridApp(DialogsMixin):
    def __init__(self, root, engine):
        self.root = root
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

        self.root.title(f"HomeGrid Backup v{SCRIPT_VER} (від {BUILD_DATE})")
        m = self.metrics
        self.root.geometry(f"{m['win_w']}x{m['win_h']}+{m['pos_x']}+{m['pos_y']}")
        self.root.minsize(620, 420)
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.root.bind("<Configure>", self._on_root_configure)

        self.var_srv = tk.StringVar(value=self.engine.state.get("server", ""))
        self.var_dir = tk.StringVar(value=self.engine.state.get("backup_dir", ""))
        self.var_mirror = tk.StringVar(value=self.engine.state.get("mirror_dir", ""))
        self.var_net = tk.StringVar(value="Не перевірено")
        self.var_disk = tk.StringVar(value="0 архівів (0 МБ)")
        self.var_last_bkp = tk.StringVar(value="Перевірка...")
        self.var_strat = tk.StringVar(value="")
        self.var_stage = tk.StringVar(value=self.engine.stage)
        self.var_pct = tk.StringVar(value="0%")

        import sys
        if sys.platform == "darwin":
            self.root.bind_class("Entry", "<Command-v>", lambda e: e.widget.event_generate("<<Paste>>"))
            self.root.bind_class("Entry", "<Command-c>", lambda e: e.widget.event_generate("<<Copy>>"))
            self.root.bind_class("Entry", "<Command-x>", lambda e: e.widget.event_generate("<<Cut>>"))
            self.root.bind_class("Entry", "<Command-a>", lambda e: (e.widget.select_range(0, "end"), "break")[1])
        self._build_ui()
        self.apply_theme_and_mode()
        self.root.after(300, self._poll_ui)

    def _on_root_configure(self, event=None):
        if event is None or event.widget is not self.root:
            return
        w, h = int(event.width), int(event.height)
        if w < 500 or h < 350 or (w, h) == self._last_live_wh:
            return
        self._last_live_wh = (w, h)
        if self._resize_timer:
            try:
                self.root.after_cancel(self._resize_timer)
            except Exception:
                pass
        self._resize_timer = self.root.after(160, lambda: self.apply_theme_and_mode(resize_win=False, live_outer_wh=(w + 16, h + 40)))

    def show_window(self):
        try:
            self.root.deiconify()
            if self.root.state() in ("iconic", "withdrawn"):
                self.root.state("normal")
            self.root.attributes("-topmost", True)
            self.root.update()
            self.root.attributes("-topmost", False)
            self.root.lift()
            self.root.focus_force()
            self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        except Exception:
            pass

    def on_window_close(self):
        import sys
        if sys.platform == "darwin":
            if bool(self.engine.state.get("minimize_to_tray", True)):
                self.root.iconify()
                self.engine.log("Вікно згорнуто у Dock (програма продовжує роботу).", "info")
                return
            self.confirm_exit()
            return
        keep_tray = bool(self.engine.state.get("minimize_to_tray", True))
        if keep_tray and HAS_TRAY:
            try:
                if self.engine.tray_icon is None:
                    _start_tray_thread(self.engine)
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
        self.lbl_sub = tk.Label(hdr_left, text=f"Версія v{SCRIPT_VER}  (оновлено: {BUILD_DATE})", font=("Segoe UI", max(8, fs - 1)))
        self.lbl_sub.pack(anchor="w")

        hdr_right = tk.Frame(self.header)
        hdr_right.pack(side="right")
        self.btn_theme = tk.Button(hdr_right, text="🎨 Тема: Темна", command=self.cycle_theme_quick, padx=10, pady=4, cursor="hand2")
        self.btn_theme.pack(side="left", padx=8)
        ToolTip(self.btn_theme, "Швидке перемикання між світлою та темною темою (інші стилі доступні у Налаштуваннях)")

        self.btn_mode = tk.Button(hdr_right, text="🖥️ Графіка (1920×1080) ▾", command=self.open_mode_menu, padx=10, pady=4, cursor="hand2")
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

        conn_box = tk.Frame(self.card_conn)
        conn_box.pack(anchor="w", fill="x")
        r1 = tk.Frame(conn_box)
        r1.pack(anchor="w", pady=4)
        self.l_srv = tk.Label(r1, text="Адреса:", width=9, anchor="w")
        self.l_srv.pack(side="left")
        self.ent_srv = tk.Entry(r1, textvariable=self.var_srv, width=42, font=("Segoe UI", fs))
        self.ent_srv.pack(side="left", padx=(0, 10), ipady=3)
        self.btn_hist = tk.Button(r1, text="🕘 Історія", command=self.open_history_modal, padx=8, pady=3, cursor="hand2")
        self.btn_hist.pack(side="left", padx=5)
        self.btn_conn = tk.Button(r1, text="🔌 Підключити", command=self.do_connect, padx=12, pady=3, cursor="hand2")
        self.btn_conn.pack(side="left", padx=5)
        self.btn_scan = tk.Button(r1, text="🔍 Автопошук по LAN", command=self.do_scan, padx=12, pady=3, cursor="hand2")
        self.btn_scan.pack(side="left", padx=(5, 0))
        self.btn_pick_lan = tk.Button(r1, text="📡 Обрати виявлений (0)", command=self.open_discovered_menu, state="disabled", padx=10, pady=3, cursor="hand2")
        self.btn_pick_lan.pack(side="left", padx=(6, 0))
        ToolTip(self.btn_pick_lan, "Список серверів, виявлених під час останнього сканування локальної мережі")
        self.ent_srv.bind("<Return>", lambda e: (self._apply_srv_autofill(), self.do_connect()))
        self.ent_srv.bind("<FocusOut>", lambda e: self._apply_srv_autofill())
        self.ent_srv.bind("<KeyRelease>", self._on_srv_key_release)

        r2 = tk.Frame(conn_box)
        r2.pack(anchor="w", pady=4)
        self.l_dir = tk.Label(r2, text="Папка:", width=9, anchor="w")
        self.l_dir.pack(side="left")
        self.ent_dir = tk.Entry(r2, textvariable=self.var_dir, width=42, font=("Segoe UI", fs))
        self.ent_dir.pack(side="left", padx=(0, 10), ipady=3)
        self.btn_dir = tk.Button(r2, text="📁 Папка архівів...", command=self.choose_dir, padx=12, pady=3, cursor="hand2")
        self.btn_dir.pack(side="left", padx=5)
        self.btn_open_dir = tk.Button(r2, text="📂 Відкрити папку", command=self.open_backup_folder, padx=12, pady=3, cursor="hand2")
        self.btn_open_dir.pack(side="left", padx=(5, 0))
        self.ent_dir.bind("<FocusOut>", lambda e: self.save_dir_manual())

        r3 = tk.Frame(conn_box)
        r3.pack(anchor="w", pady=4)
        self.l_mir = tk.Label(r3, text="Дзеркало:", width=9, anchor="w")
        self.l_mir.pack(side="left")
        self.ent_mir = tk.Entry(r3, textvariable=self.var_mirror, width=42, font=("Segoe UI", fs))
        self.ent_mir.pack(side="left", padx=(0, 10), ipady=3)
        self.btn_mir = tk.Button(r3, text="🪞 Папка дзеркала...", command=self.choose_mirror, padx=12, pady=3, cursor="hand2")
        self.btn_mir.pack(side="left", padx=5)
        self.var_mir_en = tk.BooleanVar(value=bool(self.engine.state.get("mirror_enabled", True)))
        self.chk_mir_tog = tk.Checkbutton(r3, text="Увімкнено", variable=self.var_mir_en, command=self.toggle_mirror, cursor="hand2")
        self.chk_mir_tog.pack(side="left", padx=(8, 0))
        self.ent_mir.bind("<FocusOut>", lambda e: self.save_mirror_manual())

        self.card_stat = tk.Frame(self.body, padx=12, pady=py, bd=1, relief="solid")
        self.card_stat.pack(fill="x", pady=(0, py))
        stat_row = tk.Frame(self.card_stat)
        stat_row.pack(fill="x")

        stat_row.columnconfigure(0, weight=1)
        stat_row.columnconfigure(1, weight=1)
        stat_row.columnconfigure(2, weight=0)

        stat_left = tk.Frame(stat_row)
        stat_left.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.t2_cap = tk.Label(stat_left, text="ЛОКАЛЬНЕ СХОВИЩЕ", font=("Segoe UI", max(7, fs - 2), "bold"))
        self.t2_cap.pack(anchor="w")
        self.t2_val = tk.Label(stat_left, textvariable=self.var_disk, font=("Segoe UI", fs + 1, "bold"))
        self.t2_val.pack(anchor="w", pady=(2, 0))

        stat_mid = tk.Frame(stat_row)
        stat_mid.grid(row=0, column=1, sticky="w", padx=(8, 12))
        self.t3_cap = tk.Label(stat_mid, text="ОСТАННІЙ АРХІВ", font=("Segoe UI", max(7, fs - 2), "bold"))
        self.t3_cap.pack(anchor="w")
        self.t3_val = tk.Label(stat_mid, textvariable=self.var_last_bkp, font=("Segoe UI", fs + 1, "bold"))
        self.t3_val.pack(anchor="w", pady=(2, 0))

        stat_btns = tk.Frame(stat_row)
        stat_btns.grid(row=0, column=2, sticky="e")
        self.btn_stats = tk.Button(stat_btns, text="📊 Статистика", command=self.open_stats_modal, padx=10, pady=5, cursor="hand2")
        self.btn_stats.pack(side="left", padx=(0, 6))
        self.btn_ops_hist = tk.Button(stat_btns, text="📜 Журнал операцій", command=self.open_ops_history, padx=10, pady=5, cursor="hand2")
        self.btn_ops_hist.pack(side="left", padx=(0, 6))
        self.btn_analyze = tk.Button(stat_btns, text="🔍 Аналіз GFS / SHA-256", command=self.open_analyze, padx=12, pady=5, cursor="hand2")
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
        self.btn_clear_log = tk.Button(log_hdr, text="🗑 Очистити лог", command=self.clear_log_view, padx=8, pady=1, cursor="hand2")
        self.btn_clear_log.pack(side="right")

        log_wrap = tk.Frame(self.card_log)
        log_wrap.pack(fill="both", expand=True)
        self.txt_log = tk.Text(log_wrap, height=4, wrap="word", state="disabled", font=("Consolas", max(8, fs - 1)), bd=1, relief="solid", padx=8, pady=5)
        sb = tk.Scrollbar(log_wrap, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_log.pack(side="left", fill="both", expand=True)

        self.btn_start = tk.Button(self.footer, text="▶ ЗАПУСТИТИ БЕКАП", command=self.do_backup, font=("Segoe UI", fs, "bold"), padx=16, pady=5, cursor="hand2")
        self.btn_start.pack(side="left", padx=(0, 10))
        self.btn_strat = tk.Button(self.footer, text="⚙️ Налаштування", command=self.open_settings, padx=12, pady=5, cursor="hand2")
        self.btn_strat.pack(side="left", padx=8)
        self.btn_about = tk.Button(self.footer, text="ℹ️ Про програму", command=self.open_about, padx=12, pady=5, cursor="hand2")
        self.btn_about.pack(side="left", padx=8)
        self.btn_exit = tk.Button(self.footer, text="✖ Вихід", command=self.confirm_exit, padx=14, pady=5, cursor="hand2")
        self.btn_exit.pack(side="right", padx=(8, 0))

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
        else:
            fam = "Consolas" if is_lite else p.get("font", "Segoe UI")
        rel = "solid" if is_lite else p.get("relief", "solid")
        bd_w = 2 if rel in ("raised", "groove") else 1

        f_main = (fam, fs)
        f_bold = (fam, fs, "bold")
        f_sub = (fam, max(8, fs - 1))
        f_cap = (fam, max(8, fs - 2), "bold")

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

        avail_chars = max(16, int((m["win_w"] - int(460 * m["k"])) / max(7, fs * 0.65)))
        ent_chars = max(20, min(52, avail_chars))
        for ent in (self.ent_srv, self.ent_dir, self.ent_mir):
            ent.configure(bg=p["inp_bg"], fg=p["text"], insertbackground=p["text"], font=f_main, width=ent_chars)

        self.t2_cap.configure(bg=p["panel"], fg=p["muted"], font=f_cap)
        self.t2_val.configure(bg=p["panel"], fg=p["green"], font=f_bold)
        if hasattr(self, "t3_cap"):
            self.t3_cap.configure(bg=p["panel"], fg=p["muted"], font=f_cap)
            self.t3_val.configure(bg=p["panel"], fg=p["cyan"], font=f_bold)

        self.pbar.configure(height=max(20, fs + 9))
        self.txt_log.configure(bg=p["log_bg"], fg=p["text"], font=("Consolas", max(8, fs - 1)))
        self.txt_log.tag_configure("dim", foreground=p["muted"])
        self.txt_log.tag_configure("ok", foreground=p["green"])
        self.txt_log.tag_configure("warn", foreground=p["amber"])
        self.txt_log.tag_configure("err", foreground=p["red"])
        self.txt_log.tag_configure("info", foreground=p["text"])

        dis_fg = p["muted"]
        for b in (self.btn_hist, self.btn_scan, self.btn_dir, self.btn_open_dir, self.btn_mir, self.btn_about):
            b.configure(bg=p["card"], fg=p["text"], disabledforeground=dis_fg, activebackground=p["border"], activeforeground=p["text"], font=f_main, padx=bpx, pady=bpy)

        self.btn_clear_log.configure(bg=p["card"], fg=p["muted"], disabledforeground=dis_fg, activebackground=p["border"], activeforeground=p["text"], font=f_sub, padx=max(6, bpx - 2), pady=1)
        self.btn_conn.configure(bg=p["blue"], fg=p["btn_txt"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)
        self.btn_start.configure(bg=p["green"], fg=p["green_txt"], disabledforeground=dis_fg, font=f_bold, padx=bpx + 4, pady=bpy + 1)
        for b in (self.btn_analyze, self.btn_ops_hist, self.btn_stats, self.btn_strat):
            b.configure(bg=p["card"], fg=p["cyan"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)
        self.btn_exit.configure(bg=p["panel"], fg=p["red"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)

        is_dark_now = cur_theme in ("dark", "mac_dark", "crt", "norton")
        t_lbl = "☀️ Світла тема" if is_dark_now else "🌙 Темна тема"
        self.btn_theme.configure(text=t_lbl, bg=p["card"], fg=p["cyan"], disabledforeground=dis_fg, font=f_main, padx=bpx, pady=bpy)
        if hasattr(self, "btn_pick_lan"):
            self.btn_pick_lan.configure(bg=p["card"], fg=p["green"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)

        res_txt = f"{m['outer_w']}×{m['outer_h']}"
        mode_lbl = f"⚡ LITE ({res_txt}) ▾" if is_lite else f"🖥️ Графіка ({res_txt}) ▾"
        self.btn_mode.configure(
            text=mode_lbl,
            bg=p["card"], fg=p["amber"] if is_lite else p["green"], disabledforeground=dis_fg, font=f_main, padx=bpx, pady=bpy
        )
        self._update_mirror_btn()

    def cycle_theme_quick(self):
        import sys
        cur = self.engine.state.get("theme", "dark")
        is_dark_now = cur in ("dark", "mac_dark", "crt", "norton")
        if sys.platform == "darwin":
            self.engine.state["theme"] = "mac_light" if is_dark_now else "mac_dark"
        else:
            self.engine.state["theme"] = "light" if is_dark_now else "dark"
        if self.engine.state.get("lite_mode", False):
            self.engine.state["lite_mode"] = False
        commit_state(self.engine.state)
        self.apply_theme_and_mode()

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
        menu.add_command(label="✨ Повна графіка (стандартний режим)", command=lambda: self._set_graphic_mode(False))
        menu.add_command(label="⚡ Ультралегкий LITE-режим (швидкий текст)", command=lambda: self._set_graphic_mode(True))
        menu.add_separator()
        cur_sc = self.engine.state.get("ui_scale", "auto")
        for code, lbl in UI_SCALE_LABELS:
            mark = "✔ " if code == cur_sc else "    "
            menu.add_command(label=f"{mark}{lbl}", command=lambda c=code: self._set_screen_scale_quick(c))
        menu.add_separator()
        menu.add_command(label="⚙️ Налаштування екрана, шрифту та тем...", command=self.open_settings)
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
        is_lite = bool(self.engine.state.get("lite_mode", False))
        fam = "Consolas" if is_lite else p.get("font", "Segoe UI")
        has_dir = bool(self.var_mirror.get().strip())
        enabled = bool(self.engine.state.get("mirror_enabled", True)) and has_dir
        self.var_mir_en.set(enabled)
        self.chk_mir_tog.configure(
            state="normal" if has_dir else "disabled",
            text="Увімкнено" if has_dir else "Не задано",
            bg=p["panel"], fg=p["green"] if enabled else p["muted"],
            selectcolor=p["inp_bg"], activebackground=p["panel"], activeforeground=p["text"],
            font=(fam, fs, "bold" if enabled else "normal")
        )

    def open_backup_folder(self):
        bdir = self.var_dir.get().strip() or self.engine.state.get("backup_dir") or DEFAULT_BACKUP_DIR
        open_folder_native(bdir)

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
        self.engine.state["mirror_enabled"] = bool(self.var_mir_en.get())
        commit_state(self.engine.state)
        self._update_mirror_btn()

    def save_mirror_manual(self):
        val = self.var_mirror.get().strip()
        self.engine.state["mirror_dir"] = os.path.normpath(os.path.expanduser(val)) if val else ""
        self.engine.state["mirror_enabled"] = bool(self.engine.state["mirror_dir"])
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

            z_cnt, z_mb, free_gb = self.engine.get_storage_stats()
            free_txt = f" — Вільно: {free_gb} ГБ" if free_gb >= 0 else ""
            self.var_disk.set(f"{z_cnt} архівів ({z_mb} МБ){free_txt}")

            if hasattr(self.engine, "get_last_backup_info") and hasattr(self, "t3_val"):
                lb_txt, lb_st = self.engine.get_last_backup_info()
                self.var_last_bkp.set(lb_txt)
                p_cur = self._get_palette()
                self.t3_val.configure(fg=p_cur["green"] if lb_st == "ok" else (p_cur["amber"] if lb_st == "warn" else p_cur["muted"]))

            if hasattr(self, "lbl_pill"):
                p_cur = self._get_palette()
                ptype = getattr(self.engine, "pill_type", "idle")
                ptxt = getattr(self.engine, "pill_text", "") or "Очікування"
                if " | " in ptxt and ptype == "idle":
                    ptxt = "Очікування"
                pill_fg = {"ok": p_cur["green"], "run": p_cur["cyan"], "warn": p_cur["amber"], "err": p_cur["red"]}.get(ptype, p_cur["muted"])
                self.lbl_pill.configure(text=ptxt, bg=p_cur["card"], fg=pill_fg, highlightbackground=p_cur["border"], font=("Segoe UI", max(8, self.metrics["font_sz"] - 1), "bold"))

            self.var_stage.set(self.engine.stage)
            self.var_pct.set("пошук..." if self.engine.indeterminate else f"{self.engine.progress}%")
            self.pbar.set_state(
                self.engine.progress,
                self.engine.indeterminate,
                st.get("progress_style", "v8"),
                bool(st.get("lite_mode", False)),
                self._get_palette()
            )

            btn_state = "disabled" if self.engine.is_running else "normal"
            for b in (self.btn_hist, self.btn_conn, self.btn_scan, self.btn_dir, self.btn_open_dir, self.btn_mir, self.btn_start, self.btn_strat):
                b.configure(state=btn_state)
            disc = getattr(self.engine, "discovered_servers", []) or []
            if hasattr(self, "btn_pick_lan"):
                if disc and not self.engine.is_running:
                    self.btn_pick_lan.configure(text=f"📡 Обрати виявлений ({len(disc)}) ▾", state="normal")
                else:
                    cnt_d = len(disc)
                    lbl_d = f"📡 Обрати виявлений ({cnt_d}) ▾" if cnt_d else "📡 Обрати виявлений (0)"
                    self.btn_pick_lan.configure(text=lbl_d, state="disabled")

            logs = self.engine.logs
            if logs and (len(logs) != self.last_log_len or logs[-1] is not self._last_log_item):
                self.txt_log.configure(state="normal")
                rebuild = (self.last_log_len > 0 and self._last_log_item is not None
                           and not any(item is self._last_log_item for item in logs))
                if rebuild:
                    self.txt_log.delete("1.0", "end")
                    items_to_add = logs
                else:
                    items_to_add = logs[self.last_log_len:] if len(logs) >= self.last_log_len else logs
                for item in items_to_add:
                    self.txt_log.insert("end", f"[{item['ts']}] ", "dim")
                    self.txt_log.insert("end", f"{item['msg']}\n", item.get("level", "info"))
                self.txt_log.see("end")
                self.txt_log.configure(state="disabled")
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
