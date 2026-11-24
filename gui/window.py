# patch-id: i18n-ping-and-retry-en-2.79
# patch-id: fix-net-drive-status-and-build-retry-2.78
# ==============================================================================
# patch-id: idle-ui-cache-2.19
# patch-id: opt-log-i18n-ui-2.20
# patch-id: mirror-btn-sig-2.22
# patch-id: adaptive-ui-poll-2.11
# patch-id: ui-widget-signatures-2.12
# patch-id: macos-tray-quit-apps-2.41
# patch-id: cumulative-linux-tray-pcloud-menu-2.42
# patch-id: card-conn-copies-2.59
# patch-id: archives-label-and-logs-dir-2.60
# patch-id: dest-stats-bg-worker-2.61
# patch-id: pcloud-inline-path-2.63
# patch-id: lan-btn-layout68-2.64
# patch-id: fav-servers-pills-2.65
# patch-id: fix-grid-rows-2.65a
# patch-id: big-bottom-pbar-2.66
# patch-id: pcloud-stats-refresh-compact-2.67
# patch-id: split-last-backup-2.68
# patch-id: pretty-last-backup-2.69
# patch-id: tall-pbar-server-marquee-2.70
# patch-id: remove-mirror-ui-2.71-p1
# patch-id: force-tall-pbar-and-grid-2.74
# [ФАЙЛ: gui/window.py (v2.30 | 24.11.2026 02:15) — ГЛАВНОЕ ОКНО HOMEGRIDAPP И ФОНОВЫЙ ЦИКЛ UI]
# ==============================================================================
import os
import threading
import time
import tkinter as tk

from core.backup import run_backup_task
from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW

# patch-id: center-storage-notepad-2.40
# patch-id: dashboard-redesign-2.34
from core.config import (
    BUILD_DATE,
    DEFAULT_BACKUP_DIR,
    NO_TRAY,
    SCRIPT_VER,
    commit_state,
    get_logs_dir,
)
from core.files import choose_folder_native, get_app_icon_path, open_folder_native
from core.i18n import apply_widget_i18n, tr
from core.network import normalize_server_url, run_connect_task, run_scan_task
from gui.dialogs import DialogsMixin
from gui.styles import (
    THEMES,
    UI_SCALE_LABELS,
    ToolTip,
    _calc_screen_metrics,
    fix_mac_buttons,
)

# patch-id: homegrid-design-system-2.45
from gui.widgets import HomeGridToggle, StyledProgressBar


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
        self.var_net_dir = tk.StringVar(value=self.engine.state.get("net_dir", ""))
        self.var_cloud_path = tk.StringVar(value=self.engine.state.get("cloud_path", "HomeGridBackup"))
        self.var_net = tk.StringVar(value="Не перевірено")
        self.var_disk = tk.StringVar(value="0 архівів (0 МБ)")
        self.var_last_bkp = tk.StringVar(value="Перевірка...")
        self.var_last_bkp_sub = tk.StringVar(value="")
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
        self._setup_native_menubar()
        self._build_ui()
        self.apply_theme_and_mode()
        self.root.deiconify()
        self.root.resizable(True, True)
        self.root.minsize(620, 420)
        self.root.update_idletasks()
        self._last_live_wh = (self.root.winfo_width(), self.root.winfo_height())
        self.root.after(60, self._apply_window_icon)
        self.root.after(250, self._watch_size)
        self.root.after(300, self._poll_ui)
        if hasattr(self.engine, 'start_dest_stats_worker'):
            self.root.after(150, self.engine.start_dest_stats_worker)
        if WINDOWS7_CLOUD_SYNC_PREVIEW and self.engine.state.get("cloud_enabled"):
            self.root.after(5000, self._retry_pending_cloud_sync)

    def _setup_native_menubar(self):
        import sys
        if sys.platform != "darwin":
            try: self.root.configure(menu="")
            except Exception: pass
            return
        try:
            lng = self.engine.state.get("lang", "en")
            menubar = tk.Menu(self.root)
            app_menu = tk.Menu(menubar, name="apple", tearoff=0)
            app_menu.add_command(label=tr("Про програму", lng) + " HomeGrid Backup", command=self.open_about)
            app_menu.add_separator()
            app_menu.add_command(label=tr("Налаштування", lng) + "...", accelerator="Command+,", command=self.open_settings)
            menubar.add_cascade(label="HomeGrid Backup", menu=app_menu)
            try:
                self.root.createcommand("tk::mac::Quit", self.confirm_exit)
            except Exception:
                pass
            self.root.configure(menu=menubar)
        except Exception:
            pass

    def open_burger_menu(self):
        lng = self.engine.state.get("lang", "en")
        p = self._get_palette()
        m = tk.Menu(self.root, tearoff=0, bg=p["panel"], fg=p["text"], activebackground=p["blue"], activeforeground="#ffffff", font=(self._base_fam, self.metrics["font_sz"]))
        m.add_command(label="▶  " + tr("ЗАПУСТИТИ БЕКАП", lng), command=self.do_backup)
        m.add_command(label="🔍  " + tr("Автопошук", lng), command=self.do_scan)
        m.add_command(label="📂  " + tr("Відкрити папку", lng), command=self.open_backup_folder)
        m.add_separator()
        m.add_command(label="📊  " + tr("Статистика", lng), command=self.open_stats_modal)
        m.add_command(label="📋  " + tr("Журнал операцій", lng), command=self.open_ops_history)
        m.add_command(label="🛡  " + tr("Аналіз GFS / SHA-256", lng), command=self.open_analyze)
        m.add_separator()
        m.add_command(label="⚙  " + tr("Налаштування", lng), command=self.open_settings)
        m.add_command(label="ℹ  " + tr("Про програму", lng), command=self.open_about)
        m.add_separator()
        m.add_command(label="✖  " + tr("Вихід", lng), command=self.confirm_exit)
        m.tk_popup(self.btn_burger.winfo_rootx(), self.btn_burger.winfo_rooty() + self.btn_burger.winfo_height())


    def _apply_window_icon(self):
        ico = get_app_icon_path()
        if not ico:
            return
        if os.name == "nt":
            try:
                self.root.iconbitmap(default=ico)
            except Exception:
                pass
        try:
            from PIL import Image, ImageTk
            im = Image.open(ico).convert("RGBA")
            self._win_icons = [ImageTk.PhotoImage(im.resize((sz, sz), Image.LANCZOS)) for sz in (16, 32, 48, 64)]
            self.root.iconphoto(True, *self._win_icons)
        except Exception:
            pass

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
            if self.root.state() in ("iconic", "withdrawn"):
                self.root.after(2000, self._watch_size)
                return
            if time.time() >= getattr(self, "_ignore_resize_until", 0):
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
        if NO_TRAY or not self.engine.state.get("tray_enabled", True):
            self.root.iconify()
            self.engine.log("Вікно згорнуто в панель задач (трей вимкнено).", "info")
            return
        keep_tray = bool(self.engine.state.get("minimize_to_tray", True))
        if keep_tray:
            from gui.tray import HAS_TRAY, _start_tray_thread
        else:
            HAS_TRAY = False
        if keep_tray and HAS_TRAY:
            try:
                if self.engine.tray_icon is None:
                    _start_tray_thread(self.engine)
                ready_event = getattr(self.engine, "tray_ready_event", None)
                ready = bool(
                    self.engine.tray_icon is not None
                    and ready_event is not None
                    and (ready_event.is_set() or ready_event.wait(2.5))
                    and getattr(self.engine, "tray_ready", False)
                )
                if ready:
                    self.root.withdraw()
                    self.engine.log("Значок системного трею запущено; вікно приховано.", "info")
                    return
            except Exception as exc:
                self.engine.tray_error = str(exc)
                self.engine.log("Не вдалося перевірити запуск значка системного трею.", "err")
        if sys.platform.startswith("linux") and keep_tray:
            self.root.iconify()
            reason = getattr(self.engine, "tray_error", "")
            if not reason:
                from gui.tray import _tray_problem
                reason = _tray_problem()
            self.engine.log(
                "Запуск трею не підтверджено; вікно згорнуто на панель задач.",
                "warn"
            )
            if reason:
                self.engine.log(f"[TRAY DETAIL] {reason}", "warn")
            return
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
        self.var_cloud_st = tk.StringVar(value="pCloud: вимкнено")

        self.header = tk.Frame(self.root, padx=px, pady=max(6, py), bd=0, highlightthickness=1)
        self.header.pack(side="top", fill="x")
        hdr_left = tk.Frame(self.header)
        hdr_left.pack(side="left", fill="x", expand=True)
        self.btn_burger = tk.Button(hdr_left, text="☰", command=self.open_burger_menu, padx=8, pady=2, bd=0, cursor="hand2")
        self.btn_burger.pack(side="left", padx=(0, 8))
        self.lbl_title = tk.Label(hdr_left, text="HomeGrid Backup", font=(self._base_fam, fs + 4, "bold"))
        self.lbl_title.pack(side="left")
        self.lbl_sub = tk.Label(hdr_left, text="", font=(self._base_fam, 1))

        hdr_right = tk.Frame(self.header)
        hdr_right.pack(side="right")
        self.btn_cloud_badge = tk.Button(hdr_right, textvariable=self.var_cloud_st, command=lambda: self.open_settings(initial_tab=2), padx=10, pady=3, bd=0, cursor="hand2")
        # hidden cloud badge
        self.btn_theme = tk.Button(hdr_right, text="☀️ Світла тема", command=self.toggle_theme_quick, padx=10, pady=3, bd=0, cursor="hand2")
        self.btn_theme.pack(side="left", padx=(0, 6))
        self.btn_mode = tk.Button(hdr_right, text="Графіка ▾", command=self.open_mode_menu, padx=8, pady=3, bd=0, cursor="hand2")
        self.btn_mode.pack(side="left")

        self.footer = tk.Frame(self.root, padx=px, pady=max(6, py), bd=0, highlightthickness=1)
        self.footer.pack(side="bottom", fill="x")

        self.body = tk.Frame(self.root, padx=px, pady=py)
        self.body.pack(side="top", fill="both", expand=True)

        self.top_split = tk.Frame(self.body)
        self.top_split.pack(fill="x", pady=(0, py))
        self.top_split.columnconfigure(0, weight=68)
        self.top_split.columnconfigure(1, weight=32)

        self.card_conn = tk.Frame(self.top_split, padx=px, pady=py, bd=0, highlightthickness=1)
        self.card_conn.grid(row=0, column=0, sticky="nsew", padx=(0, max(6, px // 2)))
        c1_hdr = tk.Frame(self.card_conn, bd=0, highlightthickness=0)
        c1_hdr.pack(fill="x", pady=(0, 4))
        self.lbl_c1 = tk.Label(c1_hdr, text="Підключення та папки", font=(self._base_fam, fs, "bold"))
        self.lbl_c1.pack(side="left")
        self.var_srv_badge = tk.StringVar(value="")
        self.lbl_srv_badge = tk.Label(c1_hdr, textvariable=self.var_srv_badge, font=(self._base_fam, max(8, fs - 1), "bold"))
        self.lbl_srv_badge.pack(side="right")

        cg = tk.Frame(self.card_conn, bd=0, highlightthickness=0)
        cg.pack(fill="x")
        cg.columnconfigure(0, minsize=max(106, fs * 11))
        cg.columnconfigure(1, weight=1)
        cg.columnconfigure(2, minsize=max(34, fs * 3), uniform="cc_mid")
        cg.columnconfigure(3, minsize=max(102, fs * 10), uniform="cc_act")

        self.l_srv = tk.Label(cg, text="Сервер:", anchor="w", font=(self._base_fam, fs))
        self.l_srv.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=3)
        srv_in_wrap = tk.Frame(cg, bd=0, highlightthickness=0)
        srv_in_wrap.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(0, 4), pady=3)
        self.ent_srv = tk.Entry(srv_in_wrap, width=1, textvariable=self.var_srv, bd=0, highlightthickness=1, font=(self._base_fam, fs))
        self.ent_srv.pack(side="left", fill="x", expand=True, ipady=4)
        self.btn_scan = tk.Button(srv_in_wrap, text="Автопошук LAN", command=self.on_scan_btn_click, padx=10, pady=2, bd=0, highlightthickness=1, cursor="hand2")
        self.btn_scan.pack(side="left", padx=(6, 0), fill="y")
        self.btn_conn = tk.Button(cg, text="Підключити", command=self.do_connect, pady=2, bd=0, cursor="hand2")
        self.btn_conn.grid(row=0, column=3, sticky="nsew", padx=(4, 0), pady=3)

        self.l_fav = tk.Label(cg, text="Обрані:", anchor="w", font=(self._base_fam, max(8, fs - 1)))
        self.l_fav.grid(row=1, column=0, sticky="w", padx=(0, 6), pady=2)
        self.fav_bar = tk.Frame(cg, bd=0, highlightthickness=0)
        self.fav_bar.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 4), pady=2)
        self.btn_hist = tk.Button(cg, text="Історія", command=self.open_history_modal, pady=1, bd=0, highlightthickness=1, cursor="hand2")
        self.btn_hist.grid(row=1, column=3, sticky="nsew", padx=(4, 0), pady=2)

        self.conn_sep = tk.Frame(cg, height=1, bd=0, highlightthickness=0)
        self.conn_sep.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(5, 4))
        self.l_copies_hdr = tk.Label(cg, text="Сховища:", anchor="w", font=(self._base_fam, max(8, fs - 1), "bold"))
        self.l_copies_hdr.grid(row=3, column=0, columnspan=4, sticky="w", pady=(0, 2))
        lb = tk.Frame(cg, bd=0, highlightthickness=0)
        lb.grid(row=4, column=0, sticky="w", padx=(8, 6), pady=3)
        self.var_loc_en = tk.BooleanVar(value=bool(self.engine.state.get("local_enabled", True)))
        self.chk_loc_tog = HomeGridToggle(lb, variable=self.var_loc_en, command=lambda: (self.engine.state.update(local_enabled=bool(self.var_loc_en.get())), commit_state(self.engine.state), self._update_mirror_btn()), compact=True, palette=self._get_palette(), font_sz=max(8, fs - 1))
        self.chk_loc_tog.pack(side="left", padx=(0, 5))
        self.l_dir = tk.Label(lb, text="Локально", anchor="w", font=(self._base_fam, max(8, fs - 1)), cursor="hand2")
        self.l_dir.pack(side="left")
        self.l_dir.bind("<Button-1>", lambda _e: self.chk_loc_tog._on_click_compact())
        self.ent_dir = tk.Entry(cg, width=1, textvariable=self.var_dir, bd=0, highlightthickness=1, font=(self._base_fam, fs))
        self.ent_dir.grid(row=4, column=1, sticky="ew", padx=(0, 4), pady=3, ipady=3)
        self.btn_dir = tk.Button(cg, text="📂", command=self.choose_dir, pady=1, bd=0, highlightthickness=1, cursor="hand2")
        self.btn_dir.grid(row=4, column=2, sticky="nsew", padx=2, pady=3)
        self.var_loc_st = tk.StringVar(value="—")
        self.lbl_loc_st = tk.Label(cg, textvariable=self.var_loc_st, anchor="w", font=(self._base_fam, max(8, fs - 1)), cursor="hand2")
        self.lbl_loc_st.grid(row=4, column=3, sticky="w", padx=(6, 0), pady=3)
        self.lbl_loc_st.bind("<Button-1>", lambda _e: self.open_backup_folder())
        self.btn_open_dir = tk.Button(cg, text="↗", command=self.open_backup_folder)
        net_box = tk.Frame(cg, bd=0, highlightthickness=0)
        net_box.grid(row=5, column=0, sticky="w", padx=(8, 6), pady=2)
        self.var_net_en = tk.BooleanVar(value=bool(self.engine.state.get("net_enabled", False)) and bool(self.var_net_dir.get().strip()))
        self.chk_net_tog = HomeGridToggle(net_box, variable=self.var_net_en, command=self.toggle_net_dir, compact=True, palette=self._get_palette(), font_sz=max(8, fs - 1))
        self.chk_net_tog.pack(side="left", padx=(0, 5))
        self.l_net = tk.Label(net_box, text="Мережа", anchor="w", font=(self._base_fam, max(8, fs - 1)), cursor="hand2")
        self.l_net.pack(side="left")
        self.l_net.bind("<Button-1>", lambda _e: self.chk_net_tog._on_click_compact())
        self.ent_net = tk.Entry(cg, width=1, textvariable=self.var_net_dir, state="disabled", bd=0, highlightthickness=1, font=(self._base_fam, fs))
        self.ent_net.grid(row=5, column=1, sticky="ew", padx=(0, 4), pady=2, ipady=3)
        self.btn_net = tk.Button(cg, text="📂", command=self.choose_net_dir, state="disabled", pady=1, bd=0, highlightthickness=1, cursor="hand2")
        self.btn_net.grid(row=5, column=2, sticky="nsew", padx=2, pady=2)
        self.var_net_st = tk.StringVar(value="—")
        self.lbl_net_st = tk.Label(cg, textvariable=self.var_net_st, anchor="w", font=(self._base_fam, max(8, fs - 1)))
        self.lbl_net_st.grid(row=5, column=3, sticky="w", padx=(6, 0), pady=2)

        cld_box = tk.Frame(cg, bd=0, highlightthickness=0)
        # cld_box.grid(row=6, column=0, sticky="w", padx=(8, 6), pady=2)
        self.var_cld_en = tk.BooleanVar(value=bool(self.engine.state.get("cloud_enabled", False)))
        self.chk_cld_tog = HomeGridToggle(cld_box, variable=self.var_cld_en, command=self.toggle_cloud_quick, compact=True, palette=self._get_palette(), font_sz=max(8, fs - 1))
        self.chk_cld_tog.pack(side="left", padx=(0, 5))
        self.l_cld = tk.Label(cld_box, text="pCloud", anchor="w", font=(self._base_fam, max(8, fs - 1)), cursor="hand2")
        self.l_cld.pack(side="left")
        self.l_cld.bind("<Button-1>", lambda _e: self.chk_cld_tog._on_click_compact())
        self.ent_cld = tk.Entry(cg, width=1, textvariable=self.var_cloud_path, state="disabled", bd=0, highlightthickness=1, font=(self._base_fam, fs))
        # self.ent_cld.grid(row=6, column=1, sticky="ew", padx=(0, 4), pady=2, ipady=3)
        self.btn_cld_cfg = tk.Button(cg, text="⚙", command=lambda: self.open_settings(initial_tab=2), pady=1, bd=0, highlightthickness=1, cursor="hand2")
        # self.btn_cld_cfg.grid(row=6, column=2, sticky="nsew", padx=2, pady=2)
        self.var_cld_st = tk.StringVar(value="● вимкнено")
        self.lbl_cld_st = tk.Label(cg, textvariable=self.var_cld_st, anchor="w", font=(self._base_fam, max(8, fs - 1)), cursor="hand2")
        # self.lbl_cld_st.grid(row=6, column=3, sticky="w", padx=(6, 0), pady=2)
        self.lbl_cld_st.bind("<Button-1>", lambda _e: self.open_settings(initial_tab=2))
        self.ent_srv.bind("<Return>", lambda e: (self._apply_srv_autofill(), self.do_connect()))
        self.ent_srv.bind("<FocusOut>", lambda e: (self._apply_srv_autofill(), self._render_fav_servers()))
        self.ent_srv.bind("<KeyRelease>", self._on_srv_key_release)
        self.ent_dir.bind("<FocusOut>", lambda e: self.save_dir_manual())
        self.ent_net.bind("<FocusOut>", lambda e: self.save_net_manual())
        self.ent_cld.bind("<FocusOut>", lambda e: self.save_cloud_path_manual())
        self.ent_cld.bind("<Return>", lambda e: self.save_cloud_path_manual())

        self.card_stat = tk.Frame(self.top_split, padx=px, pady=py, bd=0, highlightthickness=1)
        self.card_stat.grid(row=0, column=1, sticky="nsew", padx=(max(6, px // 2), 0))
        self.lbl_c2 = tk.Label(self.card_stat, text="Сховище та аналітика", font=(self._base_fam, fs, "bold"), anchor="center")
        self.lbl_c2.pack(fill="x", pady=(0, 6))

        t2 = tk.Frame(self.card_stat)
        t2.pack(anchor="center", pady=2)
        self.t2_cap = tk.Label(t2, text="ЛОКАЛЬНО:", font=(self._base_fam, max(8, fs - 1), "bold"))
        self.t2_cap.pack(side="left", padx=(0, 6))
        self.t2_val = tk.Label(t2, textvariable=self.var_disk, font=(self._base_fam, fs, "bold"))
        self.t2_val.pack(side="left")

        self.dest_rows = {}
        for d_key, d_cap in (("network", "МЕРЕЖА:"), ("pcloud", "PCLOUD:")):
            rf = tk.Frame(self.card_stat)
            v_str = tk.StringVar(value="—")
            c_lbl = tk.Label(rf, text=d_cap, font=(self._base_fam, max(8, fs - 2), "bold"))
            c_lbl.pack(side="left", padx=(0, 5))
            v_lbl = tk.Label(rf, textvariable=v_str, font=(self._base_fam, max(8, fs - 1), "bold"))
            v_lbl.pack(side="left")
            if d_key == "pcloud":
                self.btn_refresh_cld = tk.Button(rf, text=chr(0x21BB), command=self._force_refresh_pcloud_stats, padx=5, pady=0, bd=0, highlightthickness=1, cursor="hand2")
                self.btn_refresh_cld.pack(side="left", padx=(6, 0))
                ToolTip(self.btn_refresh_cld, "Оновити статистику pCloud")
            self.dest_rows[d_key] = (rf, c_lbl, v_lbl, v_str)

        t3 = tk.Frame(self.card_stat)
        t3.pack(anchor="center", pady=(2, 0))
        self.t3_cap = tk.Label(t3, text="ОСТАННІЙ:", font=(self._base_fam, max(8, fs - 1), "bold"))
        self.t3_cap.pack(side="left", padx=(0, 6))
        self.t3_val = tk.Label(t3, textvariable=self.var_last_bkp, font=(self._base_fam, fs, "bold"))
        self.t3_val.pack(side="left")
        self.t3_sub = tk.Label(self.card_stat, textvariable=self.var_last_bkp_sub, font=(self._base_fam, max(8, fs - 1), "bold"))
        self.t3_sub.pack(anchor="center", pady=(0, 2))

        self.stat_btns = tk.Frame(self.card_stat)
        self.stat_btns.pack(fill="x", pady=(8, 0))
        self.stat_btns.columnconfigure(0, weight=1)
        self.stat_btns.columnconfigure(1, weight=1)
        self.btn_stats = tk.Button(self.stat_btns, text="📊 Локально", command=self.open_stats_modal, pady=4, bd=0, cursor="hand2")
        self.btn_stats.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
        self.btn_cstats = tk.Button(self.stat_btns, text="🌐 Мережа", command=self.open_cloud_stats_modal, pady=4, bd=0, cursor="hand2")
        self.btn_cstats.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=2)
        self.btn_ops_hist = tk.Button(self.stat_btns, text="📋 Журнал", command=self.open_ops_history, pady=4, bd=0, cursor="hand2")
        self.btn_ops_hist.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=2)
        self.btn_analyze = tk.Button(self.stat_btns, text="🛡 Перевірка SHA", command=self.open_analyze, pady=4, bd=0, cursor="hand2")
        self.btn_analyze.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=2)

        self.card_prog = tk.Frame(self.body, padx=px, pady=py, bd=0, highlightthickness=1)
        self.card_prog.pack(side="bottom", fill="x", pady=(py, 0))
        p_top = tk.Frame(self.card_prog)
        p_top.pack(fill="x", pady=(0, 6))
        self.lbl_stage = tk.Label(p_top, textvariable=self.var_stage, font=(self._base_fam, fs + 2, "bold"))
        self.lbl_stage.pack(side="left")
        self.lbl_pct = tk.Label(p_top, textvariable=self.var_pct, font=(self._base_fam, fs + 4, "bold"))
        self.lbl_pct.pack(side="right")
        self.lbl_pill = tk.Label(p_top, text="Очікування", padx=10, pady=2, bd=0, font=(self._base_fam, fs, "bold"))
        self.lbl_pill.pack(side="right", padx=(0, 12))
        self.lbl_load_3s = tk.Label(p_top, text="CPU: --% | RAM: --%", font=(self._base_fam, max(8, fs - 1), "bold"))
        self.lbl_load_3s.pack(side="right", padx=(0, 12))
        self.root.after(1000, self._tick_3s_loader)
        self.pbar = StyledProgressBar(self.card_prog, height=84)
        self.pbar.pack(fill="x", ipady=4)

        self.card_log = tk.Frame(self.body, padx=px, pady=py, bd=0, highlightthickness=1)
        self.card_log.pack(side="top", fill="both", expand=True)
        log_hdr = tk.Frame(self.card_log)
        log_hdr.pack(fill="x", pady=(0, 4))
        self.lbl_c4 = tk.Label(log_hdr, text="Системний лог", font=(self._base_fam, fs, "bold"))
        self.lbl_c4.pack(side="left")
        self.btn_clear_log = tk.Button(log_hdr, text="Очистити", command=self.clear_log_view, padx=8, pady=1, bd=0, cursor="hand2")
        self.btn_clear_log.pack(side="right")
        self.btn_open_log = tk.Button(log_hdr, text="📄 backup.log", command=self.open_raw_log_file, padx=8, pady=1, bd=0, cursor="hand2")
        self.btn_open_log.pack(side="right", padx=(0, 6))

        log_wrap = tk.Frame(self.card_log)
        log_wrap.pack(fill="both", expand=True)
        self.txt_log = tk.Text(log_wrap, height=10, wrap="word", state="disabled", font=(self._base_fam, fs), bd=0, highlightthickness=1, padx=10, pady=6, spacing1=1, spacing3=1)
        sb = tk.Scrollbar(log_wrap, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_log.pack(side="left", fill="both", expand=True)
        self.txt_log.bind("<Configure>", lambda _e: self._center_log_vertically(), add="+")

        self.btn_start = tk.Button(self.footer, text="▶ ЗАПУСТИТИ БЕКАП", command=self.do_backup, font=(self._base_fam, fs, "bold"), padx=18, pady=5, bd=0, cursor="hand2")
        self.btn_start.pack(side="left", padx=(0, 10))
        self.btn_strat = tk.Button(self.footer, text="⚙ Налаштування", command=self.open_settings, padx=12, pady=5, bd=0, cursor="hand2")
        self.btn_strat.pack(side="left", padx=6)
        self.btn_about = tk.Button(self.footer, text="ℹ Про програму", command=self.open_about, padx=12, pady=5, bd=0, cursor="hand2")
        self.btn_about.pack(side="left", padx=6)
        self.btn_exit = tk.Button(self.footer, text="✖ Вихід", command=self.confirm_exit, padx=14, pady=5, bd=0, cursor="hand2")
        self.btn_exit.pack(side="right")
        for w_tip, t_tip in ((self.btn_scan, "Автоматичний пошук серверів HomeGrid Monitor у локальній мережі"), (self.btn_hist, "Відкрити список раніше збережених адрес серверів"), (self.btn_dir, "Обрати папку"), (self.btn_open_dir, "Відкрити папку"), (self.btn_net, "Обрати мережеву папку"), (self.ent_cld, "Папка у хмарі pCloud (напр. HomeGridBackup)"), (self.btn_cld_cfg, "Налаштування pCloud"), (self.lbl_cld_st, "Налаштування pCloud"), (self.btn_open_log, "Відкрити текстовий файл backup.log")):
            ToolTip(w_tip, t_tip)

    def open_raw_log_file(self):
        import subprocess
        import sys
        bdir = get_logs_dir(self.engine.state)
        os.makedirs(bdir, exist_ok=True)
        lp = os.path.join(bdir, "backup.log")
        if not os.path.isfile(lp):
            with open(lp, "w", encoding="utf-8") as f:
                f.write("")
        try:
            if os.name == "nt":
                os.startfile(lp)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-t", lp])
            else:
                subprocess.Popen(["xdg-open", lp], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as ex:
            self.engine.log(f"Не вдалося відкрити backup.log: {ex}", "warn")


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
        if hasattr(self, "top_split"): self.top_split.configure(bg=p["bg"])
        if hasattr(self, "lbl_c2"): self.lbl_c2.configure(bg=p["panel"], fg=p["text"], font=f_bold)
        if hasattr(self, "btn_burger"): self.btn_burger.configure(bg=p["card"], fg=p["text"], font=f_bold)
        if hasattr(self, "btn_open_log"): self.btn_open_log.configure(bg=p["card"], fg=p["cyan"], font=f_sub)
        if hasattr(self, "btn_cloud_badge"):
            c_on = bool(self.engine.state.get("cloud_enabled"))
            self.var_cloud_st.set("☁ pCloud: ON" if c_on else "☁ pCloud: OFF")
            self.btn_cloud_badge.configure(bg=p["card"], fg=p["green"] if c_on else p["muted"], font=f_sub)
        for frm in (self.header, self.card_conn, self.card_stat, self.card_prog, self.card_log, self.footer):
            frm.configure(bg=p["panel"], highlightbackground=p["border"], padx=px, pady=py, relief=rel, bd=bd_w)
        def _paint_frames(node):
            for ch in node.winfo_children():
                if isinstance(ch, tk.Frame) and not isinstance(ch, HomeGridToggle):
                    ch.configure(bg=p["border"] if ch is getattr(self, "conn_sep", None) else p["panel"], bd=0, highlightthickness=0)
                    _paint_frames(ch)
        for parent_frm in (self.header, self.card_conn, self.card_stat, self.card_prog, self.card_log):
            _paint_frames(parent_frm)

        self.lbl_title.configure(bg=p["panel"], fg=p["text"], font=(fam, fs + 4, "bold"))
        self.lbl_sub.configure(bg=p["panel"], fg=p["muted"], font=f_sub)
        self.lbl_srv_badge.configure(bg=p["panel"], bd=0, highlightthickness=0)
        for lbl in (self.lbl_c1, self.lbl_c4):
            lbl.configure(bg=p["panel"], fg=p["text"], font=f_bold)
        self.lbl_stage.configure(bg=p["panel"], fg=p["text"], font=(fam, fs + 2, "bold"))
        self.lbl_pct.configure(bg=p["panel"], fg=p["green"], font=(fam, fs + 4, "bold"))
        for lbl in (self.l_srv, self.l_fav):
            lbl.configure(bg=p["panel"], fg=p["muted"], font=f_main)

        self.l_copies_hdr.configure(bg=p["panel"], fg=p["muted"], font=f_cap)
        for ent in (self.ent_srv, self.ent_dir, self.ent_net, self.ent_cld):
            ent.configure(bg=p["inp_bg"], fg=p["text"], insertbackground=p["text"], highlightbackground=p["border"], highlightcolor=p["blue"], font=f_main)

        f_big = f_bold
        self.t2_cap.configure(bg=p["panel"], fg=p["muted"], font=f_cap)
        self.t2_val.configure(bg=p["panel"], fg=p["green"], font=f_big)
        for _rf, _cl, _vl, _ in getattr(self, 'dest_rows', {}).values():
            _cl.configure(bg=p['panel'], fg=p['muted'], font=f_cap)
            _vl.configure(bg=p['panel'], fg=p['cyan'], font=f_sub)
        if hasattr(self, "t3_cap"):
            self.t3_cap.configure(bg=p["panel"], fg=p["muted"], font=f_cap)
            self.t3_val.configure(bg=p["panel"], fg=p["cyan"], font=f_big)
        if hasattr(self, "t3_sub"):
            self.t3_sub.configure(bg=p["panel"], fg=p["green"], font=f_sub)
        if hasattr(self, "lbl_pct"):
            self.lbl_pct.configure(bg=p["panel"], fg=p["green"], font=(fam, fs + 4, "bold"))

        self.pbar.configure(height=max(84, fs * 6 + 20))
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
        for b in (self.btn_scan, self.btn_hist, self.btn_dir, self.btn_open_dir, self.btn_net, self.btn_cld_cfg, self.btn_about):
            b.configure(highlightbackground=p["border"])
            b.configure(bg=p["card"], fg=p["text"], disabledforeground=dis_fg, activebackground=p["border"], activeforeground=p["text"], font=f_main, padx=bpx, pady=bpy)

        self.btn_clear_log.configure(bg=p["card"], fg=p["muted"], disabledforeground=dis_fg, activebackground=p["border"], activeforeground=p["text"], font=f_sub, padx=max(6, bpx - 2), pady=1)
        self.btn_conn.configure(bg=p["blue"], fg=p["btn_txt"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)
        self.btn_start.configure(bg=p["green"], fg=p["green_txt"], disabledforeground=dis_fg, font=f_bold, padx=bpx + 4, pady=bpy + 1)
        for b in (self.btn_analyze, self.btn_ops_hist, self.btn_stats, self.btn_cstats, self.btn_strat):
            b.configure(bg=p["card"], fg=p["cyan"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)
        self.btn_exit.configure(bg=p["panel"], fg=p["red"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)

        if hasattr(self, "btn_refresh_cld"):
            self.btn_refresh_cld.configure(bg=p["card"], fg=p["cyan"], highlightbackground=p["border"], font=f_sub)
        if hasattr(self, "btn_pick_lan"):
            self.btn_pick_lan.configure(bg=p["card"], fg=p["green"], disabledforeground=dis_fg, font=f_bold, padx=bpx, pady=bpy)

        if hasattr(self, "btn_theme"):
            thm_lbl = "☀️ Світла тема" if cur_theme == "dark" else "🌙 Темна тема"
            self.btn_theme.configure(
                text=thm_lbl, bg=p["card"], fg=p["text"], activebackground=p["border"],
                activeforeground=p["text"], relief="solid", bd=1, font=f_sub, padx=8, pady=2
            )
        res_txt = f"{m['outer_w']}×{m['outer_h']}"
        mode_lbl = f"LITE ({res_txt}) ▾" if is_lite else f"Графіка ({res_txt}) ▾"
        self.btn_mode.configure(
            text=mode_lbl,
            bg=p["panel"], fg=p["muted"], relief="flat", bd=0, disabledforeground=dis_fg, font=f_sub, padx=6, pady=2
        )
        self.btn_scan.configure(fg=p["cyan"], font=f_bold)
        self._render_fav_servers()
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
        self.btn_cstats.configure(text="🌐 Мережа" if lang == "uk" else "🌐 Network")
        self.btn_analyze.configure(text="🛡 Перевірка SHA" if lang == "uk" else "🛡 Verify SHA")
        fix_mac_buttons(self.root, p)
        if hasattr(self, "_setup_native_menubar"):
            self._setup_native_menubar()


    def on_scan_btn_click(self):
        found = getattr(self.engine, "discovered_servers", []) or []
        if not found:
            self.do_scan()
            return
        lng = self.engine.state.get("lang", "en")
        p = self._get_palette()
        fs = self.metrics["font_sz"]
        menu = tk.Menu(self.root, tearoff=0, bg=p["panel"], fg=p["text"], activebackground=p["blue"], activeforeground="#ffffff", font=(self._base_fam, fs))
        for url, t_ms, a_ms in found:
            menu.add_command(label=tr(f"{url}   (TCP: {t_ms} мс, API: {a_ms} мс)", lng), command=lambda u=url: self._select_discovered_server(u))
        menu.add_separator()
        menu.add_command(label=tr("Автопошук LAN", lng), command=self.do_scan)
        menu.tk_popup(self.btn_scan.winfo_rootx(), self.btn_scan.winfo_rooty() + self.btn_scan.winfo_height())

    def _select_discovered_server(self, url):
        self.var_srv.set(url)
        self.engine.state["server"] = url
        self._last_synced_srv = url
        self._render_fav_servers()
        self.engine.log(f"Обрано виявлений у мережі сервер: {url}", "ok")

    def _add_current_to_favs(self):
        self._apply_srv_autofill()
        raw = self.var_srv.get().strip().rstrip("/")
        if not raw:
            return
        favs = [x.strip().rstrip("/") for x in (self.engine.state.get("favorite_servers") or []) if x.strip()]
        if raw not in favs:
            favs.append(raw)
            self.engine.state["favorite_servers"] = favs[:8]
            commit_state(self.engine.state)
            self._render_fav_servers()

    def _remove_from_favs(self, url):
        norm_u = (url or "").strip().rstrip("/")
        self.engine.state["favorite_servers"] = [x for x in (self.engine.state.get("favorite_servers") or []) if x.strip().rstrip("/") != norm_u]
        commit_state(self.engine.state)
        self._render_fav_servers()

    def _pick_fav_server(self, url):
        self.var_srv.set(url)
        self.engine.state["server"] = url
        self._last_synced_srv = url
        commit_state(self.engine.state)
        self._render_fav_servers()

    def _render_fav_servers(self):
        if not hasattr(self, "fav_bar") or not self.fav_bar.winfo_exists():
            return
        for ch in self.fav_bar.winfo_children():
            ch.destroy()
        p = self._get_palette()
        lang = self.engine.state.get("lang", "en")
        fs = max(8, self.metrics["font_sz"] - 1)
        cur_u = (self.var_srv.get() or "").strip().rstrip("/")
        favs = [x.strip().rstrip("/") for x in (self.engine.state.get("favorite_servers") or []) if x.strip()]
        for u in favs[:4]:
            is_act = (u == cur_u)
            short_u = u.replace("http://", "").replace("https://", "")
            short_u = short_u[:19] + "..." if len(short_u) > 22 else short_u
            star = "★" if is_act else "☆"
            chip = tk.Button(self.fav_bar, text=f"{star} {short_u}", command=lambda t=u: self._pick_fav_server(t), bg=p["blue"] if is_act else p["card"], fg=p["btn_txt"] if is_act else p["text"], activebackground=p["border"], activeforeground=p["text"], bd=0, highlightthickness=1, highlightbackground=p["cyan"] if is_act else p["border"], font=(self._base_fam, fs, "bold" if is_act else "normal"), padx=8, pady=1, cursor="hand2")
            chip.pack(side="left", padx=(0, 4))
            chip.bind("<Button-3>", lambda _e, t=u: self._remove_from_favs(t))
            ToolTip(chip, f"{u} (ПКМ — прибрати з обраних)")
        if cur_u and cur_u not in favs and len(favs) < 8:
            btn_add = tk.Button(self.fav_bar, text=tr("+ Додати", lang), command=self._add_current_to_favs, bg=p["card"], fg=p["cyan"], activebackground=p["border"], activeforeground=p["text"], bd=0, highlightthickness=1, highlightbackground=p["border"], font=(self._base_fam, fs, "bold"), padx=8, pady=1, cursor="hand2")
            btn_add.pack(side="left", padx=(0, 4))

    def toggle_theme_quick(self):
        cur = self.engine.state.get("theme", "dark")
        self.engine.state["theme"] = "light" if cur == "dark" else "dark"
        self.engine.state["lite_mode"] = False
        commit_state(self.engine.state)
        self.apply_theme_and_mode(resize_win=False)

    def open_mode_menu(self):
        p = self._get_palette()
        fs = self.metrics["font_sz"]
        menu = tk.Menu(self.root, tearoff=0, bg=p["panel"], fg=p["text"], activebackground=p["blue"], activeforeground="#ffffff", font=(self._base_fam, fs))
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
        import shutil as _sh
        lang = self.engine.state.get("lang", "en")
        run = bool(getattr(self.engine, "is_running", False))
        lo = bool(self.engine.state.get("local_enabled", True))
        no = bool(self.engine.state.get("net_enabled", False))
        ld = (self.var_dir.get() or "").strip()
        nd = (self.var_net_dir.get() or "").strip()
        p = self._get_palette()
        fs = self.metrics["font_sz"]
        sf = (getattr(self, "_base_fam", "Segoe UI"), max(8, fs - 1))
        self.var_loc_en.set(lo)
        self.var_net_en.set(no)
        for tg in (self.chk_loc_tog, self.chk_net_tog):
            tg.apply_style(palette=p, state="disabled" if run else "normal", font_sz=max(8, fs - 1))
        self.l_dir.configure(bg=p["panel"], fg=p["text"] if lo else p["muted"], font=sf)
        self.l_net.configure(bg=p["panel"], fg=p["text"] if no else p["muted"], font=sf)
        with self.engine.lock:
            _net_info = dict((getattr(self.engine, "_dest_stats", {}) or {}).get("network") or {}) if (getattr(self.engine, "_dest_stats", {}) or {}).get("network") is not None else None
        for kind, en, ew, bw, sv, sl, ps in (("loc", lo, self.ent_dir, self.btn_dir, self.var_loc_st, self.lbl_loc_st, ld), ("net", no, self.ent_net, self.btn_net, self.var_net_st, self.lbl_net_st, nd)):
            st = "disabled" if (run or not en) else "normal"
            ew.configure(state=st, bg=p["inp_bg"], fg=p["text"], disabledbackground=p["panel"], disabledforeground=p["muted"])
            bw.configure(state=st)
            if not en or not ps:
                sv.set("—")
                sl.configure(bg=p["panel"], fg=p["muted"], font=sf)
            elif kind == "net":
                if _net_info is None:
                    sv.set("● ...")
                    sl.configure(bg=p["panel"], fg=p["muted"], font=sf)
                elif _net_info.get("ok"):
                    gb = _net_info.get("free_gb", -1)
                    sv.set((f"● {gb} " + ("ГБ" if lang == "uk" else "GB")) if gb >= 0 else "● Online")
                    sl.configure(bg=p["panel"], fg=p["amber"] if _net_info.get("stale") else p["green"], font=sf)
                else:
                    sv.set(tr("● офлайн", lang))
                    sl.configure(bg=p["panel"], fg=p["red"], font=sf)
            else:
                try:
                    if os.path.isdir(ps):
                        gb = round(_sh.disk_usage(ps).free / (1024 ** 3), 1)
                        sv.set(f"● {gb} " + ("ГБ" if lang == "uk" else "GB"))
                        sl.configure(bg=p["panel"], fg=p["green"], font=sf)
                    else:
                        sv.set(tr("● офлайн", lang))
                        sl.configure(bg=p["panel"], fg=p["red"], font=sf)
                except Exception:
                    sv.set(tr("● офлайн", lang))
                    sl.configure(bg=p["panel"], fg=p["red"], font=sf)
        if hasattr(self.engine, "request_dest_stats_refresh"):
            self.engine.request_dest_stats_refresh()
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
        self.save_net_manual()
        self.save_cloud_path_manual()
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
            was_r = getattr(self, "_was_running_ui", False)
            cur_r = bool(self.engine.is_running)
            if was_r and not cur_r:
                self._mir_btn_sig = None
            self._was_running_ui = cur_r
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

    def choose_net_dir(self):
        if not bool(self.var_net_en.get()):
            return
        chosen = choose_folder_native(self.engine.state.get("net_dir") or self.engine.state["backup_dir"])
        if chosen:
            self.engine.state["net_dir"] = chosen
            self.engine.state["net_enabled"] = True
            self.var_net_dir.set(chosen)
            commit_state(self.engine.state)
            self._update_mirror_btn()
            self.engine.log(f"Папку мережі змінено на: {chosen}", "ok")

    def toggle_net_dir(self):
        en = bool(self.var_net_en.get())
        self.engine.state["net_enabled"] = en
        commit_state(self.engine.state)
        self._update_mirror_btn()
        if en and not self.var_net_dir.get().strip():
            self.choose_net_dir()

    def save_net_manual(self):
        val = self.var_net_dir.get().strip()
        self.engine.state["net_dir"] = os.path.normpath(os.path.expanduser(val)) if val else ""
        self.engine.state["net_enabled"] = bool(self.var_net_en.get()) and bool(self.engine.state["net_dir"])
        commit_state(self.engine.state)
        self._update_mirror_btn()

    def _force_refresh_pcloud_stats(self):
        with self.engine.lock:
            if hasattr(self.engine, "_dest_stats"):
                self.engine._dest_stats["pcloud"] = None
        if hasattr(self.engine, "request_dest_stats_refresh"):
            self.engine.request_dest_stats_refresh()

    def save_cloud_path_manual(self):
        raw = (self.var_cloud_path.get() or "").strip()
        remote = str(self.engine.state.get("cloud_remote") or "pcloud").strip()
        try:
            from core.cloud import validate_cloud_settings
            clean = validate_cloud_settings(remote, raw or "HomeGridBackup")
        except Exception as exc:
            self.engine.log(str(exc), "warn")
            clean = self.engine.state.get("cloud_path") or "HomeGridBackup"
        self.var_cloud_path.set(clean)
        if self.engine.state.get("cloud_path") != clean:
            self.engine.state["cloud_path"] = clean
            commit_state(self.engine.state)
            if hasattr(self.engine, "request_dest_stats_refresh"):
                self.engine.request_dest_stats_refresh()
        self._update_mirror_btn()

    def toggle_cloud_quick(self):
        en = bool(self.var_cld_en.get())
        self.engine.state["cloud_enabled"] = en
        if en and not (self.var_cloud_path.get() or "").strip():
            self.var_cloud_path.set(self.engine.state.get("cloud_path") or "HomeGridBackup")
        commit_state(self.engine.state)
        self._update_mirror_btn()
        if en:
            try:
                self.ent_cld.focus_set()
                self.ent_cld.icursor("end")
            except Exception:
                pass
    def _retry_pending_cloud_sync(self):
        if not WINDOWS7_CLOUD_SYNC_PREVIEW or not self.engine.state.get("cloud_enabled"):
            return
        try:
            from core.cloud import cloud_sync_queue_state, start_cloud_sync_worker
            if cloud_sync_queue_state(self.engine)["total"]:
                start_cloud_sync_worker(self.engine)
        except Exception as exc:
            self.engine.log(f"Не вдалося перевірити чергу хмарної синхронізації: {exc}", "warn")

    def _get_sys_load(self):
        cpu_p, ram_p = 0, 0
        try:
            if os.name == "nt":
                import ctypes
                class _MS(ctypes.Structure):
                    _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong)] + [("u", ctypes.c_ulonglong)] * 7
                ms = _MS(); ms.l = ctypes.sizeof(_MS)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                    ram_p = int(ms.m)
                idl, ker, usr = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
                if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idl), ctypes.byref(ker), ctypes.byref(usr)):
                    cur = (idl.value, ker.value + usr.value)
                    prv = getattr(self, "_prv_cpu", None); self._prv_cpu = cur
                    if prv and cur[1] > prv[1]:
                        cpu_p = max(0, min(100, int(round(100.0 * (1.0 - (cur[0] - prv[0]) / (cur[1] - prv[1]))))))
            elif os.path.exists("/proc/stat") and os.path.exists("/proc/meminfo"):
                with open("/proc/stat", "r", encoding="utf-8") as f:
                    vals = [int(x) for x in f.readline().split()[1:8]]
                cur = (vals[3] + vals[4], sum(vals))
                prv = getattr(self, "_prv_cpu", None); self._prv_cpu = cur
                if prv and cur[1] > prv[1]:
                    cpu_p = max(0, min(100, int(round(100.0 * (1.0 - (cur[0] - prv[0]) / (cur[1] - prv[1]))))))
                with open("/proc/meminfo", "r", encoding="utf-8") as f:
                    mi = dict(ln.split(":", 1) for ln in f if ":" in ln)
                tot = int(mi["MemTotal"].split()[0])
                if "MemAvailable" in mi:
                    avl = int(mi["MemAvailable"].split()[0])
                else:
                    avl = int(mi.get("MemFree", "0").split()[0]) + int(mi.get("Buffers", "0").split()[0]) + int(mi.get("Cached", "0").split()[0])
                ram_p = max(0, min(100, int(round(100.0 * (tot - avl) / max(1, tot)))))
            else:
                if hasattr(os, "getloadavg"):
                    cpu_p = max(0, min(100, int(round((os.getloadavg()[0] / max(1, os.cpu_count() or 1)) * 100))))
                import sys as _s
                if _s.platform == "darwin":
                    import subprocess as _sp, re as _re
                    tb = int(_sp.check_output(["sysctl", "-n", "hw.memsize"], timeout=0.3).decode().strip())
                    vm = _sp.check_output(["vm_stat"], timeout=0.3).decode("utf-8", errors="ignore")
                    mp = _re.search(r"page size of (\d+) bytes", vm)
                    ps = int(mp.group(1)) if mp else 4096
                    fp = sum(int(m.group(1)) for k in ("Pages free", "Pages inactive", "Pages speculative") if (m := _re.search(rf"{k}:\s+(\d+)", vm)))
                    ram_p = max(0, min(100, int(round(100.0 * (tb - fp * ps) / max(1, tb)))))
                elif hasattr(os, "sysconf"):
                    pg = os.sysconf("SC_PAGE_SIZE")
                    tot = os.sysconf("SC_PHYS_PAGES") * pg
                    avl = os.sysconf("SC_AVPHYS_PAGES") * pg
                    if tot > 0:
                        ram_p = max(0, min(100, int(round(100.0 * (tot - avl) / tot))))
        except Exception:
            pass
        return cpu_p, ram_p

    def _tick_3s_loader(self):
        try:
            if not self.root.winfo_exists(): return
            pal = self._get_palette()
            cpu_p, ram_p = self._get_sys_load()
            col = pal["red"] if (cpu_p >= 85 or ram_p >= 90) else (pal["amber"] if (cpu_p >= 60 or ram_p >= 75) else pal["cyan"])
            self.lbl_load_3s.configure(text=f"CPU: {cpu_p}% | RAM: {ram_p}%", bg=pal["panel"], fg=col)
        except Exception:
            pass
        self.root.after(5000, self._tick_3s_loader)

    def _poll_ui(self):
        try:
            if getattr(self.engine, "tray_icon", None) is not None:
                from gui.tray import drain_tray_ui_queue
                drain_tray_ui_queue()
            if self.root.state() in ("iconic", "withdrawn"):
                if self.engine.modal and self.engine.modal.get("id") != self.last_modal_id:
                    self.last_modal_id = self.engine.modal["id"]
                    self.show_window()
                    self._show_engine_modal(self.engine.modal)
                self.root.after(450, self._poll_ui)
                return
            st = self.engine.state
            srv_in_state = (st.get("server") or "").strip()
            last_synced = getattr(self, "_last_synced_srv", srv_in_state)
            if srv_in_state and srv_in_state != last_synced:
                self._last_synced_srv = srv_in_state
                if self.root.focus_get() != self.ent_srv:
                    self.var_srv.set(srv_in_state)

            now_m = time.monotonic()
            if now_m - getattr(self, '_last_disk_t', 0.0) >= 5.5 or not self.engine.is_running:
                self._last_disk_t = now_m
                self._cached_disk = self.engine.get_storage_stats()
            cur_lang = st.get("lang", "en")
            cur_theme = st.get("theme", "dark")
            cur_lite = bool(st.get("lite_mode", False))
            cur_fs = self.metrics["font_sz"]

            z_cnt, z_mb, free_gb = getattr(self, '_cached_disk', (0, 0.0, -1))
            _disk_sig = (z_cnt, z_mb, free_gb, cur_lang)
            if getattr(self, '_last_disk_sig', None) != _disk_sig:
                self._last_disk_sig = _disk_sig
                free_txt = f" — Вільно: {free_gb} ГБ" if free_gb >= 0 else ""
                self.var_disk.set(tr(f"{z_cnt} архівів ({z_mb} МБ){free_txt}", cur_lang))
            if hasattr(self, "dest_rows"):
                with self.engine.lock:
                    d_snap = dict(getattr(self.engine, "_dest_stats", {}) or {})
                active_flags = {
                    "network": bool(st.get("net_enabled") and (st.get("net_dir") or "").strip()),
                    "pcloud": bool(st.get("cloud_enabled")),
                }
                p_cur = self._get_palette()
                for d_k in ("network", "pcloud"):
                    rf, _cl, vl, v_str = self.dest_rows[d_k]
                    is_on = active_flags[d_k]
                    info = d_snap.get(d_k)
                    _dsig = (is_on, repr(info), cur_lang, cur_theme)
                    if getattr(rf, "_dsig", None) != _dsig:
                        rf._dsig = _dsig
                        if not is_on:
                            if rf.winfo_ismapped():
                                rf.pack_forget()
                        else:
                            if not rf.winfo_ismapped():
                                rf.pack(anchor="center", pady=1, before=self.stat_btns)
                            if info is None:
                                v_str.set(tr("оновлення...", cur_lang))
                                vl.configure(fg=p_cur["muted"])
                            elif not info.get("ok"):
                                rsn = tr(info.get("reason") or "недоступно", cur_lang)
                                v_str.set(rsn)
                                vl.configure(fg=p_cur["amber"] if info.get("reason") else p_cur["red"])
                            else:
                                fr_t = f" — Вільно: {info['free_gb']} ГБ" if info.get("free_gb", -1) >= 0 else ""
                                q_t = f" ({tr('в черзі', cur_lang)})" if info.get("pending") else ""
                                v_str.set(tr(f"{info['count']} архівів ({info['mb']} МБ){fr_t}", cur_lang) + q_t)
                                vl.configure(fg=p_cur["amber"] if info.get("pending") else (p_cur["green"] if d_k == "pcloud" else p_cur["cyan"]))

            if hasattr(self, "lbl_srv_badge"):
                dn = getattr(self.engine, "diag_net", "") or ""
                dp = getattr(self.engine, "diag_ping", "") or ""
                _s_sig = (dn, dp, cur_theme)
                if getattr(self, "_last_srv_b_sig", None) != _s_sig:
                    self._last_srv_b_sig = _s_sig
                    p_c = self._get_palette()
                    if "ОНЛАЙН" in dn:
                        self.var_srv_badge.set(tr(f"● {dp}", cur_lang) if dp else "● Online")
                        self.lbl_srv_badge.configure(bg=p_c["panel"], fg=p_c["green"])
                    elif "ОФЛАЙН" in dn:
                        self.var_srv_badge.set("● Offline")
                        self.lbl_srv_badge.configure(bg=p_c["panel"], fg=p_c["red"])
            if hasattr(self.engine, "get_last_backup_info") and hasattr(self, "t3_val"):
                lb_txt, lb_st = self.engine.get_last_backup_info()
                _lb_sig = (lb_txt, lb_st, cur_lang, cur_theme, cur_lite)
                if getattr(self, '_last_lb_sig', None) != _lb_sig:
                    self._last_lb_sig = _lb_sig
                    parts = lb_txt.split(chr(10))
                    self.var_last_bkp.set(tr(parts[0], cur_lang))
                    self.var_last_bkp_sub.set(tr(parts[1], cur_lang) if len(parts) > 1 else "")
                    p_cur = self._get_palette()
                    c_ok = p_cur["green"] if lb_st == "ok" else (p_cur["amber"] if lb_st == "warn" else p_cur["muted"])
                    self.t3_val.configure(fg=c_ok)
                    if hasattr(self, "t3_sub"):
                        self.t3_sub.configure(fg=c_ok)

            if hasattr(self, "lbl_pill"):
                ptype = getattr(self.engine, "pill_type", "idle")
                ptxt = getattr(self.engine, "pill_text", "") or "Очікування"
                if " | " in ptxt and ptype == "idle":
                    ptxt = "Очікування"
                _pill_sig = (ptype, ptxt, cur_lang, cur_theme, cur_lite, cur_fs)
                if getattr(self, '_last_pill_sig', None) != _pill_sig:
                    self._last_pill_sig = _pill_sig
                    p_cur = self._get_palette()
                    pill_fg = {"ok": p_cur.get("pill_ok_fg", p_cur["green"]), "run": p_cur["cyan"], "warn": p_cur["amber"], "err": p_cur["red"]}.get(ptype, p_cur["muted"])
                    pill_bg = p_cur.get("pill_ok_bg", p_cur["card"]) if ptype in ("ok", "idle") and "pill_ok_bg" in p_cur else p_cur["card"]
                    bd_pill = 0 if "pill_ok_bg" in p_cur else 1
                    self.lbl_pill.configure(text=tr(ptxt, cur_lang), bg=pill_bg, fg=pill_fg, bd=bd_pill, highlightbackground=p_cur["border"], font=(self._base_fam, cur_fs, "bold"))

            if getattr(self, '_last_stage_val', None) != self.engine.stage:
                self._last_stage_val = self.engine.stage
                self.var_stage.set(self.engine.stage)
            _pct_sig = (self.engine.indeterminate, self.engine.progress, cur_lang)
            if getattr(self, '_last_pct_sig', None) != _pct_sig:
                self._last_pct_sig = _pct_sig
                self.var_pct.set(tr("пошук...", cur_lang) if self.engine.indeterminate else f"{self.engine.progress}%")
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
            btns_changed = False
            _action_btn_sig = (btn_state, cur_lang, cur_theme, cur_lite)
            if getattr(self, '_last_action_btn_sig', None) != _action_btn_sig:
                self._last_action_btn_sig = _action_btn_sig
                for b in (self.btn_scan, self.btn_hist, self.btn_conn, self.btn_open_dir, self.btn_start, self.btn_strat):
                    if str(b.cget("state")) != btn_state:
                        b.configure(state=btn_state)
                        btns_changed = True
            self._update_mirror_btn()
            disc = getattr(self.engine, "discovered_servers", []) or []
            if hasattr(self, "btn_scan"):
                _lan_sig = (len(disc), cur_theme, cur_lang)
                if getattr(self, '_last_lan_sig', None) != _lan_sig:
                    self._last_lan_sig = _lan_sig
                    p_c = self._get_palette()
                    base_scan = tr("Автопошук LAN", cur_lang)
                    self.btn_scan.configure(text=f"{base_scan} ({len(disc)})" if disc else base_scan, fg=p_c["green"] if disc else p_c["cyan"])
                    btns_changed = True
            if btns_changed:
                fix_mac_buttons(self.root, self._get_palette())

            with self.engine.lock:
                logs = list(self.engine.logs)
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
            delay = 650 if lite else 450
        else:
            delay = 1200 if lite else 800
        self.root.after(delay, self._poll_ui)
