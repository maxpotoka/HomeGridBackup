# ==============================================================================
# [ФАЙЛ: gui/widgets.py (v2.06 | 21.11.2026 07:34) — ЕДИНЫЙ ОПТИМАЛЬНЫЙ ИНДИКАТОР ПРОГРЕССА (V8 + LITE)]
# ==============================================================================
import tkinter as tk
from gui.styles import THEMES

class StyledProgressBar(tk.Canvas):
    def __init__(self, parent, height=20, **kwargs):
        super().__init__(parent, height=height, highlightthickness=0, bd=0, **kwargs)
        self.pct = 0
        self.indet = False
        self.style_name = "v8"
        self.lite_mode = False
        self.theme = THEMES["dark"]
        self._phase = 0
        self.status_lbl = ""
        self.lang = "en"
        self.bind("<Configure>", lambda e: self.redraw())

    def set_state(self, pct, indet, style_name, lite_mode, theme, status_lbl="", lang="en"):
        self.lang = lang or "en"
        self.status_lbl = str(status_lbl or "")
        self.pct = max(0, min(100, int(pct or 0)))
        self.indet = bool(indet)
        self.style_name = "v8"
        self.lite_mode = bool(lite_mode)
        self.theme = theme
        if self.indet:
            self._phase = (self._phase + 1) % 40
        sig = (self.pct, self.indet, self._phase if self.indet else 0, self.lite_mode, id(theme), self.winfo_width(), self.winfo_height())
        if sig == getattr(self, "_last_draw_sig", None):
            return
        self._last_draw_sig = sig
        self.redraw()

    def _draw_gradient(self, x1, y1, x2, y2, c1, c2):
        w = max(1, int(x2 - x1))
        r1, g1, b1 = self.winfo_rgb(c1)
        r2, g2, b2 = self.winfo_rgb(c2)
        steps = min(w, 60)
        for i in range(steps):
            t = i / max(1, steps - 1)
            r = int((r1 + (r2 - r1) * t) / 256)
            g = int((g1 + (g2 - g1) * t) / 256)
            b = int((b1 + (b2 - b1) * t) / 256)
            sx1 = x1 + int(w * i / steps)
            sx2 = x1 + int(w * (i + 1) / steps)
            self.create_rectangle(sx1, y1, sx2, y2, fill=f"#{r:02x}{g:02x}{b:02x}", outline="")

    def redraw(self):
        self.delete("all")
        w = max(10, self.winfo_width())
        h = max(10, self.winfo_height())
        if self.lite_mode:
            self.configure(bg=self.theme["bg"])
            chars = 36
            if self.indet:
                pos = self._phase % (chars - 4)
                bar = ["-"] * chars
                for k in range(4):
                    bar[pos + k] = "#"
                from core.i18n import tr
                txt = f"[{''.join(bar)}] {tr('пошук...', self.lang)}"
            else:
                filled = int(round((self.pct / 100.0) * chars))
                txt = f"[{'#' * filled}{'-' * (chars - filled)}] {self.pct:3d}%"
            import sys as _sys_w
            _mono_f = "Menlo" if _sys_w.platform == "darwin" else ("DejaVu Sans Mono" if _sys_w.platform.startswith("linux") else "Consolas")
            self.create_text(4, h // 2, anchor="w", text=txt, fill=self.theme["cyan"], font=(_mono_f, 11, "bold"))
            return

        if self.indet:
            seg_w = max(40, int(w * 0.28))
            fx1 = int(((self._phase / 39.0) * (w + seg_w)) - seg_w)
            fx2 = fx1 + seg_w
        else:
            fx1 = 2
            fx2 = 2 + int(((w - 4) * self.pct) / 100.0)

        bg_c = self.theme.get("pbar_bg", "#1e293b")
        brd_c = self.theme.get("pbar_brd", "#475569")
        self.configure(bg=bg_c)
        self.create_rectangle(0, 0, w - 1, h - 1, outline=brd_c, width=1)
        if fx2 > fx1:
            self._draw_gradient(max(2, fx1), 2, min(w - 2, fx2), h - 2, "#2563eb", "#10b981")
