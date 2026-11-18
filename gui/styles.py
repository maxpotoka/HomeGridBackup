# ==============================================================================
# [ФАЙЛ: gui/styles.py (v1.006 | 18.11.2026 17:36) — ТЕМЫ ОФОРМЛЕНИЯ, МАСШТАБ ЭКРАНА (DPI WIN7) И TOOLTIP]
# ==============================================================================
import ctypes
from ctypes import wintypes
import tkinter as tk
from core.config import VALID_SCALES

THEME_LABELS = [
    ("crt", "1970-ті — Термінал CRT"),
    ("norton", "1980-ті — Norton Commander"),
    ("mac_classic", "1984 — Macintosh System 1"),
    ("win95", "1995 — Windows 95 / 98"),
    ("winxp", "2001 — Windows XP Luna"),
    ("mac_aqua", "2004 — macOS X Aqua"),
    ("win7", "2007 — Windows 7 Aero"),
    ("mac_light", "2014 — macOS Yosemite Light"),
    ("mac_dark", "2024 — macOS Sonoma Dark"),
    ("dark", "2026 — Темна (нічна)"),
    ("light", "2026 — Світла (денна)"),
]

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
    "mac_classic": {
        "bg": "#d8d8d8", "panel": "#ffffff", "card": "#f4f4f4", "border": "#000000",
        "text": "#000000", "muted": "#333333", "blue": "#000000", "green": "#111111",
        "amber": "#444444", "red": "#000000", "cyan": "#000000",
        "inp_bg": "#ffffff", "log_bg": "#ffffff", "btn_txt": "#ffffff", "green_txt": "#ffffff",
        "font": "Helvetica Neue", "relief": "solid"
    },
    "mac_aqua": {
        "bg": "#d6dde5", "panel": "#eef2f6", "card": "#ffffff", "border": "#9cb0c4",
        "text": "#1b2430", "muted": "#4f6075", "blue": "#1b74e4", "green": "#189b49",
        "amber": "#d97706", "red": "#d63031", "cyan": "#0984e3",
        "inp_bg": "#ffffff", "log_bg": "#f7f9fc", "btn_txt": "#ffffff", "green_txt": "#ffffff",
        "font": "Helvetica Neue", "relief": "groove"
    },
    "mac_light": {
        "bg": "#d1d1d6", "panel": "#ffffff", "card": "#f2f2f7", "border": "#8e8e93",
        "text": "#1d1d1f", "muted": "#6e6e73", "blue": "#007aff", "green": "#34c759",
        "amber": "#ff9500", "red": "#ff3b30", "cyan": "#007aff",
        "inp_bg": "#ffffff", "log_bg": "#fafafa", "btn_txt": "#ffffff", "green_txt": "#ffffff",
        "font": "Helvetica Neue", "relief": "solid"
    },
    "mac_dark": {
        "bg": "#1c1c1e", "panel": "#2c2c2e", "card": "#3a3a3c", "border": "#48484a",
        "text": "#f5f5f7", "muted": "#aeaeb2", "blue": "#0a84ff", "green": "#30d158",
        "amber": "#ff9f0a", "red": "#ff453a", "cyan": "#64d2ff",
        "inp_bg": "#161618", "log_bg": "#161618", "btn_txt": "#ffffff", "green_txt": "#042f1a",
        "font": "Helvetica Neue", "relief": "solid"
    },
    "dark": {
        "bg": "#0a0f18", "panel": "#111827", "card": "#161f33", "border": "#26324d",
        "text": "#f1f5f9", "muted": "#94a3b8", "blue": "#2b7fff", "green": "#10b981",
        "amber": "#f59e0b", "red": "#ef4444", "cyan": "#38bdf8",
        "inp_bg": "#060911", "log_bg": "#060911", "btn_txt": "#ffffff", "green_txt": "#042f2e",
        "font": "Segoe UI", "relief": "solid"
    },
    "light": {
        "bg": "#cbd5e1", "panel": "#ffffff", "card": "#f1f5f9", "border": "#94a3b8",
        "text": "#0f172a", "muted": "#475569", "blue": "#2563eb", "green": "#059669",
        "amber": "#d97706", "red": "#dc2626", "cyan": "#0284c7",
        "inp_bg": "#ffffff", "log_bg": "#f8fafc", "btn_txt": "#ffffff", "green_txt": "#ffffff",
        "font": "Segoe UI", "relief": "solid"
    },
    "norton": {
        "bg": "#000084", "panel": "#0000a8", "card": "#000084", "border": "#55ffff",
        "text": "#ffff55", "muted": "#55ffff", "blue": "#008080", "green": "#00a8a8",
        "amber": "#ffff55", "red": "#ff5555", "cyan": "#ffffff",
        "inp_bg": "#000055", "log_bg": "#000055", "btn_txt": "#ffffff", "green_txt": "#000000",
        "font": "Consolas", "relief": "solid"
    },
    "win95": {
        "bg": "#008080", "panel": "#c0c0c0", "card": "#d4d0c8", "border": "#808080",
        "text": "#000000", "muted": "#404040", "blue": "#000080", "green": "#008000",
        "amber": "#808000", "red": "#800000", "cyan": "#000080",
        "inp_bg": "#ffffff", "log_bg": "#ffffff", "btn_txt": "#ffffff", "green_txt": "#ffffff",
        "font": "Tahoma", "relief": "raised"
    },
    "winxp": {
        "bg": "#245edb", "panel": "#ece9d8", "card": "#f5f4ea", "border": "#7f9db9",
        "text": "#000000", "muted": "#4a5568", "blue": "#225ad8", "green": "#389c28",
        "amber": "#d97706", "red": "#cc2929", "cyan": "#003399",
        "inp_bg": "#ffffff", "log_bg": "#ffffff", "btn_txt": "#ffffff", "green_txt": "#ffffff",
        "font": "Tahoma", "relief": "groove"
    },
    "win7": {
        "bg": "#8faed1", "panel": "#f4f8fd", "card": "#e2ecf7", "border": "#5b7da3",
        "text": "#1e293b", "muted": "#475569", "blue": "#2874c5", "green": "#1e9e35",
        "amber": "#d97706", "red": "#c92a2a", "cyan": "#0b5cab",
        "inp_bg": "#ffffff", "log_bg": "#f8fbff", "btn_txt": "#ffffff", "green_txt": "#ffffff",
        "font": "Segoe UI", "relief": "groove"
    },
    "crt": {
        "bg": "#020a03", "panel": "#041206", "card": "#071c0a", "border": "#22c55e",
        "text": "#4ade80", "muted": "#16a34a", "blue": "#15803d", "green": "#22c55e",
        "amber": "#eab308", "red": "#ef4444", "cyan": "#86efac",
        "inp_bg": "#010602", "log_bg": "#010602", "btn_txt": "#020a03", "green_txt": "#020a03",
        "font": "Consolas", "relief": "solid"
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
        pass

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
    max_fs_by_w = 10 if ow_l < 920 else (11 if ow_l < 1150 else max(12, min(16, int(ow_l / 65))))
    font_sz = min(raw_fs, max_fs_by_w)
    k = max(k_prof, round(font_sz / 10.5, 2))
    pad_x, pad_y = max(6, int(round(11 * k * dpi_mult))), max(3, int(round(6 * k * dpi_mult)))
    btn_px, btn_py = max(6, int(round(10 * k * dpi_mult))), max(2, int(round(4 * k * dpi_mult)))
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
        self.widget = widget
        self.text = text
        self.tipwin = None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")

    def show(self, _event=None):
        if self.tipwin or not self.text:
            return
        top = self.widget.winfo_toplevel()
        cur_fs = getattr(top, "_cur_font_sz", 10)
        tip_fs = max(9, cur_fs - 1)
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() - max(34, tip_fs * 3)
        if y < 10:
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tipwin = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass
        lbl = tk.Label(
            tw, text=self.text, justify="left",
            background="#060911", foreground="#f1f5f9",
            relief="solid", borderwidth=1, padx=max(10, tip_fs), pady=max(5, tip_fs // 2),
            font=("Segoe UI", tip_fs), wraplength=max(380, tip_fs * 36)
        )
        lbl.pack()

    def hide(self, _event=None):
        if self.tipwin:
            try:
                self.tipwin.destroy()
            except Exception:
                pass
            self.tipwin = None
