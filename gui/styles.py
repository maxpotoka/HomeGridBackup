# ==============================================================================
# [ФАЙЛ: gui/styles.py (v1.096 | 19.11.2026 21:53) — ТЕМЫ ОФОРМЛЕНИЯ, МАСШТАБ ЭКРАНА (DPI WIN7) И TOOLTIP]
# ==============================================================================
import ctypes
from ctypes import wintypes
import tkinter as tk
from core.config import VALID_SCALES

UI_SCALE_LABELS = [
    ("auto", "Авто (під монітор і DPI)"),
    ("800x600", "800 × 600 (SVGA)"),
    ("1024x600", "1024 × 600 (Нетбук)"),
    ("1024x768", "1024 × 768 (XGA)"),
    ("1280x720", "1280 × 720 (HD 720p)"),
    ("1366x768", "1366 × 768 (WXGA)"),
    ("1600x900", "1600 × 900 (HD+)"),
    ("1920x1080", "1920 × 1080 (Full HD)"),
    ("2560x1440", "2560 × 1440 (2K QHD)"),
]

UI_FONT_LABELS = [
    (0, "Авто (за розміром вікна)"),
    (8, "8 pt (Дуже дрібний)"),
    (9, "9 pt (Дрібний)"),
    (10, "10 pt (Стандартний)"),
    (11, "11 pt (Середній)"),
    (12, "12 pt (Великий)"),
    (14, "14 pt (Дуже великий)"),
    (16, "16 pt (Підвищений)"),
    (18, "18 pt (Крупний)"),
    (20, "20 pt (Дуже крупний)"),
    (22, "22 pt (Суперкрупний)"),
    (24, "24 pt (Гігантський)"),
    (26, "26 pt (Максимальний)"),
]

PBAR_STYLE_LABELS = [
    ("v8", "2026 — Неоновий кібер-градієнт (v8)"),
    ("amber_pro", "2026 — Бурштиново-жовтий градієнт"),
    ("emerald_pro", "2026 — Смарагдовий градієнт"),
    ("s_20s_macos", "2024 — macOS Sonoma (фірмовий синій)"),
    ("classic", "2015 — Сучасний плоский синій"),
    ("s_00s_win7", "2007 — Windows Vista / 7 Aero"),
    ("s_00s_aqua", "2004 — macOS X Aqua (глянцеві смуги)"),
    ("s_00s_winxp", "2001 — Windows XP Luna (зелені блоки)"),
    ("s_90s_win95", "1995 — Windows 95 / 98 Classic"),
    ("s_80s_mac1", "1984 — Macintosh System 1 (ч/б штрих)"),
    ("s_80s_dos", "1980-ті — MS-DOS / Norton Commander"),
    ("s_70s_crt", "1970-ті — Термінал мейнфрейму CRT"),
    ("s_60s_tty", "1960-ті — Телетайп / Перфострічка"),
    ("digits_only", "Цифровий лічильник (тільки відсотки)"),
]

THEMES = {
    "dark": {
        "bg": "#0a0f18", "panel": "#111827", "card": "#161f33", "border": "#26324d",
        "text": "#f1f5f9", "muted": "#94a3b8", "blue": "#2b7fff", "green": "#10b981",
        "amber": "#f59e0b", "red": "#ef4444", "cyan": "#38bdf8",
        "inp_bg": "#060911", "log_bg": "#060911", "btn_txt": "#ffffff", "green_txt": "#042f2e",
        "font": "Segoe UI", "relief": "solid"
    }
}

def _calc_screen_metrics(root, scale_pref="auto", font_pref=0, live_outer_wh=None):
    wa_x, wa_y = 0, 0
    sw, sh = root.winfo_screenwidth() or 1024, root.winfo_screenheight() or 768
    dpi = 96
    frame_w, frame_h = 16, 40
    try:
        u32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        try:
            dpi = u32.GetDpiForSystem()
        except Exception:
            hdc = u32.GetDC(0)
            if hdc:
                dpi = gdi32.GetDeviceCaps(hdc, 88) or 96
                u32.ReleaseDC(0, hdc)
        if not dpi or dpi < 72:
            dpi = 96
        rect = wintypes.RECT()
        if u32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            wa_x, wa_y = rect.left, rect.top
            sw, sh = max(640, rect.right - rect.left), max(480, rect.bottom - rect.top)
        cx_f = u32.GetSystemMetrics(32)
        cy_f = u32.GetSystemMetrics(33)
        cy_cap = u32.GetSystemMetrics(4)
        pad_b = u32.GetSystemMetrics(92)
        frame_w = max(8, (cx_f + pad_b) * 2)
        frame_h = max(28, cy_cap + (cy_f + pad_b) * 2)
    except Exception:
        try:
            px_in = float(root.winfo_fpixels("1i"))
            if 72.0 <= px_in <= 384.0:
                dpi = int(round(px_in))
        except Exception:
            dpi = 96

    dpi_mult = max(1.0, dpi / 96.0)
    try:
        root.tk.call("tk", "scaling", dpi / 72.0)
    except Exception:
        pass
    sc = scale_pref if scale_pref in VALID_SCALES else "auto"

    if live_outer_wh is not None:
        lw, lh = live_outer_wh
        outer_w = max(640, int(lw))
        outer_h = max(480, int(lh))
        scale_ratio = ((outer_w / dpi_mult) / 1200.0 + (outer_h / dpi_mult) / 720.0) / 2.0
        k_prof = round(max(0.80, min(1.60, scale_ratio)), 2)
        base_fs = max(9, min(16, int(round(10.0 * k_prof))))
        raw_fs = base_fs
    else:
        if sc != "auto" and "x" in sc:
            rw_s, rh_s = sc.split("x", 1)
            outer_w = min(sw, int(rw_s))
            outer_h = min(sh, int(rh_s))
        else:
            outer_w, outer_h = sw, sh
        k_prof = round(max(0.80, min(1.60, (outer_w / dpi_mult) / 1280.0)), 2)
        base_fs = max(9, min(16, int(round(10.0 * k_prof))))
        raw_fs = int(font_pref) if (isinstance(font_pref, int) and 8 <= font_pref <= 28) else base_fs

    win_w = max(620, outer_w - frame_w)
    win_h = max(440, outer_h - frame_h)
    ow_l = outer_w / dpi_mult
    oh_l = outer_h / dpi_mult
    max_fs_by_w = 8 if ow_l < 860 else (9 if ow_l < 1060 else (10 if ow_l < 1260 else max(11, min(15, int(ow_l / 80)))))
    max_fs_by_h = 8 if oh_l < 620 else (9 if oh_l < 720 else max(10, min(15, int(oh_l / 52))))
    safe_cap = max(8, min(max_fs_by_w, max_fs_by_h))
    font_sz = max(8, min(raw_fs, safe_cap))
    k = round(max(0.76, min(1.45, font_sz / 10.5)), 2)
    pad_x, pad_y = max(5, int(round(9 * k))), max(2, int(round(4 * k)))
    btn_px, btn_py = max(5, int(round(8 * k))), max(1, int(round(3 * k)))
    pos_x = wa_x + max(0, (sw - outer_w) // 2)
    pos_y = wa_y + max(0, (sh - outer_h) // 2)
    return {
        "wa_x": wa_x, "wa_y": wa_y, "sw": sw, "sh": sh,
        "outer_w": outer_w, "outer_h": outer_h,
        "win_w": win_w, "win_h": win_h, "pos_x": pos_x, "pos_y": pos_y,
        "scale_code": sc, "font_sz": font_sz, "k": k,
        "pad_x": pad_x, "pad_y": pad_y, "btn_px": btn_px, "btn_py": btn_py
    }

class ToolTip:
    def __init__(self, widget, text):
        if getattr(widget, "_has_tooltip", False):
            return
        widget._has_tooltip = True
        self.widget = widget
        self.text = text
        self.tipwin = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")

    def _schedule(self, _event=None):
        if self.tipwin or self._after_id or not self.text:
            return
        self._after_id = self.widget.after(240, self.show)

    def _on_leave(self, _event=None):
        try:
            px, py = self.widget.winfo_pointerxy()
            wx, wy = self.widget.winfo_rootx(), self.widget.winfo_rooty()
            ww, wh = self.widget.winfo_width(), self.widget.winfo_height()
            if wx <= px <= wx + ww and wy <= py <= wy + wh:
                return
        except Exception:
            pass
        self.hide()

    def show(self, _event=None):
        self._after_id = None
        if self.tipwin or not self.text:
            return
        try:
            px, py = self.widget.winfo_pointerxy()
            wx, wy = self.widget.winfo_rootx(), self.widget.winfo_rooty()
            ww, wh = self.widget.winfo_width(), self.widget.winfo_height()
            if not (wx - 2 <= px <= wx + ww + 2 and wy - 2 <= py <= wy + wh + 2):
                return
        except Exception:
            wx, wy, ww, wh = self.widget.winfo_rootx(), self.widget.winfo_rooty(), self.widget.winfo_width(), self.widget.winfo_height()

        top = self.widget.winfo_toplevel()
        cur_fs = getattr(top, "_cur_font_sz", 10)
        tip_fs = max(9, cur_fs - 1)
        from core.i18n import tr
        tip_txt = tr(self.text, getattr(top, "_cur_lang", "en"))

        self.tipwin = tw = tk.Toplevel(self.widget)
        tw.withdraw()
        tw.wm_overrideredirect(True)
        lbl = tk.Label(
            tw, text=tip_txt, justify="left",
            background="#060911", foreground="#f1f5f9",
            relief="solid", borderwidth=1, padx=max(10, tip_fs), pady=max(5, tip_fs // 2),
            font=("Segoe UI", tip_fs), wraplength=max(360, tip_fs * 34)
        )
        lbl.pack()
        tw.update_idletasks()
        tw_w, tw_h = tw.winfo_reqwidth(), tw.winfo_reqheight()
        sw, sh = top.winfo_screenwidth() or 1280, top.winfo_screenheight() or 720
        x = max(8, min(wx + 8, sw - tw_w - 8))
        y = wy - tw_h - 8
        if y < 8:
            y = min(sh - tw_h - 8, wy + wh + 8)
        tw.wm_geometry(f"+{x}+{y}")
        try:
            tw.transient(top)
            tw.lift()
            tw.attributes("-topmost", True)
        except Exception:
            pass
        tw.deiconify()

    def hide(self, _event=None):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self.tipwin:
            try:
                self.tipwin.destroy()
            except Exception:
                pass
            self.tipwin = None
