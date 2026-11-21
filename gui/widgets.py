# ==============================================================================
# [ФАЙЛ: gui/widgets.py (v2.08 | 21.11.2026 18:18) — ИНДИКАТОР ПРОГРЕССА (V8 + LITE)]
# patch-id: progress-2.09
# ==============================================================================
import sys
import tkinter as tk
from gui.styles import THEMES
from core.i18n import tr

# Цвета градиента по умолчанию; тема может переопределить ключами pbar_from / pbar_to
PBAR_FROM = "#2563eb"
PBAR_TO = "#10b981"
STRIPS = 60
LITE_CHARS = 36
MONO = "Menlo" if sys.platform == "darwin" else ("DejaVu Sans Mono" if sys.platform.startswith("linux") else "Consolas")


class StyledProgressBar(tk.Canvas):
    """Полосу строит один раз; при обновлении меняются только координаты и видимость полос."""

    def __init__(self, parent, height=20, **kwargs):
        super().__init__(parent, height=height, highlightthickness=0, bd=0, **kwargs)
        self.pct = 0
        self.indet = False
        self.lite_mode = False
        self.theme = THEMES["dark"]
        self.lang = "en"
        self._phase = 0
        self._strips = []
        self._text = None
        self._cw = self._ch = 0
        self.bind("<Configure>", lambda e: self._rebuild())

    def set_state(self, pct, indet, style_name, lite_mode, theme, status_lbl="", lang="en"):
        # style_name и status_lbl оставлены для совместимости с вызовом из gui/window.py
        self.lang = lang or "en"
        self.pct = max(0, min(100, int(pct or 0)))
        self.indet = bool(indet)
        if self.indet:
            self._phase = (self._phase + 1) % 40
        lite = bool(lite_mode)
        if lite != self.lite_mode or theme != self.theme or self._cw == 0:
            self.lite_mode = lite
            self.theme = theme
            self._rebuild()
            return
        self._update()

    def _rebuild(self):
        self.delete("all")
        self._strips = []
        self._text = None
        w = max(10, self.winfo_width())
        h = max(10, self.winfo_height())
        self._cw, self._ch = w, h
        if self.lite_mode:
            self.configure(bg=self.theme["bg"])
            self._text = self.create_text(4, h // 2, anchor="w", text="", fill=self.theme["cyan"], font=(MONO, 11, "bold"))
        else:
            self.configure(bg=self.theme.get("pbar_bg", "#1e293b"))
            self.create_rectangle(0, 0, w - 1, h - 1, outline=self.theme.get("pbar_brd", "#475569"), width=1)
            c1 = self.winfo_rgb(self.theme.get("pbar_from", PBAR_FROM))
            c2 = self.winfo_rgb(self.theme.get("pbar_to", PBAR_TO))
            span = w - 4
            steps = max(1, min(span, STRIPS))
            for i in range(steps):
                t = i / max(1, steps - 1)
                r = int((c1[0] + (c2[0] - c1[0]) * t) / 256)
                g = int((c1[1] + (c2[1] - c1[1]) * t) / 256)
                b = int((c1[2] + (c2[2] - c1[2]) * t) / 256)
                x1 = 2 + span * i // steps
                x2 = 2 + span * (i + 1) // steps
                item = self.create_rectangle(x1, 2, x2, h - 2, fill=f"#{r:02x}{g:02x}{b:02x}", outline="", state="hidden")
                self._strips.append((x1, x2, item))
        self._update()

    def _update(self):
        if self.lite_mode:
            if self._text is None:
                return
            if self.indet:
                pos = self._phase % (LITE_CHARS - 4)
                bar = ["-"] * LITE_CHARS
                for k in range(4):
                    bar[pos + k] = "#"
                txt = f"[{''.join(bar)}] {tr('пошук...', self.lang)}"
            else:
                filled = int(round((self.pct / 100.0) * LITE_CHARS))
                txt = f"[{'#' * filled}{'-' * (LITE_CHARS - filled)}] {self.pct:3d}%"
            self.itemconfigure(self._text, text=txt)
            return
        w, h = self._cw, self._ch
        if self.indet:
            seg = max(40, int(w * 0.28))
            lo = int(((self._phase / 39.0) * (w + seg)) - seg)
            hi = lo + seg
        else:
            lo = 2
            hi = 2 + int(((w - 4) * self.pct) / 100.0)
        lo, hi = max(2, lo), min(w - 2, hi)
        for x1, x2, item in self._strips:
            a, b = max(x1, lo), min(x2, hi)
            if b > a:
                self.coords(item, a, 2, b, h - 2)
                self.itemconfigure(item, state="normal")
            else:
                self.itemconfigure(item, state="hidden")
