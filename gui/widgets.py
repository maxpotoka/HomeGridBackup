# ==============================================================================
# [ФАЙЛ: gui/widgets.py (v1.006 | 18.11.2026 17:36) — КАСТОМНЫЙ ИНДИКАТОР ПРОГРЕССА (12 СТИЛЕЙ + LITE)]
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
        self.bind("<Configure>", lambda e: self.redraw())

    def set_state(self, pct, indet, style_name, lite_mode, theme):
        self.pct = max(0, min(100, int(pct or 0)))
        self.indet = bool(indet)
        self.style_name = style_name or "v8"
        self.lite_mode = bool(lite_mode)
        self.theme = theme
        if self.indet:
            self._phase = (self._phase + 1) % 40
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
        st = self.style_name

        if self.lite_mode:
            self.configure(bg=self.theme["bg"])
            chars = 36
            if self.indet:
                pos = self._phase % (chars - 4)
                bar = ["-"] * chars
                for k in range(4):
                    bar[pos + k] = "#"
                txt = f"[{''.join(bar)}] пошук..."
            else:
                filled = int(round((self.pct / 100.0) * chars))
                txt = f"[{'#' * filled}{'-' * (chars - filled)}] {self.pct:3d}%"
            self.create_text(4, h // 2, anchor="w", text=txt, fill=self.theme["cyan"], font=("Consolas", 11, "bold"))
            return

        if st == "digits_only":
            self.configure(bg=self.theme["panel"])
            lbl = "[  ...  ]" if self.indet else f"[  {self.pct:3d}%  ]"
            self.create_rectangle(2, 1, 110, h - 1, fill=self.theme["inp_bg"], outline=self.theme["border"])
            self.create_text(56, h // 2, text=lbl, fill=self.theme["cyan"], font=("Consolas", 11, "bold"))
            return

        if self.indet:
            seg_w = max(40, int(w * 0.28))
            fx1 = int(((self._phase / 39.0) * (w + seg_w)) - seg_w)
            fx2 = fx1 + seg_w
        else:
            fx1 = 2
            fx2 = 2 + int(((w - 4) * self.pct) / 100.0)

        if st in ("v8", "amber_pro", "emerald_pro"):
            bg_c = "#050811" if st == "v8" else ("#141005" if st == "amber_pro" else "#03140e")
            brd_c = "#334155" if st == "v8" else ("#d97706" if st == "amber_pro" else "#10b981")
            c1, c2 = ("#2563eb", "#10b981") if st == "v8" else (("#d97706", "#facc15") if st == "amber_pro" else ("#059669", "#6ee7b7"))
            self.configure(bg=bg_c)
            self.create_rectangle(0, 0, w - 1, h - 1, outline=brd_c)
            if fx2 > fx1:
                self._draw_gradient(max(2, fx1), 2, min(w - 2, fx2), h - 2, c1, c2)
        elif st == "s_20s_macos":
            self.configure(bg="#e5e5ea")
            self.create_rectangle(0, 0, w - 1, h - 1, outline="#c7c7cc")
            if fx2 > fx1:
                self._draw_gradient(max(2, fx1), 2, min(w - 2, fx2), h - 2, "#007aff", "#5ac8fa")
        elif st == "s_80s_mac1":
            self.configure(bg="#ffffff")
            self.create_rectangle(0, 0, w - 1, h - 1, outline="#000000", width=2)
            if fx2 > fx1:
                x_a, x_b = max(2, fx1), min(w - 2, fx2)
                self.create_rectangle(x_a, 2, x_b, h - 2, fill="#000000", outline="")
                for sx in range(x_a, x_b, 4):
                    self.create_line(sx, 2, sx, h - 2, fill="#ffffff", width=1)
        elif st == "classic":
            self.configure(bg=self.theme["inp_bg"])
            self.create_rectangle(0, 0, w - 1, h - 1, outline=self.theme["border"])
            if fx2 > fx1:
                self.create_rectangle(max(2, fx1), 2, min(w - 2, fx2), h - 2, fill="#3b82f6", outline="")
        elif st == "s_00s_win7":
            self.configure(bg="#e4e4e4")
            self.create_rectangle(0, 0, w - 1, h - 1, outline="#8e8f8f")
            if fx2 > fx1:
                x_a, x_b = max(2, fx1), min(w - 2, fx2)
                mid = h // 2
                self.create_rectangle(x_a, 2, x_b, mid, fill="#8bf098", outline="")
                self.create_rectangle(x_a, mid, x_b, h - 2, fill="#07b51f", outline="")
        elif st == "s_00s_aqua":
            self.configure(bg="#cbd5e1")
            self.create_rectangle(0, 0, w - 1, h - 1, outline="#64748b")
            if fx2 > fx1:
                x_a, x_b = max(2, fx1), min(w - 2, fx2)
                self.create_rectangle(x_a, 2, x_b, h - 2, fill="#3b82f6", outline="")
                for sx in range(x_a - h, x_b, 16):
                    self.create_line(sx, h - 2, sx + h, 2, fill="#93c5fd", width=5)
        elif st == "s_00s_winxp":
            self.configure(bg="#ffffff")
            self.create_rectangle(0, 0, w - 1, h - 1, outline="#686868")
            for bx in range(max(3, fx1), min(w - 3, fx2), 12):
                self.create_rectangle(bx, 3, min(bx + 9, min(w - 3, fx2)), h - 3, fill="#28d228", outline="")
        elif st == "s_90s_win95":
            self.configure(bg="#c0c0c0")
            self.create_line(0, 0, w - 1, 0, fill="#808080")
            self.create_line(0, 0, 0, h - 1, fill="#808080")
            self.create_line(0, h - 1, w - 1, h - 1, fill="#ffffff")
            self.create_line(w - 1, 0, w - 1, h - 1, fill="#ffffff")
            for bx in range(max(3, fx1), min(w - 3, fx2), 14):
                self.create_rectangle(bx, 3, min(bx + 11, min(w - 3, fx2)), h - 3, fill="#000080", outline="")
        elif st == "s_80s_dos":
            self.configure(bg="#000084")
            self.create_rectangle(0, 0, w - 1, h - 1, outline="#55ffff", width=2)
            for bx in range(max(4, fx1), min(w - 4, fx2), 14):
                self.create_rectangle(bx, 4, min(bx + 11, min(w - 4, fx2)), h - 4, fill="#55ffff", outline="")
        elif st == "s_70s_crt":
            self.configure(bg="#020d04")
            self.create_rectangle(0, 0, w - 1, h - 1, outline="#22c55e", width=2)
            for bx in range(max(4, fx1), min(w - 4, fx2), 13):
                self.create_rectangle(bx, 4, min(bx + 10, min(w - 4, fx2)), h - 4, fill="#22c55e", outline="")
        elif st == "s_60s_tty":
            self.configure(bg="#1c1915")
            self.create_rectangle(0, 0, w - 1, h - 1, outline="#a8a29e", dash=(4, 2))
            for bx in range(max(4, fx1), min(w - 4, fx2), 9):
                self.create_rectangle(bx, 4, min(bx + 5, min(w - 4, fx2)), h - 4, fill="#e7e5e4", outline="")
