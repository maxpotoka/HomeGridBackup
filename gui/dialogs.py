import re
import os
import time
from core.i18n import tr, apply_widget_i18n
# ==============================================================================
# [ФАЙЛ: gui/dialogs.py (v1.055 | 19.11.2026 14:54) — МОДАЛЬНЫЕ ДИАЛОГИ, НАСТРОЙКИ, АНАЛИЗ GFS И О ПРОГРАММЕ]
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
    def _calc_parent_center(self, parent_win, w_box, h_box):
        m = self.metrics
        try:
            parent_win.update_idletasks()
            pw, ph = parent_win.winfo_width(), parent_win.winfo_height()
            if pw > 120 and ph > 120:
                cx = parent_win.winfo_rootx() + (pw - w_box) // 2
                cy = parent_win.winfo_rooty() + (ph - h_box) // 2
                vw = max(m["sw"], parent_win.winfo_vrootwidth() or parent_win.winfo_screenwidth() or m["sw"])
                vh = max(m["sh"], parent_win.winfo_vrootheight() or parent_win.winfo_screenheight() or m["sh"])
                vx = parent_win.winfo_vrootx() if hasattr(parent_win, "winfo_vrootx") else 0
                vy = parent_win.winfo_vrooty() if hasattr(parent_win, "winfo_vrooty") else 0
                x = max(vx + 6, min(cx, vx + vw - w_box - 6))
                y = max(vy + 6, min(cy, vy + vh - h_box - 30))
                return x, y
        except Exception:
            pass
        return m["wa_x"] + max(0, (m["sw"] - w_box) // 2), m["wa_y"] + max(0, (m["sh"] - h_box) // 2)

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
        self._ignore_resize_until = time.time() + 0.7
        dlg = tk.Toplevel(self.root)
        dlg.bind('<Destroy>', lambda e: setattr(self, '_ignore_resize_until', time.time() + 0.7) if e.widget is dlg else None)
        dlg.title(tr(title, self.engine.state.get("lang", "en")))
        dlg.configure(bg=p["panel"])
        parent_win = self.root.grab_current() or self.root
        dlg.transient(parent_win)
        def _safe_grab(tries=0):
            try:
                if dlg.winfo_exists():
                    dlg.update_idletasks()
                    dlg.deiconify()
                    dlg.grab_set()
            except Exception:
                if tries < 8 and dlg.winfo_exists():
                    dlg.after(25, lambda: _safe_grab(tries + 1))
        _safe_grab()
        px, py = self._calc_parent_center(parent_win, dlg_w, dlg_h)
        dlg.geometry(f"{dlg_w}x{dlg_h}+{px}+{py}")
        def _recenter_later():
            try:
                if dlg.winfo_exists():
                    dlg.update_idletasks()
                    rx, ry = self._calc_parent_center(parent_win, dlg.winfo_width(), dlg.winfo_height())
                    dlg.geometry(f"+{rx}+{ry}")
            except Exception:
                pass
        dlg.after(35, _recenter_later)
        dlg.maxsize(min(m["sw"], int(round(max(w, 760) * k * 1.15))), min(m["sh"], int(round(max(h, 520) * k * 1.15))))
        try:
            dlg.lift(parent_win)
            dlg.attributes("-topmost", True)
            dlg.update_idletasks()
            dlg.attributes("-topmost", False)
            dlg.focus_force()
        except Exception:
            pass

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

    def _fit_dialog(self, dlg):
        """Гарантирует, что содержимое диалога не обрезается: растит окно до нужного размера (в пределах экрана)."""
        try:
            dlg.update_idletasks()
            m = self.metrics
            need_w, need_h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
            cur_w, cur_h = dlg.winfo_width(), dlg.winfo_height()
            new_w = min(max(cur_w, need_w), max(360, m["sw"] - 20))
            new_h = min(max(cur_h, need_h), max(240, m["sh"] - 60))
            mx_w, mx_h = dlg.maxsize()
            dlg.maxsize(max(new_w, mx_w), max(new_h, mx_h))
            if (new_w, new_h) != (cur_w, cur_h):
                p_ref = dlg.master if getattr(dlg, "master", None) else self.root
                x, y = self._calc_parent_center(p_ref, new_w, new_h)
                dlg.geometry(f"{new_w}x{new_h}+{x}+{y}")
            dlg.minsize(min(new_w, need_w), min(new_h, need_h))
            dlg.lift()
            dlg.focus_force()
        except Exception:
            pass

    def confirm_exit(self):
        fs = self.metrics["font_sz"]
        dlg, p, _ = self._make_dialog("Підтвердження виходу", 460, 185)
        tk.Label(dlg, text="Ви дійсно бажаєте завершити роботу HomeGrid Backup та закрити програму?", bg=p["panel"], fg=p["text"], wraplength=int(410 * self.metrics["k"]), font=("Segoe UI", fs)).pack(pady=22, padx=16)
        bf = tk.Frame(dlg, bg=p["panel"])
        bf.pack(side="bottom", fill="x", padx=16, pady=12)
        tk.Button(bf, text="Скасувати", command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=5).pack(side="right", padx=8)
        tk.Button(bf, text="Так, вийти", command=lambda: (dlg.destroy(), _force_quit_app(self.engine)), bg=p["red"], fg="#ffffff", font=("Segoe UI", fs, "bold"), padx=14, pady=5).pack(side="right", padx=8)
        apply_widget_i18n(dlg, self.engine.state.get("lang", "en"))

    def _show_engine_modal(self, m):
        fs = self.metrics["font_sz"]
        lang = self.engine.state.get("lang", "en")
        is_lan_dlg = (m["type"] == "lan_found")
        dlg, p, _ = self._make_dialog(m["title"], 660 if is_lan_dlg else 590, 340 if is_lan_dlg else 235)
        def _done(val):
            try:
                dlg.destroy()
            except Exception:
                pass
            self.engine.submit_modal(val)

        dlg.protocol("WM_DELETE_WINDOW", lambda: _done("" if m["type"] == "pin" else False))

        if is_lan_dlg:
            items = m.get("default") or []
            hdr_t = "Оберіть дію для виявленого сервера в локальній мережі:" if lang == "uk" else "Choose an action for the discovered LAN server:"
            tk.Label(dlg, text=hdr_t, bg=p["panel"], fg=p["muted"], font=("Segoe UI", fs)).pack(anchor="w", padx=16, pady=(14, 8))
            box = tk.Frame(dlg, bg=p["panel"])
            box.pack(fill="both", expand=True, padx=16, pady=(0, 6))
            for url, t_ms, a_ms in items:
                row = tk.Frame(box, bg=p["card"], bd=1, relief="solid", padx=10, pady=8)
                row.pack(fill="x", pady=4)
                info_f = tk.Frame(row, bg=p["card"])
                info_f.pack(side="left", fill="x", expand=True)
                tk.Label(info_f, text=url, bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs + 1, "bold")).pack(anchor="w")
                tk.Label(info_f, text=f"TCP: {t_ms} ms  •  API: {a_ms} ms", bg=p["card"], fg=p["muted"], font=("Segoe UI", max(8, fs - 1))).pack(anchor="w")
                btn_bkp_t = "🔌 Підключити та бекап" if lang == "uk" else "🔌 Connect & Backup"
                btn_sav_t = "⭐ В Історію" if lang == "uk" else "⭐ Save to History"
                tk.Button(row, text=btn_bkp_t, command=lambda u=url: _done({"action": "backup", "url": u}), bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=10, pady=4, cursor="hand2").pack(side="right", padx=(6, 0))
                tk.Button(row, text=btn_sav_t, command=lambda u=url: _done({"action": "save", "url": u}), bg=p["blue"], fg="#ffffff", font=("Segoe UI", fs, "bold"), padx=10, pady=4, cursor="hand2").pack(side="right", padx=6)
            bf = tk.Frame(dlg, bg=p["panel"])
            bf.pack(side="bottom", fill="x", padx=16, pady=12)
            tk.Button(bf, text="Закрити" if lang == "uk" else "Close", command=lambda: _done(False), bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=5).pack(side="right")
            self._fit_dialog(dlg)
            return
        is_list = ("• " in m["text"])
        if is_list:
            lines = [ln.strip() for ln in m["text"].splitlines() if ln.strip()]
            tk.Label(dlg, text=lines[0], bg=p["panel"], fg=p["text"], anchor="w", justify="left", font=("Segoe UI", fs, "bold")).pack(pady=(14, 6), padx=18, fill="x")
            list_box = tk.Frame(dlg, bg=p["card"], bd=1, relief="solid", padx=10, pady=8)
            list_box.pack(padx=18, pady=(0, 8), fill="x")
            for ln in lines[1:]:
                clean_ln = ln.lstrip("• ").strip()
                prefix = "•  " if ln.startswith("•") else ""
                tk.Label(list_box, text=f"{prefix}{clean_ln}", bg=p["card"], fg=p["amber"] if prefix else p["muted"], anchor="w", justify="left", font=("Consolas", max(9, fs - 1))).pack(anchor="w", pady=1)
        else:
            tk.Label(dlg, text=m["text"], bg=p["panel"], fg=p["text"], justify="center", anchor="center", wraplength=int(480 * self.metrics["k"]), font=("Segoe UI", fs)).pack(pady=(16, 10), padx=18, fill="x")
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
        self._fit_dialog(dlg)

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
        apply_widget_i18n(dlg, self.engine.state.get("lang", "en"))

    def open_settings(self):
        _sync_scheduler_from_windows(self.engine.state)
        st = self.engine.state
        fs = self.metrics["font_sz"]
        dlg, p, host = self._make_dialog("Налаштування програми, тем, масштабу, GFS та Планувальника", 940, 620, scrollable=False, min_outer_w=880, min_outer_h=580)

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
        v_lang = tk.StringVar(value=st.get("lang", "en"))
        v_tray_min = tk.BooleanVar(value=bool(st.get("minimize_to_tray", True)))
        v_pstyle = tk.StringVar(value=st.get("progress_style", "v8"))

        sch_parts = (st.get("sched_time") or "03:00").split(":")
        v_sh = tk.StringVar(value=sch_parts[0] if len(sch_parts) > 0 else "03")
        v_sm = tk.StringVar(value=sch_parts[1] if len(sch_parts) > 1 else "00")
        v_smode = tk.StringVar(value=st.get("sched_mode", "--hidden"))
        v_sprio = tk.IntVar(value=int(st.get("sched_prio", 6)))
        v_smissed = tk.BooleanVar(value=bool(st.get("sched_missed", True)))
        v_swake = tk.BooleanVar(value=bool(st.get("sched_wake", False)))

        bf = tk.Frame(dlg, bg=p["panel"], bd=1, relief="solid")
        bf.pack(side="bottom", fill="x", padx=12, pady=(4, 8))

        nb_style = ttk.Style()
        nb_style.configure("HGB.TNotebook", background=p["panel"], borderwidth=0)
        nb_style.configure("HGB.TNotebook.Tab", font=("Segoe UI", fs, "bold"), padding=(12, 4))
        nb = ttk.Notebook(host, style="HGB.TNotebook")
        nb.pack(fill="both", expand=True, padx=10, pady=(4, 4))
        tab_bkp = tk.Frame(nb, bg=p["panel"])
        tab_ui = tk.Frame(nb, bg=p["panel"])
        nb.add(tab_bkp, text="  Резервне копіювання та Розклад  ")
        nb.add(tab_ui, text="  Вигляд та Інтерфейс  ")

        top_grid = tk.Frame(tab_bkp, bg=p["panel"])
        top_grid.pack(fill="x", padx=12, pady=(6, 2))
        top_grid.columnconfigure(0, weight=1)
        top_grid.columnconfigure(1, weight=1)

        f_gfs = tk.LabelFrame(top_grid, text=" 1. Стратегія збереження файлів (GFS) ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"), padx=10, pady=3)
        f_gfs.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=2)
        for ci in (0, 1, 2, 3):
            f_gfs.columnconfigure(ci, weight=1 if ci in (0, 2) else 0)

        tk.Label(f_gfs, text="Щоденні (дн.):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=0, column=0, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=1, to=90, textvariable=v_daily, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=0, column=1, sticky="w", padx=(4, 14), pady=3)
        tk.Label(f_gfs, text="Копій за день:", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=0, column=2, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=1, to=15, textvariable=v_today, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=0, column=3, sticky="w", padx=(4, 0), pady=3)

        tk.Label(f_gfs, text="Тижневі (шт.):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=1, column=0, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=0, to=52, textvariable=v_week, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=1, column=1, sticky="w", padx=(4, 14), pady=3)
        tk.Label(f_gfs, text="Місячні (шт.):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=1, column=2, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=0, to=60, textvariable=v_month, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=1, column=3, sticky="w", padx=(4, 0), pady=3)

        tk.Label(f_gfs, text="Річні (архів):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=2, column=0, sticky="w", pady=3)
        tk.Spinbox(f_gfs, from_=0, to=25, textvariable=v_year, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs)).grid(row=2, column=1, sticky="w", padx=(4, 14), pady=3)
        tk.Checkbutton(f_gfs, text="У Кошик (замість видалення)", variable=v_trash, bg=p["card"], fg=p["cyan"], selectcolor=p["inp_bg"], font=("Segoe UI", fs)).grid(row=2, column=2, columnspan=2, sticky="w", pady=3)

        f_del = tk.LabelFrame(top_grid, text=" 2. Системний трей та тихий режим ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"), padx=12, pady=6)
        f_del.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=2)
        tk.Checkbutton(f_del, text="Згортати у трей при закритті", variable=v_tray_min, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs)).pack(anchor="w", pady=6)
        tk.Checkbutton(f_del, text="Автоочищення у фоні (GFS)", variable=v_sclean, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs)).pack(anchor="w", pady=4)

        fs_sch = fs + 1
        f_sch = tk.LabelFrame(tab_bkp, text=" 3. Автозапуск за розкладом ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs_sch, "bold"), padx=10, pady=4)
        f_sch.pack(fill="x", padx=12, pady=2)

        sr1 = tk.Frame(f_sch, bg=p["card"])
        sr1.pack(fill="x", pady=3)
        tk.Label(sr1, text="Час щодня:", bg=p["card"], fg=p["text"], font=("Segoe UI", fs_sch, "bold")).pack(side="left")
        ttk.Combobox(sr1, textvariable=v_sh, values=[f"{i:02d}" for i in range(24)], width=4, state="readonly", font=("Segoe UI", fs_sch)).pack(side="left", padx=4)
        tk.Label(sr1, text=":", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs_sch, "bold")).pack(side="left")
        ttk.Combobox(sr1, textvariable=v_sm, values=[f"{i:02d}" for i in range(60)], width=4, state="readonly", font=("Segoe UI", fs_sch)).pack(side="left", padx=4)
        tk.Radiobutton(sr1, text="У фоні (з іконкою в треї)", variable=v_smode, value="--hidden", bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs_sch)).pack(side="left", padx=(16, 8))
        tk.Radiobutton(sr1, text="З вікном консолі", variable=v_smode, value="--silent", bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs_sch)).pack(side="left", padx=8)

        sr2 = tk.Frame(f_sch, bg=p["card"])
        sr2.pack(fill="x", pady=3)
        tk.Label(sr2, text="Пріоритет (2-9):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs_sch)).pack(side="left")
        tk.Spinbox(sr2, from_=2, to=9, textvariable=v_sprio, width=4, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs_sch)).pack(side="left", padx=6)
        tk.Checkbutton(sr2, text="Запускати пропущене", variable=v_smissed, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs_sch)).pack(side="left", padx=12)
        tk.Checkbutton(sr2, text="Розбудити ПК зі сну", variable=v_swake, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=("Segoe UI", fs_sch)).pack(side="left", padx=12)

        lbl_sch_msg = tk.Label(f_sch, text="", bg=p["card"], fg=p["green"], font=("Segoe UI", fs, "bold"))
        lbl_sch_msg.pack(side="left", padx=8)

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

        tk.Button(sr3, text="Додати в Планувальник", command=_create_task, bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=12, pady=4, cursor="hand2").pack(side="left", padx=(0, 10))
        tk.Button(sr3, text="Видалити задачу", command=_del_task, bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=12, pady=4, cursor="hand2").pack(side="left", padx=6)
        def _open_adv_sched():
            m_adv = tk.Menu(dlg, tearoff=0, bg=p["panel"], fg=p["text"], font=("Segoe UI", fs))
            m_adv.add_command(label="Копіювати команду фонового запуску", command=lambda: _copy_cmd("--hidden"))
            m_adv.add_command(label="Копіювати команду консольного запуску", command=lambda: _copy_cmd("--silent"))
            m_adv.tk_popup(btn_adv.winfo_rootx(), btn_adv.winfo_rooty() + btn_adv.winfo_height())
        btn_adv = tk.Button(sr3, text="Додатково ▾", command=_open_adv_sched, bg=p["card"], fg=p["muted"], font=("Segoe UI", fs), padx=10, pady=4, cursor="hand2")
        btn_adv.pack(side="right")

        bot_col = tk.Frame(tab_ui, bg=p["panel"])
        bot_col.pack(fill="both", expand=True, padx=14, pady=(6, 4))

        f_thm = tk.LabelFrame(bot_col, text=" 4. Оформлення, мова та масштаб екрана ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"), padx=14, pady=8)
        f_thm.pack(fill="x", pady=(0, 8))

        t_r0 = tk.Frame(f_thm, bg=p["card"])
        t_r0.pack(fill="x", pady=4)
        tk.Label(t_r0, text="Мова інтерфейсу:", width=20, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        lang_map = {"English (Default)": "en", "Українська": "uk"}
        rev_lang = {"en": "English (Default)", "uk": "Українська"}
        cb_lang = ttk.Combobox(t_r0, values=list(lang_map.keys()), state="readonly", font=("Segoe UI", fs))
        cb_lang.set(rev_lang.get(v_lang.get(), "English (Default)"))
        cb_lang.pack(side="left", fill="x", expand=True)

        t_r1 = tk.Frame(f_thm, bg=p["card"])
        t_r1.pack(fill="x", pady=4)
        tk.Label(t_r1, text="Тема оформлення:", width=20, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        theme_map = {lbl: code for code, lbl in THEME_LABELS}
        rev_theme = {code: lbl for code, lbl in THEME_LABELS}
        cb_theme = ttk.Combobox(t_r1, values=[lbl for _, lbl in THEME_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_theme.set(rev_theme.get(v_theme.get(), THEME_LABELS))
        cb_theme.pack(side="left", fill="x", expand=True)

        t_r2 = tk.Frame(f_thm, bg=p["card"])
        t_r2.pack(fill="x", pady=4)
        tk.Label(t_r2, text="Роздільна здатність:", width=20, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        scale_map = {lbl: code for code, lbl in UI_SCALE_LABELS}
        rev_scale = {code: lbl for code, lbl in UI_SCALE_LABELS}
        cb_scale = ttk.Combobox(t_r2, values=[lbl for _, lbl in UI_SCALE_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_scale.set(rev_scale.get(v_scale.get(), UI_SCALE_LABELS))
        cb_scale.pack(side="left", fill="x", expand=True)

        t_r3 = tk.Frame(f_thm, bg=p["card"])
        t_r3.pack(fill="x", pady=4)
        tk.Label(t_r3, text="Розмір шрифту:", width=20, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        font_map = {lbl: code for code, lbl in UI_FONT_LABELS}
        rev_font = {code: lbl for code, lbl in UI_FONT_LABELS}
        cb_font = ttk.Combobox(t_r3, values=[lbl for _, lbl in UI_FONT_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_font.set(rev_font.get(v_font.get(), UI_FONT_LABELS))
        cb_font.pack(side="left", fill="x", expand=True)

        f_sty = tk.LabelFrame(bot_col, text=" 5. Стиль індикатора прогресу (14 стилів) ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"), padx=14, pady=8)
        f_sty.pack(fill="x", pady=(0, 4))
        s_r0 = tk.Frame(f_sty, bg=p["card"])
        s_r0.pack(fill="x", pady=(2, 8))
        tk.Label(s_r0, text="Стиль смуги:", width=20, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        style_map = {lbl: code for code, lbl in PBAR_STYLE_LABELS}
        rev_map = {code: lbl for code, lbl in PBAR_STYLE_LABELS}
        cb_style = ttk.Combobox(s_r0, values=[lbl for _, lbl in PBAR_STYLE_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_style.set(rev_map.get(v_pstyle.get(), PBAR_STYLE_LABELS))
        cb_style.pack(side="left", fill="x", expand=True)
        prev_bar = StyledProgressBar(f_sty, height=max(24, fs + 12))
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

        def _commit_settings(close_after):
            st["daily_days"] = max(1, int(v_daily.get()))
            st["today_max"] = max(1, int(v_today.get()))
            st["weekly_count"] = max(0, int(v_week.get()))
            st["monthly_count"] = max(0, int(v_month.get()))
            st["yearly_count"] = max(0, int(v_year.get()))
            st["lang"] = lang_map.get(cb_lang.get(), "en")
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

        tk.Button(bf, text="Скинути PIN", command=lambda: (self.reset_pins(), lbl_sch_msg.configure(text="✓ Збережені PIN-коди очищено", fg=p["amber"])), bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=12, pady=6, cursor="hand2").pack(side="left", padx=(6, 6), pady=6)
        tk.Button(bf, text="Скасувати", command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=6, cursor="hand2").pack(side="right", padx=(6, 6), pady=6)
        tk.Button(bf, text="Зберегти та закрити", command=lambda: _commit_settings(True), bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=14, pady=6, cursor="hand2").pack(side="right", padx=6, pady=6)
        tk.Button(bf, text="Застосувати", command=lambda: _commit_settings(False), bg=p["blue"], fg="#ffffff", font=("Segoe UI", fs, "bold"), padx=14, pady=6, cursor="hand2").pack(side="right", padx=6, pady=6)
        def _i18n_settings():
            lng = st.get("lang", "en")
            nb.tab(0, text=tr("  Резервне копіювання та Розклад  ", lng))
            nb.tab(1, text=tr("  Вигляд та Інтерфейс  ", lng))
            apply_widget_i18n(dlg, lng)
        dlg.after(20, _i18n_settings)

    def open_analyze(self):
        import threading
        fs = self.metrics["font_sz"]
        bpx, bpy = self.metrics["btn_px"], self.metrics["btn_py"]
        fam = "Consolas" if self.engine.state.get("lite_mode", False) else self._get_palette().get("font", "Segoe UI")
        dlg, p, _ = self._make_dialog("Аналіз локального сховища (GFS та SHA-256)", 880, 540)

        lbl_sum = tk.Label(dlg, text="", bg=p["panel"], fg=p["cyan"], font=(fam, fs, "bold"))
        lbl_sum.pack(anchor="w", padx=14, pady=(10, 4))

        bf = tk.Frame(dlg, bg=p["panel"])
        bf.pack(side="bottom", fill="x", padx=14, pady=(4, 10))
        verify_bar = ttk.Progressbar(dlg, mode="determinate", maximum=100)
        verify_bar.pack(side="bottom", fill="x", padx=14, pady=(2, 4))
        verify_status = tk.Label(dlg, text="Перевірка не запущена", bg=p["panel"], fg=p["muted"], anchor="w", font=(fam, max(8, fs - 1)))
        verify_status.pack(side="bottom", fill="x", padx=14, pady=(2, 0))
        lbl_ver = tk.Label(dlg, text="", bg=p["panel"], fg=p["muted"], anchor="w", font=(fam, max(8, fs - 1), "bold"))
        lbl_ver.pack(side="bottom", fill="x", padx=14, pady=(4, 0))

        wrap = tk.Frame(dlg, bg=p["log_bg"], bd=1, relief="solid")
        wrap.pack(fill="both", expand=True, padx=14, pady=(2, 4))
        cv = tk.Canvas(wrap, bg=p["log_bg"], highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(wrap, orient="vertical", command=cv.yview)
        list_box = tk.Frame(cv, bg=p["log_bg"])
        list_box.bind("<Configure>", lambda _e: cv.configure(scrollregion=cv.bbox("all")))
        win_id = cv.create_window((0, 0), window=list_box, anchor="nw")
        cv.bind("<Configure>", lambda e: cv.itemconfigure(win_id, width=e.width))
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)

        from core.files import remove_backup_file
        def remove_file_smart(path_to_del, use_trash=True):
            remove_backup_file(path_to_del, "trash" if use_trash else "direct")
        buf_options = {"4 КБ": 4096, "16 КБ": 16384, "64 КБ": 65536, "256 КБ": 262144, "1 МБ": 1048576, "4 МБ": 4194304, "8 МБ": 8388608}
        v_buf = tk.StringVar(value="64 КБ")
        verify_state = {"running": False, "stop": False, "pct": 0, "stage": "", "res": None, "err": None, "status_map": {}}

        def _delete_archive_pair(fname):
            bdir = self.engine.state.get("backup_dir", "")
            if not bdir:
                return
            use_trash = (self.engine.state.get("delete_mode", "trash") == "trash")
            z_path = os.path.join(bdir, fname)
            if os.path.exists(z_path):
                remove_file_smart(z_path, use_trash)
            if os.path.exists(z_path + ".sha256"):
                remove_file_smart(z_path + ".sha256", use_trash)
            verify_state["status_map"].pop(fname, None)
            self.engine.log(f"Видалено пошкоджений архів: {fname}", "warn")

        def _upd_del_bad_btn():
            bdir = self.engine.state.get("backup_dir", "")
            bad_names = [fn for fn, st_i in verify_state["status_map"].items() if st_i.get("status") == "err" and os.path.exists(os.path.join(bdir, fn))]
            if bad_names:
                btn_del_bad.configure(text=tr(f"🗑 Видалити пошкоджені ({len(bad_names)})", self.engine.state.get("lang", "en")), state="normal", bg=p["red"], fg="#ffffff")
            else:
                btn_del_bad.configure(text=tr("🗑 Пошкоджених: 0", self.engine.state.get("lang", "en")), state="disabled", bg=p["card"], fg=p["muted"])

        def _verify_progress(pct, stage):
            verify_state["pct"] = pct
            verify_state["stage"] = stage

        def _poll_verify():
            if not dlg.winfo_exists():
                verify_state["stop"] = True
                return
            if verify_state["running"]:
                verify_bar["value"] = verify_state["pct"]
                verify_status.configure(text=f"{verify_state['pct']}% — {verify_state['stage']}")
                dlg.after(120, _poll_verify)
                return
            btn_verify.configure(text=tr("Перевірити SHA-256 + CRC32", self.engine.state.get("lang", "en")), state="normal")
            cb_buf.configure(state="readonly")
            if verify_state["err"]:
                verify_status.configure(text=f"Помилка перевірки: {verify_state['err']}", fg=p["red"])
            elif verify_state["res"]:
                res = verify_state["res"]
                verify_state["status_map"] = {it["name"]: it for it in res.get("items", [])}
                ok_all = (res["err_cnt"] == 0 and not res.get("cancelled"))
                perf_txt = f"Час: {res.get('elapsed', 0):.2f} с | Швидкість: {res.get('speed_mbs', 0)} МБ/с (буфер {v_buf.get()})"
                prefix = "Зупинено! " if res.get("cancelled") else ""
                msg = f"{prefix}SHA-256 + CRC32: справних {res['ok_cnt']} | без .sha256: {res['warn_cnt']} | пошкоджених: {res['err_cnt']} | {perf_txt}"
                lbl_ver.configure(text=msg, fg=p["green"] if ok_all else p["amber"])
                verify_status.configure(text=f"100% — Усі {res['total']} архівів ({res.get('total_mb', 0)} МБ) | {perf_txt}")
                verify_bar["value"] = 100
                self.engine.log(msg, "ok" if ok_all else "warn")
                _refresh()

        def _verify():
            if verify_state["running"]:
                verify_state["stop"] = True
                btn_verify.configure(text="Зупинка...", state="disabled")
                return
            verify_state.update({"running": True, "stop": False, "pct": 0, "stage": "Запуск...", "res": None, "err": None})
            btn_verify.configure(text="Зупинити")
            cb_buf.configure(state="disabled")
            chosen_buf = buf_options.get(v_buf.get(), 65536)
            lbl_ver.configure(text=f"Перевірка архівів (буфер {v_buf.get()})…", fg=p["cyan"])
            verify_bar["value"] = 0

            def _worker():
                try:
                    verify_state["res"] = verify_all_archives(self.engine.state, _verify_progress, buf_size=chosen_buf, cancel_flag=verify_state)
                except Exception as exc:
                    verify_state["err"] = str(exc)
                finally:
                    verify_state["running"] = False

            threading.Thread(target=_worker, daemon=True).start()
            dlg.after(120, _poll_verify)

        def _refresh():
            for w in list_box.winfo_children():
                w.destroy()
            all_items, keep_items, del_items = compute_gfs_plan(self.engine.state)
            tot_mb = round(sum(x["size"] for x in all_items) / 1048576.0, 1)
            del_mb = round(sum(x["size"] for x in del_items) / 1048576.0, 1)
            no_sha = sum(1 for x in all_items if not os.path.exists(x["path"] + ".sha256"))
            lbl_sum.configure(text=f"Всього: {len(all_items)} ({tot_mb} МБ) | Залишиться: {len(keep_items)} | Застарілих: {len(del_items)} ({del_mb} МБ) | Без .sha256: {no_sha}")
            _upd_del_bad_btn()
            if not all_items:
                tk.Label(list_box, text="У папці поки немає ZIP-архівів.", bg=p["log_bg"], fg=p["muted"], font=(fam, fs)).pack(pady=16)
                return
            for it in all_items:
                row = tk.Frame(list_box, bg=p["card"], bd=1, relief="solid", padx=8, pady=4)
                row.pack(fill="x", pady=2, padx=4)
                v_info = verify_state["status_map"].get(it["name"])
                is_bad = bool(v_info and v_info.get("status") == "err")
                is_keep = (it["new_tag"] != "DELETE")
                is_pin = (it["new_tag"] == "KEEP")
                if is_bad:
                    st_c, st_t = p["red"], "БИТИЙ!"
                else:
                    st_c = p["cyan"] if is_pin else (p["green"] if is_keep else p["red"])
                    st_t = "ЗАХИЩЕНО" if is_pin else ("ЗБЕРЕГТИ" if is_keep else "ВИДАЛИТИ")
                tk.Label(row, text=tr(st_t, self.engine.state.get("lang", "en")), width=10, bg=p["card"], fg=st_c, font=(fam, max(8, fs - 1), "bold")).pack(side="left")
                sz_m = round(it["size"] / 1048576.0, 1)
                det_s = f" — {v_info.get('detail', '')}" if is_bad else ""
                tk.Label(row, text=f"{it['name']}  ({sz_m} МБ){det_s}", bg=p["card"], fg=p["red"] if is_bad else p["text"], font=(fam, max(8, fs - 1))).pack(side="left", padx=6)
                if is_bad:
                    tk.Button(row, text=tr("🗑 Видалити", self.engine.state.get("lang", "en")), command=lambda n=it["name"]: (_delete_archive_pair(n), _refresh()), bg=p["red"], fg="#ffffff", font=(fam, max(8, fs - 1), "bold"), padx=8, pady=1, cursor="hand2").pack(side="right", padx=(4, 0))
                tk.Button(row, text=tr("🔒 Захист" if is_pin else "Немає захисту", self.engine.state.get("lang", "en")), width=14, command=lambda n=it["name"]: (toggle_keep_tag(self.engine.state, n), _refresh()), bg=p["cyan"] if is_pin else p["panel"], fg="#000000" if is_pin else p["muted"], font=(fam, max(8, fs - 1), "bold" if is_pin else "normal"), padx=8, pady=1, cursor="hand2").pack(side="right")

        def _clean():
            apply_gfs_cleanup(self.engine, skip_prompt=True)
            _refresh()

        def _clean_corrupted():
            bdir = self.engine.state.get("backup_dir", "")
            bad_names = [fn for fn, st_i in list(verify_state["status_map"].items()) if st_i.get("status") == "err" and os.path.exists(os.path.join(bdir, fn))]
            for fn in bad_names:
                _delete_archive_pair(fn)
            if bad_names:
                lbl_ver.configure(text=f"✓ Видалено пошкоджених архівів: {len(bad_names)} шт.", fg=p["green"])
            _refresh()

        btn_verify = tk.Button(bf, text="Перевірити SHA-256 + CRC32", command=_verify, bg=p["card"], fg=p["cyan"], font=(fam, fs, "bold"), padx=bpx, pady=bpy, cursor="hand2")
        btn_verify.pack(side="left", padx=(0, 6))
        tk.Label(bf, text="Буфер:", bg=p["panel"], fg=p["muted"], font=(fam, fs)).pack(side="left", padx=(4, 4))
        cb_buf = ttk.Combobox(bf, textvariable=v_buf, values=list(buf_options.keys()), width=7, state="readonly", font=(fam, fs))
        cb_buf.pack(side="left", padx=(0, 8))
        btn_del_bad = tk.Button(bf, text="🗑 Пошкоджених: 0", command=_clean_corrupted, state="disabled", bg=p["card"], fg=p["muted"], font=(fam, fs, "bold"), padx=bpx, pady=bpy, cursor="hand2")
        btn_del_bad.pack(side="left", padx=4)
        tk.Button(bf, text="Очистити застарілі зараз", command=_clean, bg=p["amber"], fg="#000000", font=(fam, fs, "bold"), padx=bpx, pady=bpy, cursor="hand2").pack(side="left", padx=4)
        tk.Button(bf, text="Закрити", command=dlg.destroy, bg=p["card"], fg=p["text"], font=(fam, fs), padx=bpx, pady=bpy, cursor="hand2").pack(side="right")
        _refresh()
        apply_widget_i18n(dlg, self.engine.state.get("lang", "en"))
        self._fit_dialog(dlg)

    def open_stats_modal(self):
        fs = self.metrics["font_sz"]
        dlg, p, _ = self._make_dialog("Статистика резервного копіювання", 780, 620)
        st = self.engine.get_detailed_stats() if hasattr(self.engine, "get_detailed_stats") else {}

        tk.Button(dlg, text="Закрити", command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs, "bold"), padx=int(24 * self.metrics["k"]), pady=int(6 * self.metrics["k"])).pack(side="bottom", anchor="e", padx=16, pady=(6, 12))

        tk.Label(dlg, text="Зведена аналітика за періодами та станом локального сховища:", bg=p["panel"], fg=p["muted"], font=("Segoe UI", fs)).pack(anchor="w", padx=14, pady=(10, 6))

        grid_f = tk.Frame(dlg, bg=p["panel"])
        grid_f.pack(fill="x", padx=14, pady=4)
        for c_i in range(4):
            grid_f.columnconfigure(c_i, weight=1)

        tot_c, sha_c = st.get("total_cnt", 0), st.get("sha_cnt", 0)
        sha_pct = int(round((sha_c / tot_c) * 100)) if tot_c > 0 else 100
        sha_col = p["green"] if (tot_c == 0 or sha_c == tot_c) else p["amber"]

        cards = [
            ("СЬОГОДНІ", f"{st.get('today_cnt', 0)} шт.", f"{st.get('today_mb', 0.0)} МБ", p["muted"] if st.get("today_cnt", 0) == 0 else p["cyan"], None),
            ("ЗА ТИЖДЕНЬ", f"{st.get('week_cnt', 0)} шт.", f"{st.get('week_mb', 0.0)} МБ", p["muted"] if st.get("week_cnt", 0) == 0 else p["cyan"], None),
            ("ЗА МІСЯЦЬ", f"{st.get('month_cnt', 0)} шт.", f"{st.get('month_mb', 0.0)} МБ", p["muted"] if st.get("month_cnt", 0) == 0 else p["cyan"], None),
            ("ЗА ВЕСЬ ЧАС", f"{tot_c} шт.", f"{st.get('total_mb', 0.0)} МБ", p["muted"] if tot_c == 0 else p["cyan"], None),
            ("СЕР. РОЗМІР", f"{st.get('avg_mb', 0.0)} МБ", "на один архів", p["text"], None),
            ("ЗАХИСТ SHA-256", f"{sha_c} / {tot_c} ({sha_pct}%)", "натисніть для списку" if sha_c < tot_c else "усі захищені", sha_col, "sha"),
            ("УСПІШНІСТЬ", f"{st.get('success_rate', 100)}%", "останніх запусків", p["text"], None),
            ("ГЛИБИНА", f"{st.get('span_days', 0)} дн.", "діапазон копій", p["text"], None),
        ]

        def _show_missing_sha():
            bdir = self.engine.state.get("backup_dir", "")
            miss = [f for f in os.listdir(bdir) if f.lower().endswith(".zip") and not os.path.exists(os.path.join(bdir, f + ".sha256"))] if os.path.isdir(bdir) else []
            if not miss:
                dlg.destroy()
                self.open_analyze()
                return
            miss.sort(reverse=True)
            shown = miss[:12]
            msg_m = "Архіви без файлу .sha256:\n\n• " + "\n• ".join(shown)
            if len(miss) > len(shown):
                msg_m += f"\n… та ще {len(miss) - len(shown)}"
            self._show_engine_modal({"type": "alert", "title": "Перевірка захисту SHA-256", "text": msg_m})

        for idx, (cap, v_main, v_sub, col, act) in enumerate(cards):
            r_i, c_i = divmod(idx, 4)
            is_warn_sha = (act == "sha" and sha_c < tot_c)
            c = tk.Frame(grid_f, bg=p["card"], bd=2 if is_warn_sha else 1, relief="solid", highlightbackground=p["amber"] if is_warn_sha else p["border"], highlightthickness=2 if is_warn_sha else 0, padx=9, pady=7, cursor="hand2" if act else "")
            c.grid(row=r_i, column=c_i, sticky="nsew", padx=(0 if c_i == 0 else 6, 0), pady=(0 if r_i == 0 else 6, 0))
            w1 = tk.Label(c, text=cap, bg=p["card"], fg=p["muted"], font=("Segoe UI", max(7, fs - 3), "bold"))
            w2 = tk.Label(c, text=v_main, bg=p["card"], fg=col, font=("Segoe UI", fs + 1, "bold"))
            w3 = tk.Label(c, text=v_sub, bg=p["card"], fg=p["muted"], font=("Segoe UI", max(7, fs - 2)))
            for w_it in (w1, w2, w3):
                w_it.pack(anchor="w")
                if act == "sha":
                    w_it.bind("<Button-1>", lambda _e: _show_missing_sha())
            if act == "sha":
                c.bind("<Button-1>", lambda _e: _show_missing_sha())

        mid_f = tk.Frame(dlg, bg=p["card"], bd=1, relief="solid", padx=12, pady=8)
        mid_f.pack(fill="x", padx=14, pady=(6, 6))
        gfs_txt = f"Структура GFS:   Щоденних: {st.get('gfs_daily', 0)}   •   Тижневих: {st.get('gfs_weekly', 0)}   •   Місячних: {st.get('gfs_monthly', 0)}"
        tk.Label(mid_f, text=gfs_txt, bg=p["card"], fg=p["text"], font=("Segoe UI", fs, "bold")).pack(anchor="w")

        chart_card = tk.Frame(dlg, bg=p["card"], bd=1, relief="solid", padx=12, pady=8)
        chart_card.pack(fill="both", expand=True, padx=14, pady=(4, 6))
        tk.Label(chart_card, text="ДИНАМІКА СТВОРЕННЯ АРХІВІВ ЗА ОСТАННІ 6 МІСЯЦІВ", bg=p["card"], fg=p["muted"], font=("Segoe UI", max(7, fs - 3), "bold")).pack(anchor="w", pady=(0, 6))

        cv = tk.Canvas(chart_card, height=int(120 * self.metrics["k"]), bg=p["log_bg"], highlightthickness=1, highlightbackground=p["border"])
        cv.pack(fill="both", expand=True)

        months = st.get("months", [])
        def _draw_chart(_e=None):
            cv.delete("all")
            w, h = max(240, cv.winfo_width()), max(110, cv.winfo_height())
            if not months:
                return
            max_v = max([v for _, v in months] + [1])
            k = self.metrics["k"]
            pad_x, top_y, bot_y = int(34 * k), int(32 * k), h - int(28 * k)
            slot_w = (w - pad_x * 2) / len(months)
            bar_w = min(46, max(18, slot_w * 0.52))
            cv.create_line(pad_x - 6, bot_y, w - pad_x + 6, bot_y, fill=p["border"])
            for i, (m_lbl, val) in enumerate(months):
                cx = pad_x + slot_w * (i + 0.5)
                bh = int(((bot_y - top_y) * val) / max_v) if val > 0 else 2
                y1 = bot_y - bh
                cv.create_rectangle(cx - bar_w / 2, y1, cx + bar_w / 2, bot_y, fill=p["green"] if val > 0 else p["border"], outline="")
                if val > 0:
                    cv.create_text(cx, y1 - int(12 * k), text=str(val), fill=p["text"], font=("Segoe UI", max(8, fs - 1), "bold"))
                cv.create_text(cx, bot_y + int(14 * k), text=m_lbl, fill=p["muted"], font=("Segoe UI", max(8, fs - 1)))

        cv.bind("<Configure>", _draw_chart)
        dlg.after(40, _draw_chart)
        apply_widget_i18n(dlg, self.engine.state.get("lang", "en"))
        self._fit_dialog(dlg)

    def open_ops_history(self):
        fs = self.metrics["font_sz"]
        lang = self.engine.state.get("lang", "en")
        dlg, p, _ = self._make_dialog("Журнал останніх операцій архівування", 900, 500)
        hdr_txt = "Останні 25 операцій створення резервних копій (подвійний клік по рядку — деталі):" if lang == "uk" else "Last 25 backup operations (double-click a row for details):"
        tk.Label(dlg, text=hdr_txt, bg=p["panel"], fg=p["muted"], font=("Segoe UI", fs)).pack(anchor="w", padx=14, pady=(10, 6))

        wrap = tk.Frame(dlg, bg=p["panel"])
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        style = ttk.Style()
        style.configure("HGB.Treeview", background=p["log_bg"], foreground=p["text"], fieldbackground=p["log_bg"], rowheight=max(26, int((fs + 16) * self.metrics["k"])), font=("Segoe UI", max(8, fs - 1)))
        style.configure("HGB.Treeview.Heading", background=p["card"], foreground=p["cyan"], font=("Segoe UI", max(8, fs - 1), "bold"))

        cols = ("date", "status", "file", "size", "dur", "sha")
        tree = ttk.Treeview(wrap, columns=cols, show="headings", style="HGB.Treeview")
        heads = [
            ("date", "Дата" if lang == "uk" else "Date", 150, "center"),
            ("status", "Статус" if lang == "uk" else "Status", 95, "center"),
            ("file", "Файл / Подія" if lang == "uk" else "File / Event", 330, "w"),
            ("size", "Розмір" if lang == "uk" else "Size", 90, "e"),
            ("dur", "Час" if lang == "uk" else "Duration", 78, "center"),
            ("sha", "SHA", 52, "center")
        ]
        for cid, title_h, w_col, anc in heads:
            tree.heading(cid, text=title_h)
            tree.column(cid, width=int(w_col * self.metrics["k"]), minwidth=44, anchor=anc, stretch=(cid == "file"))

        vsb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        tree.tag_configure("ok", foreground=p["green"])
        tree.tag_configure("err", foreground=p["red"])

        row_items = {}
        def _populate():
            for rid in tree.get_children():
                tree.delete(rid)
            row_items.clear()
            bdir = self.engine.state.get("backup_dir", "")
            ops = getattr(self.engine, "op_history", []) or []
            for idx_o, item in enumerate(ops):
                st_lbl = item.get("status", "")
                is_ok = (st_lbl == "Успішно")
                det = item.get("detail", "")
                dur_v = item.get("dur_sec", None)
                if " (" in det and det.endswith(")"):
                    base_part, paren_part = det.rsplit(" (", 1)
                    fname = base_part.strip()
                    p_clean = paren_part[:-1].strip()
                    if dur_v is None and (p_clean.endswith(" с") or p_clean.endswith(" s")):
                        dur_txt = p_clean
                    else:
                        dur_txt = f"{dur_v} {'с' if lang == 'uk' else 's'}" if dur_v is not None else "—"
                else:
                    fname = det
                    dur_txt = f"{dur_v} {'с' if lang == 'uk' else 's'}" if dur_v is not None else "—"

                has_sha = "✔" if (bdir and fname.endswith(".zip") and os.path.exists(os.path.join(bdir, fname + ".sha256"))) else "—"
                mb_txt = f"{item.get('size_mb', 0)} {'МБ' if lang == 'uk' else 'MB'}" if is_ok else "—"
                iid = f"op_{idx_o}"
                row_items[iid] = (item, fname, mb_txt, dur_txt, has_sha)
                tree.insert("", "end", iid=iid, values=(item.get("ts", ""), tr(st_lbl, lang), fname, mb_txt, dur_txt, has_sha), tags=("ok" if is_ok else "err",))

        def _on_double_click(_ev=None):
            sel = tree.selection()
            if not sel or sel[0] not in row_items:
                return
            item, fname, mb_txt, dur_txt, has_sha = row_items[sel[0]]
            st_tr = tr(item.get("status", ""), lang)
            if lang == "uk":
                info_msg = f"Дата та час: {item.get('ts', '')}\nСтатус: {st_tr}\nРозмір: {mb_txt}  •  Тривалість: {dur_txt}  •  SHA-256: {has_sha}\n\nДеталі / Файл:\n{fname}"
                t_dlg = "Деталі операції"
            else:
                info_msg = f"Date & Time: {item.get('ts', '')}\nStatus: {st_tr}\nSize: {mb_txt}  •  Duration: {dur_txt}  •  SHA-256: {has_sha}\n\nDetails / File:\n{fname}"
                t_dlg = "Operation Details"
            self._show_engine_modal({"type": "alert", "title": t_dlg, "text": info_msg})

        tree.bind("<Double-1>", _on_double_click)
        _populate()

        def _clear_ops():
            self.engine.op_history = []
            self.engine.state["op_history"] = []
            commit_state(self.engine.state)
            _populate()

        bf = tk.Frame(dlg, bg=p["panel"])
        bf.pack(side="bottom", fill="x", padx=14, pady=(4, 12))
        tk.Button(bf, text="🗑 Очистити журнал" if lang == "uk" else "🗑 Clear History", command=_clear_ops, bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=12, pady=5, cursor="hand2").pack(side="left")
        tk.Button(bf, text=tr("Закрити", lang), command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=5, cursor="hand2").pack(side="right")

    def open_about(self):
        from core.config import BUILD_DATE
        fs = self.metrics["font_sz"]
        k = self.metrics["k"]
        fam = "Consolas" if self.engine.state.get("lite_mode", False) else self._get_palette().get("font", "Segoe UI")
        dlg, p, _ = self._make_dialog(f"Про програму — HomeGrid Backup v{SCRIPT_VER}", 540, 290)
        info = f"""HomeGrid Backup  •  Версія v{SCRIPT_VER} (збірка від {BUILD_DATE})

• Нативне резервне копіювання даних та налаштувань інвертора без браузера.
• Перевірка цілісності архівів за CRC32 + SHA-256 та дзеркалювання.
• Автоматична GFS-ротація копій та запуск за розкладом.

Репозиторій проєкту: https://github.com"""
        tk.Label(dlg, text=info, bg=p["panel"], fg=p["text"], justify="left", wraplength=int(490 * k), font=(fam, fs)).pack(padx=18, pady=(16, 8), anchor="w", fill="x")
        tk.Button(dlg, text="Закрити", command=dlg.destroy, bg=p["green"], fg=p["green_txt"], font=(fam, fs, "bold"), padx=int(22 * k), pady=int(7 * k), cursor="hand2").pack(side="bottom", anchor="e", padx=18, pady=14)
        apply_widget_i18n(dlg, self.engine.state.get("lang", "en"))
