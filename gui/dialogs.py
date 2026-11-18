# ==============================================================================
# [ФАЙЛ: gui/dialogs.py (v1.012 | 18.11.2026 18:54) — МОДАЛЬНЫЕ ДИАЛОГИ, НАСТРОЙКИ, АНАЛИЗ GFS И О ПРОГРАММЕ]
# ==============================================================================
import tkinter as tk
from tkinter import ttk
from core.config import SCRIPT_VER, commit_state
from core.gfs import compute_gfs_plan, toggle_keep_tag, apply_gfs_cleanup
from core.backup import verify_all_archives
from core.scheduler import _resolve_exe_path, _sync_scheduler_from_windows, _manage_windows_scheduler
from gui.styles import THEME_LABELS, UI_SCALE_LABELS, UI_FONT_LABELS, PBAR_STYLE_LABELS, THEMES
from gui.widgets import StyledProgressBar
from gui.tray import _force_quit_app

class DialogsMixin:
    def _make_dialog(self, title, w=640, h=420, scrollable=False, min_outer_w=0, min_outer_h=0):
        p = self._get_palette()
        m = self.metrics
        k = m["k"]
        fw = m.get("outer_w", m["win_w"]) - m["win_w"]
        fh = m.get("outer_h", m["win_h"]) - m["win_h"]
        bound_w = m.get("outer_w", m["sw"])
        bound_h = m.get("outer_h", m["sh"])

        target_outer_w = max(min_outer_w, int(round(w * k)))
        target_outer_h = max(min_outer_h, int(round(h * k)))
        outer_w = min(bound_w, target_outer_w)
        outer_h = min(bound_h, target_outer_h)

        dlg_w = max(360, outer_w - fw)
        dlg_h = max(160, outer_h - fh)
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.configure(bg=p["panel"])
        dlg.transient(self.root)
        dlg.grab_set()
        px = m["wa_x"] + max(0, (m["sw"] - outer_w) // 2)
        py = m["wa_y"] + max(0, (m["sh"] - outer_h) // 2)
        dlg.geometry(f"{dlg_w}x{dlg_h}+{px}+{py}")

        if not scrollable:
            return dlg, p, dlg

        wrap = tk.Frame(dlg, bg=p["panel"])
        wrap.pack(fill="both", expand=True)
        canvas = tk.Canvas(wrap, bg=p["panel"], highlightthickness=0, bd=0)
        vbar = tk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=p["panel"])
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win_id, width=e.width))
        canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_wheel(ev):
            try:
                canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")
            except Exception:
                pass
        dlg.bind("<MouseWheel>", _on_wheel)
        return dlg, p, inner

    def confirm_exit(self):
        fs = self.metrics["font_sz"]
        dlg, p, _ = self._make_dialog("Підтвердження виходу", 460, 185)
        tk.Label(dlg, text="Ви дійсно бажаєте завершити роботу HomeGrid Backup та закрити програму?", bg=p["panel"], fg=p["text"], wraplength=int(410 * self.metrics["k"]), font=("Segoe UI", fs)).pack(pady=22, padx=16)
        bf = tk.Frame(dlg, bg=p["panel"])
        bf.pack(side="bottom", fill="x", padx=16, pady=12)
        tk.Button(bf, text="Скасувати", command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=5).pack(side="right", padx=8)
        tk.Button(bf, text="✖ Так, вийти", command=lambda: (dlg.destroy(), _force_quit_app(self.engine)), bg=p["red"], fg="#ffffff", font=("Segoe UI", fs, "bold"), padx=14, pady=5).pack(side="right", padx=8)

    def _show_engine_modal(self, m):
        fs = self.metrics["font_sz"]
        dlg, p, _ = self._make_dialog(m["title"], 480, 215)
        def _done(val):
            try:
                dlg.destroy()
            except Exception:
                pass
            self.engine.submit_modal(val)

        dlg.protocol("WM_DELETE_WINDOW", lambda: _done("" if m["type"] == "pin" else False))
        tk.Label(dlg, text=m["text"], bg=p["panel"], fg=p["text"], wraplength=int(430 * self.metrics["k"]), font=("Segoe UI", fs)).pack(pady=(18, 10), padx=16)
        bf = tk.Frame(dlg, bg=p["panel"])
        bf.pack(side="bottom", fill="x", padx=16, pady=12)

        if m["type"] == "pin":
            v_pin = tk.StringVar()
            ent = tk.Entry(dlg, textvariable=v_pin, show="•", bg=p["inp_bg"], fg=p["text"], insertbackground=p["text"], font=("Segoe UI", fs + 2), justify="center")
            ent.pack(padx=40, fill="x", ipady=4)
            ent.focus_set()
            ent.bind("<Return>", lambda e: _done(v_pin.get().strip()))
            tk.Button(bf, text="Скасувати", command=lambda: _done(""), bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=5).pack(side="right", padx=8)
            tk.Button(bf, text="Підтвердити", command=lambda: _done(v_pin.get().strip()), bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=14, pady=5).pack(side="right", padx=8)
        elif m["type"] == "confirm":
            tk.Button(bf, text="Ні", command=lambda: _done(False), bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=16, pady=5).pack(side="right", padx=8)
            tk.Button(bf, text="Так", command=lambda: _done(True), bg=p["amber"], fg="#ffffff", font=("Segoe UI", fs, "bold"), padx=16, pady=5).pack(side="right", padx=8)
        else:
            tk.Button(bf, text="ОК", command=lambda: _done(True), bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=18, pady=5).pack(side="right", padx=8)

    def open_history_modal(self):
        fs = self.metrics["font_sz"]
        dlg, p, _ = self._make_dialog("Історія адрес серверів", 560, 380)
        tk.Label(dlg, text="Оберіть раніше збережену адресу або видаліть зайву:", bg=p["panel"], fg=p["muted"], font=("Segoe UI", fs)).pack(anchor="w", padx=14, pady=(10, 6))
        box = tk.Frame(dlg, bg=p["panel"])
        box.pack(fill="both", expand=True, padx=14)

        def _pick(url):
            self.var_srv.set(url)
            self.engine.state["server"] = url
            self._last_synced_srv = url
            commit_state(self.engine.state)
            dlg.destroy()

        def _render():
            for ch in box.winfo_children():
                ch.destroy()
            hist = self.engine.state.get("server_history") or []
            if not hist:
                tk.Label(box, text="Історія адрес порожня.", bg=p["panel"], fg=p["muted"], font=("Segoe UI", fs)).pack(pady=20)
                return
            for i, u in enumerate(hist):
                row = tk.Frame(box, bg=p["card"], padx=8, pady=5, bd=1, relief="solid")
                row.pack(fill="x", pady=3)
                tk.Label(row, text=f"#{i+1}  {u}", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold")).pack(side="left")
                tk.Button(row, text="✖", bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=8, command=lambda url=u: _del(url)).pack(side="right", padx=4)
                tk.Button(row, text="Обрати", bg=p["blue"], fg="#ffffff", font=("Segoe UI", fs), padx=10, command=lambda url=u: _pick(url)).pack(side="right", padx=6)

        def _del(url):
            norm_u = (url or "").strip().rstrip("/")
            self.engine.state["server_history"] = [
                x for x in (self.engine.state.get("server_history") or [])
                if x.strip().rstrip("/") != norm_u
            ]
            if (self.engine.state.get("server") or "").strip().rstrip("/") == norm_u:
                self.engine.state["server"] = ""
                self.var_srv.set("")
                self._last_synced_srv = ""
            commit_state(self.engine.state)
            _render()

        _render()
        tk.Button(dlg, text="Закрити", command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=5).pack(side="bottom", anchor="e", padx=14, pady=12)

    def open_settings(self):
        _sync_scheduler_from_windows(self.engine.state)
        st = self.engine.state
        fs = self.metrics["font_sz"]
        dlg, p, host = self._make_dialog(
            "Налаштування програми, тем, масштабу, GFS та Планувальника",
            860, 620, scrollable=True, min_outer_w=800, min_outer_h=600
        )

        v_daily = tk.IntVar(value=st.get("daily_days", 7))
        v_today = tk.IntVar(value=st.get("today_max", 2))
        v_week = tk.IntVar(value=st.get("weekly_count", 4))
        v_month = tk.IntVar(value=st.get("monthly_count", 12))
        v_year = tk.IntVar(value=st.get("yearly_count", 3))
        v_trash = tk.BooleanVar(value=(st.get("delete_mode", "trash") == "trash"))
        v_sclean = tk.BooleanVar(value=bool(st.get("silent_cleanup", False)))
        v_theme = tk.StringVar(value=st.get("theme", "dark"))
        v_scale = tk.StringVar(value=st.get("ui_scale", "auto"))
        v_font = tk.IntVar(value=int(st.get("ui_font", 0)))
        v_tray_min = tk.BooleanVar(value=bool(st.get("minimize_to_tray", True)))
        v_pstyle = tk.StringVar(value=st.get("progress_style", "v8"))

        sch_parts = (st.get("sched_time") or "03:00").split(":")
        v_sh = tk.StringVar(value=sch_parts if len(sch_parts) > 0 else "03")
        v_sm = tk.StringVar(value=sch_parts if len(sch_parts) > 1 else "00")
        v_smode = tk.StringVar(value=st.get("sched_mode", "--hidden"))
        v_sprio = tk.IntVar(value=int(st.get("sched_prio", 6)))
        v_smissed = tk.BooleanVar(value=bool(st.get("sched_missed", True)))
        v_swake = tk.BooleanVar(value=bool(st.get("sched_wake", False)))

        top_grid = tk.Frame(host, bg=p["panel"])
        top_grid.pack(fill="x", padx=14, pady=(8, 4))
        top_grid.columnconfigure(0, weight=1)
        top_grid.columnconfigure(1, weight=1)

        f_gfs = tk.LabelFrame(top_grid, text=" 1. Стратегія збереження файлів (GFS) ", bg=p["card"], fg=p["green"], font=("Segoe UI", fs, "bold"), padx=12, pady=6)
        f_gfs.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=2)
        for ci in (0, 1, 2, 3):
            f_gfs.columnconfigure(ci, weight=1 if ci in (0, 2) else 0)

        tk.Label(f_gfs, text="Щоденні (дн.):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=0, column=0, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=1, to=90, textvariable=v_daily, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=0, column=1, sticky="w", padx=(4, 14), pady=3)
        tk.Label(f_gfs, text="За сьогодні:", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=0, column=2, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=1, to=15, textvariable=v_today, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=0, column=3, sticky="w", padx=(4, 0), pady=3)

        tk.Label(f_gfs, text="Тижневі (шт.):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=1, column=0, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=0, to=52, textvariable=v_week, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=1, column=1, sticky="w", padx=(4, 14), pady=3)
        tk.Label(f_gfs, text="Місячні (шт.):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=1, column=2, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=0, to=60, textvariable=v_month, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=1, column=3, sticky="w", padx=(4, 0), pady=3)

        tk.Label(f_gfs, text="Річні (архів):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=2, column=0, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=0, to=25, textvariable=v_year, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=2, column=1, sticky="w", padx=(4, 14), pady=3)
        tk.Checkbutton(f_gfs, text="🗑️ У Кошик (замість назавжди)", variable=v_trash, bg=p["card"], fg=p["cyan"], selectcolor=p["inp_bg"], font=("Segoe UI", fs)).grid(row=2, column=2, columnspan=2, sticky="w", pady=3)

        f_del = tk.LabelFrame(top_grid, text=" 2. Системний трей та тихий режим ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"), padx=12, pady=6)
        f_del.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=2)
        tk.Checkbutton(f_del, text="📌 Згортати у системний трей при закритті [X]", variable=v_tray_min, bg=p["card"], fg=p["amber"], selectcolor=p["inp_bg"], font=("Segoe UI", fs, "bold")).pack(anchor="w", pady=6)
        tk.Checkbutton(f_del, text="🧹 Очищати старі копії у тихому режимі (GFS)", variable=v_sclean, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs)).pack(anchor="w", pady=6)

        fs_sch = fs + 1
        f_sch = tk.LabelFrame(host, text=" 3. Автозапуск за розкладом (Планувальник завдань Windows) ", bg=p["card"], fg=p["blue"], font=("Segoe UI", fs_sch, "bold"), padx=12, pady=8)
        f_sch.pack(fill="x", padx=14, pady=4)

        sr1 = tk.Frame(f_sch, bg=p["card"])
        sr1.pack(fill="x", pady=3)
        tk.Label(sr1, text="Час щодня:", bg=p["card"], fg=p["text"], font=("Segoe UI", fs_sch, "bold")).pack(side="left")
        ttk.Combobox(sr1, textvariable=v_sh, values=[f"{i:02d}" for i in range(24)], width=4, state="readonly", font=("Segoe UI", fs_sch)).pack(side="left", padx=4)
        tk.Label(sr1, text=":", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs_sch, "bold")).pack(side="left")
        ttk.Combobox(sr1, textvariable=v_sm, values=[f"{i:02d}" for i in range(60)], width=4, state="readonly", font=("Segoe UI", fs_sch)).pack(side="left", padx=4)
        tk.Radiobutton(sr1, text="У фоні через трей (--hidden)", variable=v_smode, value="--hidden", bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs_sch)).pack(side="left", padx=(16, 8))
        tk.Radiobutton(sr1, text="З вікном консолі (--silent)", variable=v_smode, value="--silent", bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs_sch)).pack(side="left", padx=8)

        sr2 = tk.Frame(f_sch, bg=p["card"])
        sr2.pack(fill="x", pady=3)
        tk.Label(sr2, text="Пріоритет (2-9):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs_sch)).pack(side="left")
        tk.Spinbox(sr2, from_=2, to=9, textvariable=v_sprio, width=4, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs_sch)).pack(side="left", padx=6)
        tk.Checkbutton(sr2, text="Запускати пропущене", variable=v_smissed, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs_sch)).pack(side="left", padx=12)
        tk.Checkbutton(sr2, text="Розбудити ПК зі сну", variable=v_swake, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs_sch)).pack(side="left", padx=12)

        lbl_sch_msg = tk.Label(f_sch, text="", bg=p["card"], fg=p["green"], font=("Segoe UI", fs, "bold"))
        lbl_sch_msg.pack(anchor="w", pady=(2, 2))

        sr3 = tk.Frame(f_sch, bg=p["card"])
        sr3.pack(fill="x", pady=(2, 0))
        def _create_task():
            t_str = f"{v_sh.get()}:{v_sm.get()}"
            st["sched_time"] = t_str
            st["sched_mode"] = v_smode.get()
            st["sched_missed"] = v_smissed.get()
            st["sched_wake"] = v_swake.get()
            st["sched_prio"] = int(v_sprio.get())
            commit_state(st)
            ok_s, msg_s = _manage_windows_scheduler("create", t_str, st["sched_mode"], st["sched_missed"], st["sched_wake"], st["sched_prio"])
            lbl_sch_msg.configure(text=msg_s, fg=p["green"] if ok_s else p["red"])
            self.engine.log(msg_s, "ok" if ok_s else "err")

        def _del_task():
            ok_s, msg_s = _manage_windows_scheduler("delete")
            lbl_sch_msg.configure(text=msg_s, fg=p["amber"] if ok_s else p["red"])
            self.engine.log(msg_s, "warn" if ok_s else "err")

        def _copy_cmd(flag):
            cmd = f'"{_resolve_exe_path()}" {flag}'
            self.root.clipboard_clear()
            self.root.clipboard_append(cmd)
            lbl_sch_msg.configure(text=f"✓ Скопійовано у буфер: {cmd}", fg=p["cyan"])

        tk.Button(sr3, text="📅 Додати в Планувальник", command=_create_task, bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=12, pady=4, cursor="hand2").pack(side="left", padx=(0, 10))
        tk.Button(sr3, text="🗑️ Видалити задачу", command=_del_task, bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=12, pady=4, cursor="hand2").pack(side="left", padx=6)
        tk.Button(sr3, text="📋 Копіювати --hidden", command=lambda: _copy_cmd("--hidden"), bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=10, pady=4, cursor="hand2").pack(side="right", padx=(6, 0))
        tk.Button(sr3, text="📋 Копіювати --silent", command=lambda: _copy_cmd("--silent"), bg=p["blue"], fg="#ffffff", font=("Segoe UI", fs), padx=10, pady=4, cursor="hand2").pack(side="right", padx=8)

        bot_grid = tk.Frame(host, bg=p["panel"])
        bot_grid.pack(fill="x", padx=14, pady=(6, 10))
        bot_grid.columnconfigure(0, weight=1)
        bot_grid.columnconfigure(1, weight=1)

        f_thm = tk.LabelFrame(bot_grid, text=" 4. Тема (7 стилів), роздільна здатність та шрифт ", bg=p["card"], fg=p["amber"], font=("Segoe UI", fs, "bold"), padx=12, pady=8)
        f_thm.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        t_r1 = tk.Frame(f_thm, bg=p["card"])
        t_r1.pack(fill="x", pady=3)
        tk.Label(t_r1, text="Тема:", width=7, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        theme_map = {lbl: code for code, lbl in THEME_LABELS}
        rev_theme = {code: lbl for code, lbl in THEME_LABELS}
        cb_theme = ttk.Combobox(t_r1, values=[lbl for _, lbl in THEME_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_theme.set(rev_theme.get(v_theme.get(), THEME_LABELS[0][1]))
        cb_theme.pack(side="left", fill="x", expand=True)

        t_r2 = tk.Frame(f_thm, bg=p["card"])
        t_r2.pack(fill="x", pady=3)
        tk.Label(t_r2, text="Екран:", width=7, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        scale_map = {lbl: code for code, lbl in UI_SCALE_LABELS}
        rev_scale = {code: lbl for code, lbl in UI_SCALE_LABELS}
        cb_scale = ttk.Combobox(t_r2, values=[lbl for _, lbl in UI_SCALE_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_scale.set(rev_scale.get(v_scale.get(), UI_SCALE_LABELS[0][1]))
        cb_scale.pack(side="left", fill="x", expand=True)

        t_r3 = tk.Frame(f_thm, bg=p["card"])
        t_r3.pack(fill="x", pady=3)
        tk.Label(t_r3, text="Шрифт:", width=7, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        font_map = {lbl: code for code, lbl in UI_FONT_LABELS}
        rev_font = {code: lbl for code, lbl in UI_FONT_LABELS}
        cb_font = ttk.Combobox(t_r3, values=[lbl for _, lbl in UI_FONT_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_font.set(rev_font.get(v_font.get(), UI_FONT_LABELS[0][1]))
        cb_font.pack(side="left", fill="x", expand=True)

        f_sty = tk.LabelFrame(bot_grid, text=" 5. Стиль індикатора прогресу (12 стилів) ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"), padx=12, pady=8)
        f_sty.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)
        style_map = {lbl: code for code, lbl in PBAR_STYLE_LABELS}
        rev_map = {code: lbl for code, lbl in PBAR_STYLE_LABELS}
        cb_style = ttk.Combobox(f_sty, values=[lbl for _, lbl in PBAR_STYLE_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_style.set(rev_map.get(v_pstyle.get(), PBAR_STYLE_LABELS[0][1]))
        cb_style.pack(fill="x", pady=(2, 10))
        prev_bar = StyledProgressBar(f_sty, height=max(22, fs + 10))
        prev_bar.pack(fill="x")

        def _upd_prev(_e=None):
            code = style_map.get(cb_style.get(), "v8")
            t_code = theme_map.get(cb_theme.get(), "dark")
            v_pstyle.set(code)
            v_theme.set(t_code)
            prev_bar.set_state(65, False, code, False, THEMES.get(t_code, THEMES["dark"]))
        cb_style.bind("<<ComboboxSelected>>", _upd_prev)
        cb_theme.bind("<<ComboboxSelected>>", _upd_prev)
        dlg.after(60, _upd_prev)

        bf = tk.Frame(dlg, bg=p["panel"], bd=1, relief="solid")
        bf.pack(side="bottom", fill="x", padx=14, pady=(6, 12), before=dlg.winfo_children()[0])
        def _commit_settings(close_after):
            st["daily_days"] = max(1, int(v_daily.get()))
            st["today_max"] = max(1, int(v_today.get()))
            st["weekly_count"] = max(0, int(v_week.get()))
            st["monthly_count"] = max(0, int(v_month.get()))
            st["yearly_count"] = max(0, int(v_year.get()))
            st["delete_mode"] = "trash" if v_trash.get() else "direct"
            st["minimize_to_tray"] = bool(v_tray_min.get())
            st["silent_cleanup"] = bool(v_sclean.get())
            chosen_theme = theme_map.get(cb_theme.get(), "dark")
            if chosen_theme != st.get("theme") and st.get("lite_mode", False):
                st["lite_mode"] = False
            st["theme"] = chosen_theme
            st["ui_scale"] = scale_map.get(cb_scale.get(), "auto")
            st["ui_font"] = font_map.get(cb_font.get(), 0)
            st["progress_style"] = style_map.get(cb_style.get(), "v8")
            commit_state(st)
            self.apply_theme_and_mode(resize_win=True)
            self.engine.log("Налаштування програми, теми, шрифту та стратегії GFS застосовано.", "ok")
            dlg.destroy()
            if not close_after:
                self.open_settings()

        tk.Button(bf, text="🔑 Скинути PIN", command=self.reset_pins, bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=12, pady=6, cursor="hand2").pack(side="left", padx=(6, 6), pady=6)
        tk.Button(bf, text="Закрити", command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=6, cursor="hand2").pack(side="right", padx=(6, 6), pady=6)
        tk.Button(bf, text="💾 Зберегти та закрити", command=lambda: _commit_settings(True), bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=14, pady=6, cursor="hand2").pack(side="right", padx=6, pady=6)
        tk.Button(bf, text="✅ Застосувати", command=lambda: _commit_settings(False), bg=p["blue"], fg="#ffffff", font=("Segoe UI", fs, "bold"), padx=14, pady=6, cursor="hand2").pack(side="right", padx=6, pady=6)

    def open_analyze(self):
        import threading
        fs = self.metrics["font_sz"]
        bpx, bpy = self.metrics["btn_px"], self.metrics["btn_py"]
        fam = "Consolas" if self.engine.state.get("lite_mode", False) else self._get_palette().get("font", "Segoe UI")
        dlg, p, _ = self._make_dialog("Аналіз локального сховища (GFS та SHA-256)", 880, 540)

        hdr = tk.Label(dlg, text="", bg=p["panel"], fg=p["cyan"], font=(fam, fs, "bold"))
        hdr.pack(anchor="w", padx=14, pady=(10, 6))

        top_f = tk.Frame(dlg, bg=p["panel"])
        top_f.pack(fill="both", expand=True, padx=14)
        canvas = tk.Canvas(top_f, bg=p["log_bg"], highlightthickness=1, highlightbackground=p["border"])
        vbar = tk.Scrollbar(top_f, orient="vertical", command=canvas.yview)
        list_frm = tk.Frame(canvas, bg=p["log_bg"])
        list_frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=list_frm, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win_id, width=e.width))
        canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_wheel(ev):
            try:
                canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")
            except Exception:
                pass
        dlg.bind("<MouseWheel>", _on_wheel)

        lbl_ver = tk.Label(dlg, text="", bg=p["panel"], fg=p["green"], justify="left", font=("Consolas", max(9, fs - 1), "bold"))
        lbl_ver.pack(anchor="w", padx=14, pady=(6, 0))

        def _toggle_keep(fname):
            ok_t, new_n = toggle_keep_tag(self.engine.state, fname)
            if ok_t:
                self.engine.log(f"Оновлено захист архіву: {new_n}", "ok")
            _refresh()

        def _refresh():
            for ch in list_frm.winfo_children():
                ch.destroy()
            all_it, keep_it, del_it = compute_gfs_plan(self.engine.state)
            tot_mb = round(sum(x["size"] for x in all_it) / 1048576.0, 1)
            keep_mb = round(sum(x["size"] for x in keep_it) / 1048576.0, 1)
            del_mb = round(sum(x["size"] for x in del_it) / 1048576.0, 1)
            hdr.configure(text=f"Всього: {len(all_it)} шт. ({tot_mb} МБ)  |  Залишиться: {len(keep_it)} шт. ({keep_mb} МБ)  |  Застарілих: {len(del_it)} шт. ({del_mb} МБ)")
            if not all_it:
                tk.Label(list_frm, text="У папці поки немає ZIP-архівів.", bg=p["log_bg"], fg=p["muted"], font=(fam, fs)).pack(pady=20)
                return
            for it in all_it:
                mb = round(it["size"] / 1048576.0, 1)
                is_del = (it["new_tag"] == "DELETE")
                is_keep = (it["new_tag"] == "KEEP")
                col = p["amber"] if is_del else p["green"]
                lbl = "[ВИДАЛИТИ]" if is_del else f"[{it['new_tag']}]"
                row = tk.Frame(list_frm, bg=p["log_bg"], pady=3)
                row.pack(fill="x", padx=6)
                btn_t = "🔓 Зняти KEEP" if is_keep else "🔒 KEEP"
                tk.Button(row, text=btn_t, command=lambda fn=it["name"]: _toggle_keep(fn), bg=p["card"], fg=p["amber"] if is_keep else p["text"], font=(fam, max(8, fs - 2), "bold"), padx=8, pady=2, cursor="hand2").pack(side="right", padx=(8, 2))
                tk.Label(row, text=f"{lbl:<11} {mb:6.1f} МБ | {it['dt_str']} | {it['name']}", bg=p["log_bg"], fg=col, anchor="w", font=("Consolas", max(9, fs - 1))).pack(side="left", fill="x", expand=True)

        verify_bar = ttk.Progressbar(dlg, mode="determinate", maximum=100, length=420)
        verify_status = tk.Label(dlg, text="Перевірка не запущена", bg=p["panel"], fg=p["muted"], justify="left", anchor="w", font=(fam, max(8, fs - 1)))
        verify_status.pack(fill="x", padx=14, pady=(2, 2))
        verify_bar.pack(fill="x", padx=14, pady=(0, 6))
        verify_running = {"value": False}

        def _verify_progress(pct, stage):
            def _apply():
                if not dlg.winfo_exists():
                    return
                verify_bar["value"] = pct
                verify_status.configure(text=f"{pct}% — {stage}")
            try:
                dlg.after(0, _apply)
            except Exception:
                pass

        def _verify_done(res):
            verify_running["value"] = False
            btn_verify.configure(state="normal")
            ok_all = (res["err_cnt"] == 0)
            msg = f"SHA-256 + CRC32: справних {res['ok_cnt']} | без .sha256: {res['warn_cnt']} | пошкоджених: {res['err_cnt']}"
            lbl_ver.configure(text=msg, fg=p["green"] if ok_all else p["red"])
            verify_status.configure(text=f"100% — Перевірено архівів: {res['total']}")
            verify_bar["value"] = 100
            self.engine.log(msg, "ok" if ok_all else "err")

        def _verify_failed(exc):
            verify_running["value"] = False
            btn_verify.configure(state="normal")
            verify_status.configure(text=f"Помилка перевірки: {exc}", fg=p["red"])
            self.engine.log(f"Помилка ручної перевірки архівів: {exc}", "err")

        def _verify():
            if verify_running["value"]:
                return
            verify_running["value"] = True
            btn_verify.configure(state="disabled")
            lbl_ver.configure(text="Перевірка виконується…", fg=p["cyan"])
            verify_bar["value"] = 0
            verify_status.configure(text="Підготовка списку архівів…", fg=p["cyan"])

            def _worker():
                try:
                    res = verify_all_archives(self.engine.state, _verify_progress)
                    dlg.after(0, lambda result=res: _verify_done(result) if dlg.winfo_exists() else None)
                except Exception as exc:
                    dlg.after(0, lambda error=exc: _verify_failed(error) if dlg.winfo_exists() else None)

            threading.Thread(target=_worker, daemon=True).start()

        def _clean():
            apply_gfs_cleanup(self.engine, skip_prompt=True)
            _refresh()

        _refresh()
        bf = tk.Frame(dlg, bg=p["panel"])
        bf.pack(side="bottom", fill="x", padx=14, pady=10)
        btn_verify = tk.Button(bf, text="🛡️ Перевірити SHA-256 + CRC32 усіх", command=_verify, bg=p["card"], fg=p["cyan"], font=(fam, fs, "bold"), padx=bpx, pady=bpy, cursor="hand2")
        btn_verify.pack(side="left", padx=(0, 8))
        tk.Button(bf, text="🗑️ Очистити застарілі зараз", command=_clean, bg=p["amber"], fg="#000000", font=(fam, fs, "bold"), padx=bpx, pady=bpy, cursor="hand2").pack(side="left", padx=6)
        tk.Button(bf, text="Закрити", command=dlg.destroy, bg=p["card"], fg=p["text"], font=(fam, fs), padx=bpx, pady=bpy, cursor="hand2").pack(side="right")

    def open_ops_history(self):
        fs = self.metrics["font_sz"]
        dlg, p, _ = self._make_dialog("Журнал останніх операцій архівування", 680, 420)
        tk.Label(dlg, text="Останні 25 операцій створення резервних копій (дата, розмір та підсумок):", bg=p["panel"], fg=p["muted"], font=("Segoe UI", fs)).pack(anchor="w", padx=14, pady=(10, 6))
        box = tk.Frame(dlg, bg=p["log_bg"], bd=1, relief="solid")
        box.pack(fill="both", expand=True, padx=14)

        ops = getattr(self.engine, "op_history", []) or []
        if not ops:
            tk.Label(box, text="Журнал операцій поки порожній. Запустіть резервне копіювання.", bg=p["log_bg"], fg=p["muted"], font=("Segoe UI", fs)).pack(pady=24)
        else:
            for item in ops:
                st_lbl = item.get("status", "")
                is_ok = (st_lbl == "Успішно")
                col = p["green"] if is_ok else p["red"]
                mb_txt = f"{item.get('size_mb', 0)} МБ" if is_ok else "—"
                row = tk.Frame(box, bg=p["card"], padx=8, pady=4)
                row.pack(fill="x", padx=6, pady=2)
                tk.Label(row, text=f"[{item.get('ts', '')}]", bg=p["card"], fg=p["muted"], font=("Consolas", max(8, fs - 1))).pack(side="left")
                tk.Label(row, text=f" {st_lbl:<9} ", bg=p["card"], fg=col, font=("Segoe UI", fs, "bold")).pack(side="left", padx=4)
                tk.Label(row, text=f"{mb_txt:>9}  |  {item.get('detail', '')}", bg=p["card"], fg=p["text"], font=("Consolas", max(8, fs - 1))).pack(side="left")

        tk.Button(dlg, text="Закрити", command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=5).pack(side="bottom", anchor="e", padx=14, pady=12)

    def open_about(self):
        fs = self.metrics["font_sz"]
        bpx, bpy = self.metrics["btn_px"], self.metrics["btn_py"]
        fam = "Consolas" if self.engine.state.get("lite_mode", False) else self._get_palette().get("font", "Segoe UI")
        dlg, p, _ = self._make_dialog(f"Про програму — HomeGrid Backup v{SCRIPT_VER}", 620, 360)
        info = (
            "HomeGrid Backup — нативний інструмент для резервного копіювання даних та налаштувань інвертора.\n\n"
            "• Пряма робота без браузерів, локальних вебсерверів та зайвого навантаження на пам'ять.\n"
            "• Адаптація під роздільну здатність монітора, 7 тем оформлення, 12 стилів прогресу та LITE-режим.\n"
            "• Перевірка цілісності кожного ZIP-архіву за CRC32 + SHA-256 та дзеркалювання у другу папку.\n"
            "• Автоматична GFS-ротація (щоденні, тижневі, місячні, річні копії) та запуск за розкладом Windows."
        )
        tk.Label(dlg, text=info, bg=p["panel"], fg=p["text"], justify="left", wraplength=int(560 * self.metrics["k"]), font=(fam, fs)).pack(padx=18, pady=18, anchor="w", fill="x")
        tk.Button(dlg, text="Закрити", command=dlg.destroy, bg=p["green"], fg=p["green_txt"], font=(fam, fs, "bold"), padx=bpx + 4, pady=bpy, cursor="hand2").pack(side="bottom", anchor="e", padx=18, pady=14)
