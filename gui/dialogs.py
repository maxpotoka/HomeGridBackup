import re
import os
import time
from core.i18n import tr, apply_widget_i18n
# ==============================================================================
# patch-id: io-pause-buf128-2.18
# patch-id: stage-window-2.21
# [ФАЙЛ: gui/dialogs.py (v2.09 | 22.11.2026 09:10)
# patch-id: fix-i18n-dialogs-2.11 — МОДАЛЬНЫЕ ДИАЛОГИ, НАСТРОЙКИ, АНАЛИЗ GFS И О ПРОГРАММЕ]
# ==============================================================================
import tkinter as tk
from tkinter import ttk
from core.config import SCRIPT_VER, commit_state
from core.files import format_duration
from core.gfs import compute_gfs_plan, toggle_keep_tag, apply_gfs_cleanup
from core.backup import verify_all_archives
from core.scheduler import _build_run_cmd, _sync_scheduler_from_windows, _manage_windows_scheduler
from gui.styles import UI_SCALE_LABELS, UI_FONT_LABELS, THEMES, fix_mac_buttons
from gui.tray import _force_quit_app

class _EmbeddedDialog(tk.Frame):
    def __init__(self, root, palette, title_txt, w, h, on_close_cb):
        self._root = root
        self._on_close_cb = on_close_cb
        self._del_protocol = None
        super().__init__(root, bg=palette["panel"], bd=2, relief="solid", highlightbackground=palette["blue"], highlightthickness=2)
        hdr = tk.Frame(self, bg=palette["card"], padx=10, pady=6)
        hdr.pack(side="top", fill="x")
        import sys as _s; _fam = "Ubuntu" if _s.platform.startswith("linux") else "Segoe UI"; self._lbl_t = tk.Label(hdr, text=title_txt, bg=palette["card"], fg=palette["text"], font=(_fam, 10, "bold"))
        self._lbl_t.pack(side="left")
        tk.Button(hdr, text="✖", command=self._handle_wm_delete, bg=palette["card"], fg=palette["red"], bd=0, padx=6, cursor="hand2").pack(side="right")
        self.place(relx=0.5, rely=0.5, anchor="center", width=w, height=h)
        self.lift()

    def _handle_wm_delete(self):
        if callable(self._del_protocol):
            self._del_protocol()
        else:
            self.destroy()

    def title(self, txt=None):
        if txt is not None:
            self._lbl_t.configure(text=txt)
        return self._lbl_t.cget("text")

    def protocol(self, name, func=None):
        if name == "WM_DELETE_WINDOW":
            self._del_protocol = func

    def transient(self, *_a): pass
    def grab_set(self): pass
    def deiconify(self): pass
    def withdraw(self): pass
    def geometry(self, *_a): pass
    def maxsize(self, *_a): return (1920, 1080)
    def minsize(self, *_a): pass
    def destroy(self):
        if callable(self._on_close_cb):
            self._on_close_cb()
        super().destroy()

class DialogsMixin:
    def _ui_fam(self):
        if hasattr(self, '_base_fam') and self._base_fam:
            return self._base_fam
        import sys as _sf
        return 'Helvetica Neue' if _sf.platform == 'darwin' else ('Ubuntu' if _sf.platform.startswith('linux') else 'Segoe UI')

    def _calc_parent_center(self, parent_win, w_box, h_box):
        m = self.metrics
        try:
            pw, ph = parent_win.winfo_width(), parent_win.winfo_height()
            if pw > 120 and ph > 120:
                cx = parent_win.winfo_rootx() + (pw - w_box) // 2
                cy = parent_win.winfo_rooty() + (ph - h_box) // 2
                x = max(6, min(cx, m["sw"] - w_box - 6))
                y = max(6, min(cy, m["sh"] - h_box - 30))
                return x, y
        except Exception:
            pass
        return m["wa_x"] + max(0, (m["sw"] - w_box) // 2), m["wa_y"] + max(0, (m["sh"] - h_box) // 2)

    def _finalize_dialog(self, dlg):
        import sys
        try:
            if not dlg.winfo_exists():
                return
            dlg.update_idletasks()
            m = self.metrics
            req_w, req_h = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
            cur_w, cur_h = getattr(dlg, "_init_wh", (req_w, req_h))
            if getattr(dlg, "_fit_flag", False):
                w_box = min(max(cur_w, req_w), max(360, m["sw"] - 20))
                h_box = min(max(cur_h, req_h), max(180, m["sh"] - 60))
                mx_w, mx_h = dlg.maxsize()
                dlg.maxsize(max(w_box, mx_w), max(h_box, mx_h))
                dlg.minsize(min(w_box, req_w), min(h_box, req_h))
            else:
                w_box, h_box = max(360, cur_w, req_w), max(160, cur_h, req_h)
            p_ref = getattr(dlg, "_parent_ref", self.root)
            x, y = self._calc_parent_center(p_ref, w_box, h_box)
            if not sys.platform.startswith("linux"):
                dlg.geometry(f"{w_box}x{h_box}+{x}+{y}")
                dlg.transient(p_ref)
                dlg.deiconify()
                dlg.grab_set()
            else:
                rw = max(420, self.root.winfo_width() - 24)
                rh = max(220, self.root.winfo_height() - 24)
                dlg.place_configure(width=min(max(w_box, req_w + 16), rw), height=min(max(h_box, req_h + 16), rh))
            fix_mac_buttons(dlg, self._get_palette())
            if not sys.platform.startswith("linux"):
                dlg.focus_force()
        except Exception:
            pass

    def _make_dialog(self, title, w=640, h=420, scrollable=False, min_outer_w=0, min_outer_h=0):
        import sys
        if not hasattr(self, "_open_dialogs"):
            self._open_dialogs = {}
        dlg_key = str(title).split("—")[0].strip()
        prev_dlg = self._open_dialogs.get(dlg_key)
        if prev_dlg is not None:
            try:
                if prev_dlg.winfo_exists():
                    prev_dlg.destroy()
            except Exception:
                pass
        p = self._get_palette()
        m = self.metrics
        k = m["k"]
        fw = m.get("outer_w", m["win_w"]) - m["win_w"]
        fh = m.get("outer_h", m["win_h"]) - m["win_h"]
        dlg_w = max(360, min(m.get("outer_w", m["sw"]), max(min_outer_w, int(round(w * k)))) - fw)
        dlg_h = max(160, min(m.get("outer_h", m["sh"]), max(min_outer_h, int(round(h * k)))) - fh)
        self._ignore_resize_until = time.time() + 0.7
        parent_win = self.root if sys.platform.startswith("linux") else (self.root.grab_current() or self.root)
        px, py = self._calc_parent_center(parent_win, dlg_w, dlg_h)
        if sys.platform.startswith("linux"):
            for _k_old, _d_old in list(self._open_dialogs.items()):
                try:
                    if _d_old.winfo_exists():
                        _d_old.destroy()
                except Exception:
                    pass
            self._open_dialogs.clear()
            rw = max(560, self.root.winfo_width() - 24)
            rh = max(380, self.root.winfo_height() - 24)
            ew, eh = min(dlg_w, rw), min(dlg_h, rh)
            dlg = _EmbeddedDialog(self.root, p, tr(title, self.engine.state.get("lang", "en")), ew, eh, lambda: self._open_dialogs.pop(dlg_key, None))
            self._open_dialogs[dlg_key] = dlg
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
            return dlg, p, inner
        self.root.option_add("*Toplevel.background", p["panel"])
        dlg = tk.Toplevel(self.root, bg=p["panel"])
        if not sys.platform.startswith("linux"):
            dlg.withdraw()
        self._open_dialogs[dlg_key] = dlg
        def _on_dlg_destroy(e):
            if e.widget is dlg:
                self._open_dialogs.pop(dlg_key, None)
                self._ignore_resize_until = time.time() + 0.7
                try:
                    self.root.focus_set()
                except Exception:
                    pass
        dlg.bind('<Destroy>', _on_dlg_destroy)
        dlg.title(tr(title, self.engine.state.get("lang", "en")))
        dlg.configure(bg=p["panel"])
        dlg._parent_ref = parent_win
        dlg._init_wh = (dlg_w, dlg_h)
        dlg._fit_flag = False
        dlg.geometry(f"{dlg_w}x{dlg_h}+{px}+{py}")
        dlg.maxsize(min(m["sw"], int(round(max(w, 760) * k * 1.15))), min(m["sh"], int(round(max(h, 520) * k * 1.15))))
        dlg.after_idle(lambda: self._finalize_dialog(dlg))
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
        dlg.bind("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units"))
        return dlg, p, inner

    def _fit_dialog(self, dlg):
        dlg._fit_flag = True
    def confirm_exit(self):
        import sys
        fs = max(10, self.metrics["font_sz"])
        fam = "Ubuntu" if sys.platform.startswith("linux") else "Segoe UI"
        lang = self.engine.state.get("lang", "en")
        dlg, p, _ = self._make_dialog(tr("Підтвердження виходу", lang), 520, 225)
        bf = tk.Frame(dlg, bg=p["panel"])
        bf.pack(side="bottom", fill="x", padx=16, pady=(6, 14))
        tk.Label(dlg, text=tr("Ви дійсно бажаєте завершити роботу HomeGrid Backup та закрити програму?", lang), bg=p["panel"], fg=p["text"], wraplength=int(460 * self.metrics["k"]), font=(fam, fs)).pack(pady=(18, 10), padx=18, expand=True)
        tk.Button(bf, text=tr("Скасувати", lang), command=dlg.destroy, bg=p["card"], fg=p["text"], font=(fam, fs), padx=16, pady=6, cursor="hand2").pack(side="right", padx=6)
        def _do_exit(_e=None):
            self._exit_confirm_open = False
            try:
                dlg.destroy()
            except Exception:
                pass
            _force_quit_app(self.engine)
        def _cancel_exit(_e=None):
            self._exit_confirm_open = False
            try:
                dlg.destroy()
            except Exception:
                pass
        dlg.protocol("WM_DELETE_WINDOW", _cancel_exit)
        dlg.bind("<Escape>", _cancel_exit)
        dlg.bind("<Return>", _do_exit)
        tk.Button(bf, text=tr("Так, вийти", lang), command=_do_exit, bg=p["red"], fg="#ffffff", font=(fam, fs, "bold"), padx=16, pady=6, cursor="hand2").pack(side="right", padx=6)
        apply_widget_i18n(dlg, self.engine.state.get("lang", "en"))
        self._fit_dialog(dlg)

    def _show_engine_modal(self, m):
        import json as _js
        fs = self.metrics["font_sz"]
        lang = self.engine.state.get("lang", "en")
        if m["type"] == "backup_report":
            d = _js.loads(m["text"]) if isinstance(m.get("text"), str) else {}
            fam = "Consolas" if self.engine.state.get("lite_mode", False) else self._get_palette().get("font", "Segoe UI")
            dlg, p, _ = self._make_dialog("Резервне копіювання успішно завершено" if lang == "uk" else "Backup Completed Successfully", 740, 650, min_outer_w=700, min_outer_h=600)
            def _close_rep(_e=None):
                try:
                    dlg.destroy()
                except Exception:
                    pass
                self.engine.submit_modal(True)
            dlg.protocol("WM_DELETE_WINDOW", _close_rep)
            tot_s = max(0.1, float(d.get("total_sec", 0.1)))
            tot_disp = format_duration(tot_s, lang)
            fn_s = d.get("file", "backup.zip")
            sz_s = d.get("size_mb", 0.0)
            fc_s = d.get("files_cnt", 0)
            ts_a = d.get("ts_start", "—")
            ts_b = d.get("ts_end", "—")
            spd_s = d.get("spd_mbs", 0.0)
            top_c = tk.Frame(dlg, bg=p["card"], bd=1, relief="solid", padx=14, pady=10)
            top_c.pack(fill="x", padx=16, pady=(12, 8))
            import ipaddress as _ipa
            from urllib.parse import urlparse as _up
            srv_raw = str(d.get("srv") or self.engine.state.get("server", "")).strip()
            _h = (_up(srv_raw).hostname or srv_raw) if srv_raw else ""
            try:
                _is_lan = _ipa.ip_address(_h).is_private or _ipa.ip_address(_h).is_loopback
            except Exception:
                _is_lan = _h.endswith(".local") or _h in ("localhost",)
            net_tag = ("Локальна мережа / LAN" if _is_lan else "Інтернет / Зовнішній") if lang == "uk" else ("Local Network / LAN" if _is_lan else "Internet / External")
            srv_disp = f"{srv_raw}  [{net_tag}]" if srv_raw else "—"
            tk.Label(top_c, text=(f"Файл архіву:  {fn_s}" if lang == "uk" else f"Archive file:  {fn_s}"), bg=p["card"], fg=p["cyan"], font=(fam, fs, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
            tk.Label(top_c, text=(f"Джерело (сервер):  {srv_disp}" if lang == "uk" else f"Source server:  {srv_disp}"), bg=p["card"], fg=p["green"] if _is_lan else p["amber"], font=(fam, fs, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
            tk.Label(top_c, text=(f"Розмір:  {sz_s} МБ ({fc_s} файлів)   •   CRC32 + SHA-256: Підтверджено" if lang == "uk" else f"Size:  {sz_s} MB ({fc_s} files)   •   CRC32 + SHA-256: Verified"), bg=p["card"], fg=p["text"], font=(fam, fs), anchor="w").pack(fill="x", pady=(0, 6))
            tk.Label(top_c, text=(f"Час запуску:  {ts_a}   →   Завершено:  {ts_b}   (Разом: {tot_disp})" if lang == "uk" else f"Started at:  {ts_a}   →   Finished:  {ts_b}   (Total: {tot_disp})"), bg=p["card"], fg=p["green"], font=(fam, fs, "bold"), anchor="w").pack(fill="x")
            mid_c = tk.Frame(dlg, bg=p["card"], bd=1, relief="solid", padx=14, pady=10)
            mid_c.pack(fill="x", padx=16, pady=(0, 8))
            mid_c.columnconfigure(0, weight=1)
            raw_stages = [
                ("Підготовка та аналіз на сервері:" if lang == "uk" else "Server preparation & scan:", d.get("srv_prep_sec", 0.0), p["text"]),
                ("Збір та копіювання даних на сервері:" if lang == "uk" else "Server data collection & copy:", d.get("srv_copy_sec", 0.0), p["text"]),
                ("Стиснення та пакування ZIP на сервері:" if lang == "uk" else "Server ZIP archive packing:", d.get("srv_pack_sec", d.get("srv_sec", 0.0)), p["text"]),
                ("Перевірка файлів на сервері:" if lang == "uk" else "Server file verification:", d.get("srv_chk_sec", 0.0), p["text"]),
                ("Обробка на сервері:" if lang == "uk" else "Processing on server:", d.get("srv_proc_sec", 0.0), p["text"]),
                (f"Скачування по мережі ({spd_s} {'МБ/с' if lang == 'uk' else 'MB/s'}):" if lang == "uk" else f"Network download ({spd_s} MB/s):", d.get("dl_sec", 0.0), p["cyan"]),
                ("Перевірка архіву CRC32 (програма):" if lang == "uk" else "Local CRC32 integrity check:", d.get("crc_sec", d.get("ver_sec", 0.0)), p["text"]),
                ("Розрахунок та звірка SHA-256:" if lang == "uk" else "Local SHA-256 hash verification:", d.get("sha_sec", 0.0), p["text"]),
            ]
            if d.get("mir_active"):
                raw_stages.append(("Дзеркальне копіювання:" if lang == "uk" else "Mirror folder copy:", d.get("mir_sec", 0.0), p["green"]))
            stages = [(f"{i}. {t}", v, c) for i, (t, v, c) in enumerate(raw_stages, 1)]
            for idx_r, (lbl_st, val_s, col_st) in enumerate(stages):
                pct_v = min(100, int(round((float(val_s) / tot_s) * 100)))
                tk.Label(mid_c, text=lbl_st, bg=p["card"], fg=col_st, font=(fam, fs), anchor="w").grid(row=idx_r, column=0, sticky="w", pady=4)
                tk.Label(mid_c, text=f"{format_duration(val_s, lang)}  ({pct_v}%)", bg=p["card"], fg=col_st, font=(fam, fs, "bold"), anchor="e").grid(row=idx_r, column=1, sticky="e", padx=(12, 0), pady=4)
            bot_c = tk.Frame(dlg, bg=p["card"], bd=1, relief="solid", padx=14, pady=8)
            bot_c.pack(fill="x", padx=16, pady=(0, 8))
            tk.Label(bot_c, text=(f"Сховище:  {d.get('z_cnt', 0)} архівів ({d.get('z_mb', 0)} МБ)   •   Вільно:  {d.get('free_gb', 0)} ГБ   •   Застарілих GFS:  {d.get('old_cnt', 0)} шт." if lang == "uk" else f"Storage:  {d.get('z_cnt', 0)} archives ({d.get('z_mb', 0)} MB)   •   Free:  {d.get('free_gb', 0)} GB   •   Outdated GFS:  {d.get('old_cnt', 0)}"), bg=p["card"], fg=p["muted"], font=(fam, fs), anchor="w").pack(fill="x")
            bf = tk.Frame(dlg, bg=p["panel"])
            bf.pack(side="bottom", fill="x", padx=16, pady=(4, 12))
            btn_ok_r = tk.Button(bf, text="ОК" if lang == "uk" else "OK", command=_close_rep, bg=p["green"], fg=p["green_txt"], font=(fam, fs, "bold"), padx=24, pady=5, cursor="hand2")
            btn_ok_r.pack(side="right")
            dlg.after(350, lambda: (dlg.bind("<Return>", _close_rep), dlg.bind("<Escape>", _close_rep), btn_ok_r.focus_set()) if dlg.winfo_exists() else None)
            self._fit_dialog(dlg)
            return
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

        v_keep_n = tk.IntVar(value=st.get("keep_last_count", 5))
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
        v_cloud_enabled = tk.BooleanVar(value=bool(st.get("cloud_enabled", False)))
        v_cloud_remote = tk.StringVar(value=st.get("cloud_remote", ""))
        v_cloud_path = tk.StringVar(value=st.get("cloud_path", "HomeGridBackup"))

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
        tab_cloud = tk.Frame(nb, bg=p["panel"])
        nb.add(tab_bkp, text="  Резервне копіювання та Розклад  ")
        nb.add(tab_ui, text="  Вигляд та Інтерфейс  ")
        nb.add(tab_cloud, text="  Хмара та звіт  ")

        f_cloud = tk.LabelFrame(
            tab_cloud, text=" 5. Хмарне дзеркало та звіт операцій ",
            bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"),
            padx=14, pady=10
        )
        f_cloud.pack(fill="x", padx=14, pady=12)
        tk.Checkbutton(
            f_cloud, text="Увімкнути хмарне дзеркало та звіт",
            variable=v_cloud_enabled, bg=p["card"], fg=p["text"],
            selectcolor=p["inp_bg"], font=("Segoe UI", fs)
        ).pack(anchor="w", pady=(2, 8))

        cloud_remote_row = tk.Frame(f_cloud, bg=p["card"])
        cloud_remote_row.pack(fill="x", pady=4)
        tk.Label(
            cloud_remote_row, text="rclone remote:", width=18, anchor="w",
            bg=p["card"], fg=p["text"], font=("Segoe UI", fs)
        ).pack(side="left")
        cb_cloud_remote = ttk.Combobox(
            cloud_remote_row, textvariable=v_cloud_remote, state="readonly",
            font=("Segoe UI", fs)
        )
        cb_cloud_remote.pack(side="left", fill="x", expand=True, padx=(0, 8))
        cloud_msg = tk.Label(f_cloud, text="", bg=p["card"], fg=p["muted"], font=("Segoe UI", fs - 1))
        cloud_msg.pack(anchor="w", pady=(2, 4))

        cloud_path_row = tk.Frame(f_cloud, bg=p["card"])
        cloud_path_row.pack(fill="x", pady=4)
        tk.Label(
            cloud_path_row, text="Папка у хмарі:", width=18, anchor="w",
            bg=p["card"], fg=p["text"], font=("Segoe UI", fs)
        ).pack(side="left")
        tk.Entry(
            cloud_path_row, textvariable=v_cloud_path, bg=p["inp_bg"],
            fg=p["text"], insertbackground=p["text"], font=("Segoe UI", fs)
        ).pack(side="left", fill="x", expand=True)
        tk.Label(
            f_cloud,
            text="Архіви та журнали розділяються за випадковим ID пристрою. "
                 "Хмарні ZIP-копії повторюють GFS після очищення; журнали мають секундні часові мітки.",
            bg=p["card"], fg=p["muted"], justify="left", wraplength=780,
            font=("Segoe UI", max(8, fs - 1))
        ).pack(anchor="w", pady=(8, 4))
        tk.Label(
            f_cloud, text=f"ID пристрою: {st.get('device_id', '')}",
            bg=p["card"], fg=p["muted"], font=("Consolas", max(8, fs - 1))
        ).pack(anchor="w", pady=(2, 6))

        def _refresh_cloud_remotes():
            import threading
            cloud_msg.configure(text=tr("Завантаження списку rclone remotes...", st.get("lang", "en")), fg=p["muted"])

            def _worker():
                try:
                    from core.cloud import list_rclone_remotes
                    remotes = list_rclone_remotes()
                    error = ""
                except Exception as exc:
                    remotes = []
                    error = str(exc)

                def _update():
                    if not dlg.winfo_exists():
                        return
                    current = v_cloud_remote.get()
                    values = list(remotes)
                    if current and current not in values:
                        values.append(current)
                    cb_cloud_remote.configure(values=values)
                    if current:
                        v_cloud_remote.set(current)
                    if error:
                        cloud_msg.configure(text=error, fg=p["red"])
                    elif remotes:
                        cloud_msg.configure(text=tr("rclone remotes завантажено.", st.get("lang", "en")), fg=p["green"])
                    else:
                        cloud_msg.configure(text=tr("Налаштованих rclone remotes не знайдено.", st.get("lang", "en")), fg=p["amber"])

                try:
                    self.root.after(0, _update)
                except Exception:
                    pass

            threading.Thread(target=_worker, daemon=True).start()

        tk.Button(
            cloud_remote_row, text="Оновити список",
            command=_refresh_cloud_remotes, bg=p["card"], fg=p["cyan"],
            font=("Segoe UI", fs), padx=10, pady=4, cursor="hand2"
        ).pack(side="right")
        tk.Label(
            f_cloud, text="Спочатку встановіть rclone та налаштуйте провайдера командою: rclone config",
            bg=p["card"], fg=p["muted"], font=("Segoe UI", max(8, fs - 1))
        ).pack(anchor="w", pady=(4, 2))
        _refresh_cloud_remotes()

        top_grid = tk.Frame(tab_bkp, bg=p["panel"])
        top_grid.pack(fill="x", padx=12, pady=(6, 2))
        top_grid.columnconfigure(0, weight=1)
        top_grid.columnconfigure(1, weight=1)

        f_gfs = tk.LabelFrame(top_grid, text=" 1. Кільцева стратегія (останні N архівів) ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"), padx=12, pady=8)
        f_gfs.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=2)
        tk.Label(f_gfs, text="Зберігати останніх архівів (шт.):", bg=p["card"], fg=p["text"], font=("Segoe UI", fs), anchor="w").grid(row=0, column=0, sticky="w", pady=6)
        tk.Spinbox(f_gfs, from_=1, to=50, textvariable=v_keep_n, width=5, bg=p["inp_bg"], fg=p["text"], font=("Segoe UI", fs, "bold")).grid(row=0, column=1, sticky="w", padx=(8, 0), pady=6)
        tk.Checkbutton(f_gfs, text="У Кошик (замість видалення)", variable=v_trash, bg=p["card"], fg=p["cyan"], selectcolor=p["inp_bg"], font=("Segoe UI", fs)).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        f_del = tk.LabelFrame(top_grid, text=" 2. Трей та тихий режим ", bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold"), padx=12, pady=6)
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

        from core.config import IS_WINDOWS as _IS_WIN_S, IS_WSL as _IS_WSL_S, IS_MAC as _IS_MAC_S
        if _IS_WIN_S:
            sr2 = tk.Frame(f_sch, bg=p["card"])
            sr2.pack(fill="x", pady=3)
            tk.Label(sr2, text="Пріоритет (2-9):", bg=p["card"], fg=p["text"], font=(self._ui_fam(), fs_sch)).pack(side="left")
            tk.Spinbox(sr2, from_=2, to=9, textvariable=v_sprio, width=4, bg=p["inp_bg"], fg=p["text"], font=(self._ui_fam(), fs_sch)).pack(side="left", padx=6)
            tk.Checkbutton(sr2, text="Запускати пропущене", variable=v_smissed, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=(self._ui_fam(), fs_sch)).pack(side="left", padx=12)
            tk.Checkbutton(sr2, text="Розбудити ПК зі сну", variable=v_swake, bg=p["card"], fg=p["text"], selectcolor=p["inp_bg"], font=(self._ui_fam(), fs_sch)).pack(side="left", padx=12)
        else:
            lng_n = st.get("lang", "en")
            os_note = (
                ("WSL: розклад реєструється у Планувальнику Windows (schtasks.exe)." if lng_n == "uk" else "WSL: schedule uses Windows Task Scheduler (schtasks.exe).")
                if _IS_WSL_S else (
                    ("macOS: розклад працює через системний агент LaunchAgent." if lng_n == "uk" else "macOS: schedule runs via native LaunchAgent.")
                    if _IS_MAC_S else
                    ("Linux: розклад працює через crontab та ~/.config/autostart." if lng_n == "uk" else "Linux: schedule runs via crontab & ~/.config/autostart.")
                )
            )
            tk.Label(f_sch, text=os_note, bg=p["card"], fg=p["muted"], font=(self._ui_fam(), max(8, fs - 1))).pack(anchor="w", pady=(2, 3))

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
            cmd = _build_run_cmd(flag)
            self.root.clipboard_clear()
            self.root.clipboard_append(cmd)
            lbl_sch_msg.configure(text=tr(f"✓ Скопійовано у буфер: {cmd}", st.get("lang", "en")), fg=p["cyan"])

        def _export_cfg():
            import json as _j
            from tkinter import filedialog
            fp = filedialog.asksaveasfilename(defaultextension=".json", initialfile="homegrid_backup_settings.json", filetypes=[("JSON", "*.json")])
            if not fp: return
            skip_k = {"client_token", "session_token", "login_pin", "editor_pin", "_jar", "dirty", "storage_backend", "device_id"}
            data = {k: v for k, v in st.items() if k not in skip_k}
            with open(fp, "w", encoding="utf-8") as fo:
                _j.dump(data, fo, indent=2, ensure_ascii=False)
            lbl_sch_msg.configure(text=tr("✓ Налаштування експортовано у JSON", st.get("lang", "en")), fg=p["green"])

        def _import_cfg():
            import json as _j
            from tkinter import filedialog
            fp = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
            if not fp: return
            with open(fp, "r", encoding="utf-8") as fi:
                data = _j.load(fi)
            skip_k = {"client_token", "session_token", "login_pin", "editor_pin", "_jar", "dirty", "storage_backend", "device_id"}
            for k, v in data.items():
                if k in st and k not in skip_k:
                    st[k] = v
            commit_state(st)
            self.var_srv.set(st.get("server", ""))
            self.var_dir.set(st.get("backup_dir", ""))
            self.apply_theme_and_mode(resize_win=True)
            dlg.destroy()
            self.open_settings()

        tk.Button(sr3, text="Додати в Планувальник", command=_create_task, bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=12, pady=4, cursor="hand2").pack(side="left", padx=(0, 10))
        tk.Button(sr3, text="Видалити задачу", command=_del_task, bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=12, pady=4, cursor="hand2").pack(side="left", padx=6)
        def _open_adv_sched():
            lng_m = st.get("lang", "en")
            m_adv = tk.Menu(dlg, tearoff=0, bg=p["panel"], fg=p["text"], font=("Segoe UI", fs))
            m_adv.add_command(label=tr("Копіювати команду фонового запуску", lng_m), command=lambda: _copy_cmd("--hidden"))
            m_adv.add_command(label=tr("Копіювати команду консольного запуску", lng_m), command=lambda: _copy_cmd("--silent"))
            m_adv.add_separator()
            m_adv.add_command(label=tr("Експорт налаштувань (JSON)...", lng_m), command=_export_cfg)
            m_adv.add_command(label=tr("Імпорт налаштувань (JSON)...", lng_m), command=_import_cfg)
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
        lng_t = st.get("lang", "en")
        thm_map = {tr("Темна тема", lng_t): "dark", tr("Світла тема", lng_t): "light"}
        rev_thm = {"dark": tr("Темна тема", lng_t), "light": tr("Світла тема", lng_t)}
        cb_theme = ttk.Combobox(t_r1, values=list(thm_map.keys()), state="readonly", font=("Segoe UI", fs))
        cb_theme.set(rev_thm.get(v_theme.get(), tr("Темна тема", lng_t)))
        cb_theme.pack(side="left", fill="x", expand=True)


        t_r2 = tk.Frame(f_thm, bg=p["card"])
        t_r2.pack(fill="x", pady=4)
        tk.Label(t_r2, text="Роздільна здатність:", width=20, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        lng_cur = st.get("lang", "en")
        scale_map = {tr(lbl, lng_cur): code for code, lbl in UI_SCALE_LABELS}
        rev_scale = {code: tr(lbl, lng_cur) for code, lbl in UI_SCALE_LABELS}
        cb_scale = ttk.Combobox(t_r2, values=[tr(lbl, lng_cur) for _, lbl in UI_SCALE_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_scale.set(rev_scale.get(v_scale.get(), tr(UI_SCALE_LABELS[0][1], lng_cur)))
        cb_scale.pack(side="left", fill="x", expand=True)

        t_r3 = tk.Frame(f_thm, bg=p["card"])
        t_r3.pack(fill="x", pady=4)
        tk.Label(t_r3, text="Розмір шрифту:", width=20, anchor="w", bg=p["card"], fg=p["text"], font=("Segoe UI", fs)).pack(side="left")
        font_map = {tr(lbl, lng_cur): code for code, lbl in UI_FONT_LABELS}
        rev_font = {code: tr(lbl, lng_cur) for code, lbl in UI_FONT_LABELS}
        cb_font = ttk.Combobox(t_r3, values=[tr(lbl, lng_cur) for _, lbl in UI_FONT_LABELS], state="readonly", font=("Segoe UI", fs))
        cb_font.set(rev_font.get(v_font.get(), tr(UI_FONT_LABELS[0][1], lng_cur)))
        cb_font.pack(side="left", fill="x", expand=True)


        def _commit_settings(close_after):
            cloud_remote = v_cloud_remote.get().strip()
            cloud_path = v_cloud_path.get().strip() or "HomeGridBackup"
            if v_cloud_enabled.get():
                try:
                    from core.cloud import validate_cloud_settings
                    cloud_path = validate_cloud_settings(cloud_remote, cloud_path)
                except ValueError as exc:
                    cloud_msg.configure(text=str(exc), fg=p["red"])
                    nb.select(tab_cloud)
                    return
            st["keep_last_count"] = max(1, int(v_keep_n.get()))
            st["daily_days"] = max(1, int(v_daily.get()))
            st["today_max"] = max(1, int(v_today.get()))
            st["weekly_count"] = max(0, int(v_week.get()))
            st["monthly_count"] = max(0, int(v_month.get()))
            st["yearly_count"] = max(0, int(v_year.get()))
            st["lang"] = lang_map.get(cb_lang.get(), "en")
            st["theme"] = thm_map.get(cb_theme.get(), "dark")
            st["delete_mode"] = "trash" if v_trash.get() else "direct"
            st["minimize_to_tray"] = bool(v_tray_min.get())
            st["silent_cleanup"] = bool(v_sclean.get())
            st["cloud_enabled"] = bool(v_cloud_enabled.get())
            st["cloud_remote"] = cloud_remote
            st["cloud_path"] = cloud_path
            old_sc = st.get("ui_scale", "auto")
            new_sc = scale_map.get(cb_scale.get(), "auto")
            st["ui_scale"] = new_sc
            st["ui_font"] = font_map.get(cb_font.get(), 0)
            st["progress_style"] = "v8"
            commit_state(st)
            self.apply_theme_and_mode(resize_win=(new_sc != old_sc))
            self.engine.log("Налаштування програми, теми, шрифту та стратегії GFS застосовано.", "ok")
            dlg.destroy()
            if not close_after:
                self.open_settings()

        tk.Button(bf, text="Скинути PIN", command=lambda: (self.reset_pins(), lbl_sch_msg.configure(text="✓ Збережені PIN-коди очищено", fg=p["amber"])), bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=12, pady=6, cursor="hand2").pack(side="left", padx=(6, 6), pady=6)
        tk.Button(bf, text="Експорт JSON", command=_export_cfg, bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs), padx=12, pady=6, cursor="hand2").pack(side="left", padx=4, pady=6)
        tk.Button(bf, text="Імпорт JSON", command=_import_cfg, bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs), padx=12, pady=6, cursor="hand2").pack(side="left", padx=4, pady=6)
        tk.Button(bf, text="Скасувати", command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=6, cursor="hand2").pack(side="right", padx=(6, 6), pady=6)
        tk.Button(bf, text="Зберегти та закрити", command=lambda: _commit_settings(True), bg=p["green"], fg=p["green_txt"], font=("Segoe UI", fs, "bold"), padx=14, pady=6, cursor="hand2").pack(side="right", padx=6, pady=6)
        tk.Button(bf, text="Застосувати", command=lambda: _commit_settings(False), bg=p["blue"], fg="#ffffff", font=("Segoe UI", fs, "bold"), padx=14, pady=6, cursor="hand2").pack(side="right", padx=6, pady=6)
        def _i18n_settings():
            lng = st.get("lang", "en")
            nb.tab(0, text="  " + tr("Резервне копіювання та Розклад", lng) + "  ")
            nb.tab(1, text="  " + tr("Вигляд та Інтерфейс", lng) + "  ")
            nb.tab(2, text="  " + tr("Хмара та звіт", lng) + "  ")
            apply_widget_i18n(dlg, lng)
        _i18n_settings()

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
        _v_st = ttk.Style()
        try:
            _v_st.theme_use("clam")
        except Exception:
            pass
        _v_st.configure("HGB.Horizontal.TProgressbar", troughcolor=p["log_bg"], background=p["green"], bordercolor=p["border"], lightcolor=p["green"], darkcolor=p["green"])
        verify_bar = ttk.Progressbar(dlg, mode="determinate", maximum=100, style="HGB.Horizontal.TProgressbar")
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
        _lng_a = self.engine.state.get("lang", "en")
        buf_options = {tr(k, _lng_a): v for k, v in (("4 КБ", 4096), ("16 КБ", 16384), ("128 КБ", 131072), ("256 КБ", 262144), ("1 МБ", 1048576), ("4 МБ", 4194304), ("8 МБ", 8388608))}
        v_buf = tk.StringVar(value=tr("128 КБ", _lng_a))
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
                _st_tr = tr(verify_state["stage"], self.engine.state.get("lang", "en"))
                verify_status.configure(text=f"{verify_state['pct']}% — {_st_tr}", fg=p["cyan"])
                dlg.after(120, _poll_verify)
                return
            btn_verify.configure(text=tr("Перевірити SHA-256 + CRC32", self.engine.state.get("lang", "en")), state="normal")
            cb_buf.configure(state="readonly")
            lng_v = self.engine.state.get("lang", "en")
            if verify_state["err"]:
                verify_status.configure(text=tr(f"Помилка перевірки: {verify_state['err']}", lng_v), fg=p["red"])
            elif verify_state["res"]:
                res = verify_state["res"]
                verify_state["status_map"] = {it["name"]: it for it in res.get("items", [])}
                ok_all = (res["err_cnt"] == 0 and not res.get("cancelled"))
                perf_txt = f"Час: {res.get('elapsed', 0):.2f} с | Швидкість: {res.get('speed_mbs', 0)} МБ/с (буфер {v_buf.get()})"
                prefix = "Зупинено! " if res.get("cancelled") else ""
                msg = tr(f"{prefix}SHA-256 + CRC32: справних {res['ok_cnt']} | без .sha256: {res['warn_cnt']} | пошкоджених: {res['err_cnt']} | {perf_txt}", lng_v)
                lbl_ver.configure(text=msg, fg=p["green"] if ok_all else p["amber"])
                verify_status.configure(text=tr(f"100% — Усі {res['total']} архівів ({res.get('total_mb', 0)} МБ) | {perf_txt}", lng_v))
                verify_bar["value"] = 100
                self.engine.log(msg, "ok" if ok_all else "warn")
                _refresh()

        def _verify():
            lng_v = self.engine.state.get("lang", "en")
            if verify_state["running"]:
                verify_state["stop"] = True
                btn_verify.configure(text=tr("Зупинка...", lng_v), state="disabled")
                return
            verify_state.update({"running": True, "stop": False, "pct": 0, "stage": tr("Запуск...", lng_v), "res": None, "err": None})
            btn_verify.configure(text=tr("Зупинити", lng_v))
            cb_buf.configure(state="disabled")
            chosen_buf = buf_options.get(v_buf.get(), 131072)
            lbl_ver.configure(text=tr(f"Перевірка архівів (буфер {v_buf.get()})…", lng_v), fg=p["cyan"])
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
            lng_r = self.engine.state.get("lang", "en")
            for w in list_box.winfo_children():
                w.destroy()
            all_items, keep_items, del_items = compute_gfs_plan(self.engine.state)
            tot_mb = round(sum(x["size"] for x in all_items) / 1048576.0, 1)
            del_mb = round(sum(x["size"] for x in del_items) / 1048576.0, 1)
            no_sha = sum(1 for x in all_items if not os.path.exists(x["path"] + ".sha256"))
            lbl_sum.configure(text=tr(f"Всього: {len(all_items)} ({tot_mb} МБ) | Залишиться: {len(keep_items)} | Застарілих: {len(del_items)} ({del_mb} МБ) | Без .sha256: {no_sha}", lng_r))
            _upd_del_bad_btn()
            if "btn_clean_exp" in locals():
                btn_clean_exp.configure(
                    state="normal" if del_items else "disabled",
                    bg=p["amber"] if del_items else p["card"],
                    fg=p["btn_txt"] if del_items else p["muted"],
                    disabledforeground=p["muted"],
                )
            if not all_items:
                tk.Label(list_box, text=tr("У папці поки немає ZIP-архівів.", lng_r), bg=p["log_bg"], fg=p["muted"], font=(fam, fs)).pack(pady=16)
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
                row.columnconfigure(1, weight=1)
                tk.Label(row, text=tr(st_t, lng_r), width=10, bg=p["card"], fg=st_c, font=(fam, max(8, fs - 1), "bold")).grid(row=0, column=0, sticky="w")
                sz_m = round(it["size"] / 1048576.0, 1)
                det_s = f" — {tr(v_info.get('detail', ''), lng_r)}" if is_bad else ""
                disp_n = it["name"] if len(it["name"]) <= 46 else (it["name"][:43] + "...")
                tk.Label(row, text=tr(f"{disp_n}  ({sz_m} МБ){det_s}", lng_r), anchor="w", bg=p["card"], fg=p["red"] if is_bad else p["text"], font=(fam, max(8, fs - 1))).grid(row=0, column=1, sticky="ew", padx=6)
                def _ask_del_arc(n=it['name']):
                    lng_d = self.engine.state.get('lang', 'en')
                    t_c = 'Видалення архіву' if lng_d == 'uk' else 'Delete Archive'
                    q_c = f'Видалити архів та .sha256?\n\n{n}' if lng_d == 'uk' else f'Delete archive and .sha256?\n\n{n}'
                    cdlg, cp, _ = self._make_dialog(t_c, 500, 210)
                    cbf = tk.Frame(cdlg, bg=cp['panel'])
                    cbf.pack(side='bottom', fill='x', padx=14, pady=10)
                    tk.Label(cdlg, text=q_c, bg=cp['panel'], fg=cp['text'], wraplength=450, font=(fam, fs)).pack(pady=(16, 8), padx=16, expand=True)
                    tk.Button(cbf, text=tr('Скасувати', lng_d), command=cdlg.destroy, bg=cp['card'], fg=cp['text'], font=(fam, fs), padx=12, pady=4).pack(side='right', padx=6)
                    tk.Button(cbf, text=tr('Видалити', lng_d), command=lambda: (cdlg.destroy(), _delete_archive_pair(n), _refresh()), bg=cp['red'], fg='#ffffff', font=(fam, fs, 'bold'), padx=12, pady=4).pack(side='right', padx=6)
                    self._fit_dialog(cdlg)
                tk.Button(row, text=tr("🔒 Захист" if is_pin else "Немає захисту", lng_r), width=15, command=lambda n=it["name"]: (toggle_keep_tag(self.engine.state, n), _refresh()), bg=p["blue"] if is_pin else p["panel"], fg=p["btn_txt"] if is_pin else p["muted"], activebackground=p["border"], activeforeground=p["text"], font=(fam, max(8, fs - 1), "bold" if is_pin else "normal"), padx=8, pady=1, cursor="hand2").grid(row=0, column=2, sticky="e")
                tk.Button(row, text="✖", width=3, command=_ask_del_arc, bg=p['red'] if is_bad else p['panel'], fg=p['btn_txt'] if is_bad else p['red'], activebackground=p['red'], activeforeground='#ffffff', font=(fam, max(8, fs - 1), 'bold'), padx=4, pady=1, cursor='hand2').grid(row=0, column=3, sticky='e', padx=(6, 0))

        def _clean():
            apply_gfs_cleanup(self.engine, skip_prompt=True)
            _refresh()

        def _clean_corrupted():
            bdir = self.engine.state.get("backup_dir", "")
            bad_names = [fn for fn, st_i in list(verify_state["status_map"].items()) if st_i.get("status") == "err" and os.path.exists(os.path.join(bdir, fn))]
            for fn in bad_names:
                _delete_archive_pair(fn)
            if bad_names:
                lbl_ver.configure(text=tr(f"✓ Видалено пошкоджених архівів: {len(bad_names)} шт.", self.engine.state.get("lang", "en")), fg=p["green"])
            _refresh()

        btn_verify = tk.Button(bf, text="Перевірити SHA-256 + CRC32", command=_verify, bg=p["card"], fg=p["cyan"], font=(fam, fs, "bold"), padx=bpx, pady=bpy, cursor="hand2")
        btn_verify.pack(side="left", padx=(0, 6))
        tk.Label(bf, text="Буфер:", bg=p["panel"], fg=p["muted"], font=(fam, fs)).pack(side="left", padx=(4, 4))
        cb_buf = ttk.Combobox(bf, textvariable=v_buf, values=list(buf_options.keys()), width=7, state="readonly", font=(fam, fs))
        cb_buf.pack(side="left", padx=(0, 8))
        btn_del_bad = tk.Button(bf, text="🗑 Пошкоджених: 0", command=_clean_corrupted, state="disabled", bg=p["card"], fg=p["muted"], font=(fam, fs, "bold"), padx=bpx, pady=bpy, cursor="hand2")
        btn_del_bad.pack(side="left", padx=4)
        btn_clean_exp = tk.Button(bf, text="Очистити застарілі зараз", command=_clean, bg=p["amber"], fg=p["btn_txt"], disabledforeground=p["muted"], font=(fam, fs, "bold"), padx=bpx, pady=bpy, cursor="hand2")
        btn_clean_exp.pack(side="left", padx=4)
        tk.Button(bf, text="Закрити", command=dlg.destroy, bg=p["card"], fg=p["text"], font=(fam, fs), padx=bpx, pady=bpy, cursor="hand2").pack(side="right")
        _refresh()
        apply_widget_i18n(dlg, self.engine.state.get("lang", "en"))
        self._fit_dialog(dlg)

    def open_stats_modal(self):
        fs = self.metrics["font_sz"]
        lng_c = self.engine.state.get("lang", "en")
        dlg, p, _ = self._make_dialog("Статистика резервного копіювання", 780, 620)
        st = self.engine.get_detailed_stats() if hasattr(self.engine, "get_detailed_stats") else {}

        tk.Button(dlg, text=tr("Закрити", lng_c), command=dlg.destroy, bg=p["card"], fg=p["text"], font=(self._ui_fam(), fs, "bold"), padx=int(24 * self.metrics["k"]), pady=int(6 * self.metrics["k"])).pack(side="bottom", anchor="e", padx=16, pady=(6, 12))

        tk.Label(dlg, text=tr("Зведена аналітика за періодами та станом локального сховища:", lng_c), bg=p["panel"], fg=p["muted"], font=(self._ui_fam(), fs)).pack(anchor="w", padx=14, pady=(10, 6))

        grid_f = tk.Frame(dlg, bg=p["panel"])
        grid_f.pack(fill="x", padx=14, pady=4)
        for c_i in range(4):
            grid_f.columnconfigure(c_i, weight=1)

        tot_c = st.get("total_cnt", 0)
        disk_c = st.get("disk_cnt", tot_c)
        sha_c = st.get("sha_cnt", 0)
        sha_pct = int(round((sha_c / disk_c) * 100)) if disk_c > 0 else 100
        sha_col = p["green"] if (disk_c == 0 or sha_c == disk_c) else p["amber"]

        lng_c = self.engine.state.get("lang", "en")
        span_d = st.get("span_days", 0)
        depth_val = tr("1 день", lng_c) if span_d == 1 else tr(f"{span_d} дн.", lng_c)
        sha_sub = tr("натисніть для списку", lng_c) if sha_c < disk_c else (tr("усі захищені", lng_c) if disk_c > 0 else tr("папка порожня", lng_c))
        cards = [
            (tr("СЬОГОДНІ", lng_c), tr(f"{st.get('today_cnt', 0)} шт.", lng_c), tr(f"{st.get('today_mb', 0.0)} МБ", lng_c), p["muted"] if st.get("today_cnt", 0) == 0 else p["cyan"], None),
            (tr("ЗА ТИЖДЕНЬ", lng_c), tr(f"{st.get('week_cnt', 0)} шт.", lng_c), tr(f"{st.get('week_mb', 0.0)} МБ", lng_c), p["muted"] if st.get("week_cnt", 0) == 0 else p["cyan"], None),
            (tr("ЗА МІСЯЦЬ", lng_c), tr(f"{st.get('month_cnt', 0)} шт.", lng_c), tr(f"{st.get('month_mb', 0.0)} МБ", lng_c), p["muted"] if st.get("month_cnt", 0) == 0 else p["cyan"], None),
            (tr("ЗА ВЕСЬ ЧАС", lng_c), tr(f"{tot_c} шт.", lng_c), tr(f"{st.get('total_mb', 0.0)} МБ", lng_c), p["muted"] if tot_c == 0 else p["cyan"], None),
            (tr("СЕР. РОЗМІР", lng_c), tr(f"{st.get('avg_mb', 0.0)} МБ", lng_c), tr("на один архів", lng_c), p["text"], None),
            (tr("ЗАХИСТ SHA-256", lng_c), f"{sha_c} / {disk_c} ({sha_pct}%)", sha_sub, sha_col, "sha"),
            (tr("УСПІШНІСТЬ", lng_c), f"{st.get('success_rate', 100)}%", tr("останніх запусків", lng_c), p["text"], None),
            (tr("ГЛИБИНА", lng_c), depth_val, tr("діапазон копій", lng_c), p["text"], None),
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
            msg_m = tr("Архіви без файлу .sha256:", lng_c) + "\n\n• " + "\n• ".join(shown)
            if len(miss) > len(shown):
                msg_m += "\n" + (f"… та ще {len(miss) - len(shown)} шт." if lng_c == "uk" else f"… and {len(miss) - len(shown)} more")
            self._show_engine_modal({"type": "alert", "title": tr("Перевірка захисту SHA-256", lng_c), "text": msg_m})

        for idx, (cap, v_main, v_sub, col, act) in enumerate(cards):
            r_i, c_i = divmod(idx, 4)
            is_warn_sha = (act == "sha" and sha_c < disk_c)
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

        lng_s = self.engine.state.get("lang", "en")
        avg_t_s = (format_duration(st.get("avg_dur_sec", 0.0), lng_s) if float(st.get("avg_dur_sec") or 0) > 0 else "—")
        tot_t_s = (format_duration(st.get("total_dur_sec", 0.0), lng_s) if float(st.get("total_dur_sec") or 0) > 0 else "—")
        mid_f = tk.Frame(dlg, bg=p["card"], bd=1, relief="solid", padx=12, pady=8)
        mid_f.pack(fill="x", padx=14, pady=(6, 6))
        wt_txt = (
            f"Час роботи:   Середній: {avg_t_s}   •   Загальний ({st.get('dur_cnt', 0)} оп.): {tot_t_s}"
            if lng_s == "uk" else
            f"Work time:   Average: {avg_t_s}   •   Total ({st.get('dur_cnt', 0)} runs): {tot_t_s}"
        )
        tk.Label(mid_f, text=wt_txt, bg=p["card"], fg=p["cyan"], font=("Segoe UI", fs, "bold")).pack(anchor="w")

        chart_card = tk.Frame(dlg, bg=p["card"], bd=1, relief="solid", padx=12, pady=8)
        chart_card.pack(fill="both", expand=True, padx=14, pady=(4, 6))
        tk.Label(chart_card, text=tr("ДИНАМІКА СТВОРЕННЯ АРХІВІВ ЗА ОСТАННІ 6 МІСЯЦІВ", lng_c), bg=p["card"], fg=p["muted"], font=(self._ui_fam(), max(7, fs - 3), "bold")).pack(anchor="w", pady=(0, 6))

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
                cv.create_text(cx, bot_y + int(14 * k), text=tr(m_lbl, lng_c), fill=p["muted"], font=(self._ui_fam(), max(8, fs - 1)))

        cv.bind("<Configure>", _draw_chart)
        dlg.after(40, _draw_chart)
        apply_widget_i18n(dlg, self.engine.state.get("lang", "en"))
        self._fit_dialog(dlg)

    def open_ops_history(self):
        fs = self.metrics["font_sz"]
        lang = self.engine.state.get("lang", "en")
        dlg, p, _ = self._make_dialog("Журнал останніх операцій архівування", 940, 540)
        hdr_txt = "Останні 25 операцій створення резервних копій (подвійний клік по рядку — деталі):" if lang == "uk" else "Last 25 backup operations (double-click a row for details):"
        tk.Label(dlg, text=hdr_txt, bg=p["panel"], fg=p["muted"], font=("Segoe UI", fs)).pack(anchor="w", padx=14, pady=(10, 6))

        bf = tk.Frame(dlg, bg=p["panel"])
        bf.pack(side="bottom", fill="x", padx=14, pady=(6, 12))

        wrap = tk.Frame(dlg, bg=p["panel"])
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.map("HGB.Treeview", background=[("selected", p["blue"])], foreground=[("selected", "#ffffff")])
        style.map("HGB.Treeview.Heading", background=[("active", p["panel"])])
        style.configure("HGB.Treeview", background=p["log_bg"], foreground=p["text"], fieldbackground=p["log_bg"], rowheight=max(26, int((fs + 16) * self.metrics["k"])), font=("Segoe UI", max(8, fs - 1)))
        style.configure("HGB.Treeview.Heading", background=p["card"], foreground=p["cyan"], font=("Segoe UI", max(8, fs - 1), "bold"))

        cols = ("date", "status", "file", "size", "dur", "sha")
        tree = ttk.Treeview(wrap, columns=cols, show="headings", style="HGB.Treeview")
        heads = [
            ("date", "Дата" if lang == "uk" else "Date", 174, "center"),
            ("status", "Статус" if lang == "uk" else "Status", 98, "center"),
            ("file", "Файл / Подія" if lang == "uk" else "File / Event", 350, "w"),
            ("size", "Розмір" if lang == "uk" else "Size", 94, "e"),
            ("dur", "Час" if lang == "uk" else "Duration", 98, "center"),
            ("sha", "SHA", 54, "center")
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
                        dur_txt = format_duration(dur_v, lang) if dur_v is not None else "—"
                else:
                    fname = det
                    dur_txt = format_duration(dur_v, lang) if dur_v is not None else "—"

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


        tk.Button(bf, text="🗑 Очистити журнал" if lang == "uk" else "🗑 Clear History", command=_clear_ops, bg=p["card"], fg=p["red"], font=("Segoe UI", fs), padx=12, pady=5, cursor="hand2").pack(side="left")
        tk.Button(bf, text=tr("Закрити", lang), command=dlg.destroy, bg=p["card"], fg=p["text"], font=("Segoe UI", fs), padx=14, pady=5, cursor="hand2").pack(side="right")

    def open_about(self):
        import webbrowser
        from core.config import BUILD_DATE
        fs = self.metrics["font_sz"]
        k = self.metrics["k"]
        lang = self.engine.state.get("lang", "en")
        fam = "Consolas" if self.engine.state.get("lite_mode", False) else self._get_palette().get("font", "Segoe UI")
        dlg, p, _ = self._make_dialog(f"{tr('Про програму', lang)} — HomeGrid Backup v{SCRIPT_VER}", 560, 320)
        if lang == "uk":
            info = (
                f"HomeGrid Backup  •  Версія v{SCRIPT_VER} (збірка від {BUILD_DATE})\n\n"
                "• Нативне резервне копіювання даних та налаштувань інвертора без браузера.\n"
                "• Перевірка цілісності архівів за CRC32 + SHA-256 та дзеркалювання.\n"
                "• Автоматична GFS-ротація копій та запуск за розкладом."
            )
            repo_lbl = "Репозиторій проєкту:"
        else:
            info = (
                f"HomeGrid Backup  •  Version v{SCRIPT_VER} (build {BUILD_DATE})\n\n"
                "• Native backup of inverter data and settings without a browser.\n"
                "• Archive integrity verification via CRC32 + SHA-256 and mirroring.\n"
                "• Automatic GFS backup rotation and scheduled execution."
            )
            repo_lbl = "Project repository:"
        tk.Label(dlg, text=info, bg=p["panel"], fg=p["text"], justify="left", wraplength=int(510 * k), font=(fam, fs)).pack(padx=18, pady=(16, 8), anchor="w", fill="x")
        rf = tk.Frame(dlg, bg=p["panel"])
        rf.pack(fill="x", padx=18, pady=(0, 8))
        tk.Label(rf, text=repo_lbl, bg=p["panel"], fg=p["muted"], font=(fam, fs)).pack(side="left")
        lnk = tk.Label(rf, text="https://github.com", bg=p["panel"], fg=p["cyan"], font=(fam, fs, "underline"), cursor="hand2")
        lnk.pack(side="left", padx=(6, 0))
        lnk.bind("<Button-1>", lambda _e: webbrowser.open("https://github.com"))
        dlg.bind("<Escape>", lambda _e: dlg.destroy())
        dlg.bind("<Return>", lambda _e: dlg.destroy())
        tk.Button(dlg, text=tr("Закрити", lang), command=dlg.destroy, bg=p["green"], fg=p["green_txt"], font=(fam, fs, "bold"), padx=int(22 * k), pady=int(7 * k), cursor="hand2").pack(side="bottom", anchor="e", padx=18, pady=14)
        self._fit_dialog(dlg)
