# ==============================================================================
# patch-id: tall-pbar-server-marquee-2.70
# patch-id: force-tall-pbar-and-grid-2.74
# [ФАЙЛ: gui/widgets.py (v2.10 | 24.11.2026 02:15) — ИНДИКАТОР ПРОГРЕССА (V8 + LITE)]
# patch-id: progress-2.09
# ==============================================================================
import sys
import tkinter as tk

from core.i18n import tr
from gui.styles import THEMES

# Цвета градиента по умолчанию; тема может переопределить ключами pbar_from / pbar_to
PBAR_FROM = "#2563eb"
PBAR_TO = "#10b981"
STRIPS = 60
LITE_CHARS = 36
MONO = "Menlo" if sys.platform == "darwin" else ("DejaVu Sans Mono" if sys.platform.startswith("linux") else "Consolas")


# patch-id: homegrid-design-system-2.45

class HomeGridToggle(tk.Frame):
    """Фирменный переключатель HomeGrid: компактный тумблер без текста или радио-список с подписью."""
    def __init__(self, parent, variable, command=None, compact=False, on_text="Увімкнено", off_text="Вимкнено", palette=None, font_fam="Segoe UI", font_sz=10):
        self.var = variable
        self.cmd = command
        self.compact = bool(compact)
        self.on_text = on_text
        self.off_text = off_text
        self._fam = font_fam
        self._fs = font_sz
        self._state = "normal"
        self._pal = palette or {"panel": "#131c2e", "card": "#131c2e", "inp_bg": "#23314d", "border": "#1e293b", "text": "#f1f5f9", "muted": "#94a3b8", "blue": "#1d6ef2"}
        super().__init__(parent, bg=self._pal.get("card", "#131c2e"), bd=0, highlightthickness=0)
        if self.compact:
            w, h = max(36, int(font_sz * 3.4)), max(20, int(font_sz * 1.9))
            self.cv = tk.Canvas(self, width=w, height=h, bg=self._pal.get("panel", "#131c2e"), highlightthickness=0, bd=0, cursor="hand2")
            self.cv.pack()
            self.cv.bind("<Button-1>", self._on_click_compact)
        else:
            self.r_on = tk.Frame(self, bg=self._pal["card"], cursor="hand2")
            self.r_on.pack(fill="x", pady=(2, 4))
            self.cv_on = tk.Canvas(self.r_on, width=22, height=22, bg=self._pal["card"], highlightthickness=0, bd=0, cursor="hand2")
            self.cv_on.pack(side="left", padx=(0, 8))
            self.lbl_on = tk.Label(self.r_on, text=self.on_text, bg=self._pal["card"], fg=self._pal["text"], font=(self._fam, self._fs), cursor="hand2")
            self.lbl_on.pack(side="left")

            self.sep = tk.Frame(self, height=1, bg=self._pal.get("border", "#1e293b"))
            self.sep.pack(fill="x", pady=2)

            self.r_off = tk.Frame(self, bg=self._pal["card"], cursor="hand2")
            self.r_off.pack(fill="x", pady=(4, 2))
            self.cv_off = tk.Canvas(self.r_off, width=22, height=22, bg=self._pal["card"], highlightthickness=0, bd=0, cursor="hand2")
            self.cv_off.pack(side="left", padx=(0, 8))
            self.lbl_off = tk.Label(self.r_off, text=self.off_text, bg=self._pal["card"], fg=self._pal["text"], font=(self._fam, self._fs), cursor="hand2")
            self.lbl_off.pack(side="left")

            for w_it in (self.r_on, self.cv_on, self.lbl_on):
                w_it.bind("<Button-1>", lambda _e: self._set_val(True))
            for w_it in (self.r_off, self.cv_off, self.lbl_off):
                w_it.bind("<Button-1>", lambda _e: self._set_val(False))
        self.redraw()

    def _on_click_compact(self, _e=None):
        if self._state != "disabled":
            self._set_val(not bool(self.var.get()))

    def _set_val(self, val):
        if self._state == "disabled":
            return
        self.var.set(bool(val))
        self.redraw()
        if callable(self.cmd):
            self.cmd()

    def apply_style(self, palette=None, state=None, on_text=None, off_text=None, font_fam=None, font_sz=None):
        if palette: self._pal = palette
        if state: self._state = state
        if on_text is not None: self.on_text = on_text
        if off_text is not None: self.off_text = off_text
        if font_fam: self._fam = font_fam
        if font_sz: self._fs = font_sz
        self.redraw()

    def redraw(self):
        p = self._pal
        on = bool(self.var.get())
        acc = p.get("blue", "#1d6ef2")
        if self.compact:
            bg_p = p.get("panel", "#131c2e")
            self.configure(bg=bg_p)
            self.cv.configure(bg=bg_p, cursor="" if self._state == "disabled" else "hand2")
            self.cv.delete("all")
            w, h = int(self.cv.cget("width")), int(self.cv.cget("height"))
            r = (h - 4) // 2
            fill_c = acc if on else p.get("inp_bg", "#23314d")
            brd_c = acc if on else p.get("muted", "#64748b")
            self.cv.create_arc(2, 2, 2 + r * 2, 2 + r * 2, start=90, extent=180, fill=fill_c, outline=brd_c)
            self.cv.create_arc(w - 2 - r * 2, 2, w - 2, 2 + r * 2, start=270, extent=180, fill=fill_c, outline=brd_c)
            self.cv.create_rectangle(2 + r, 2, w - 2 - r, 2 + r * 2, fill=fill_c, outline="")
            self.cv.create_line(2 + r, 2, w - 2 - r, 2, fill=brd_c)
            self.cv.create_line(2 + r, 2 + r * 2, w - 2 - r, 2 + r * 2, fill=brd_c)
            kx = (w - 4 - r) if on else (4 + r)
            kr = max(4, r - 3)
            self.cv.create_oval(kx - kr, h // 2 - kr, kx + kr, h // 2 + kr, fill="#ffffff" if on else p.get("muted", "#94a3b8"), outline="")
            return
        c_bg = p.get("card", "#131c2e")
        self.configure(bg=c_bg)
        self.sep.configure(bg=p.get("border", "#1e293b"))
        for r_f, cv_i, lb_i, active, txt_s in ((self.r_on, self.cv_on, self.lbl_on, on, self.on_text), (self.r_off, self.cv_off, self.lbl_off, not on, self.off_text)):
            r_f.configure(bg=c_bg)
            cv_i.configure(bg=c_bg)
            lb_i.configure(text=txt_s, bg=c_bg, fg=p.get("text", "#f1f5f9") if active else p.get("muted", "#94a3b8"), font=(self._fam, self._fs, "bold" if active else "normal"))
            cv_i.delete("all")
            if active:
                cv_i.create_oval(2, 2, 20, 20, outline=acc, width=2, fill=p.get("inp_bg", "#23314d"))
                cv_i.create_oval(6, 6, 16, 16, fill=acc, outline="")
            else:
                cv_i.create_oval(2, 2, 20, 20, outline=p.get("muted", "#64748b"), width=2, fill=p.get("inp_bg", "#23314d"))

# patch-id: settings-two-pane-sidebar-2.47


def make_ui_icons(sz, fg_hex, accent_hex):
    try:
        from PIL import Image, ImageDraw, ImageTk
    except Exception:
        return {}
    s, up = max(14, int(sz)), max(14, int(sz)) * 2
    w = max(2, up // 10)
    out = {}
    def _new():
        im = Image.new("RGBA", (up, up), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)
    def _fin(im):
        return ImageTk.PhotoImage(im.resize((s, s), Image.LANCZOS))
    im, d = _new(); d.ellipse([3, 3, up - 4, up - 4], outline=fg_hex, width=w); d.line([up // 2, up // 4, up // 2, up // 2, up * 3 // 4, up // 2], fill=fg_hex, width=w); out["hist"] = _fin(im)
    im, d = _new(); d.polygon([(up // 2, 3), (up - 4, up // 4), (up * 4 // 5, up * 3 // 4), (up // 2, up - 3), (up // 5, up * 3 // 4), (4, up // 4)], outline=accent_hex, width=w); out["shield"] = _fin(im)
    im, d = _new(); d.ellipse([up // 4, up // 4, up * 3 // 4, up * 3 // 4], outline=accent_hex, width=w); d.ellipse([up * 2 // 5, up * 2 // 5, up * 3 // 5, up * 3 // 5], fill=accent_hex); out["gear"] = _fin(im)
    im, d = _new(); d.ellipse([up // 4, up // 5, up * 3 // 4, up * 3 // 4], outline=accent_hex, width=w); d.ellipse([3, up * 2 // 5, up // 2, up * 4 // 5], outline=accent_hex, width=w); d.ellipse([up // 2, up * 2 // 5, up - 4, up * 4 // 5], outline=accent_hex, width=w); d.line([up // 4, up * 4 // 5, up * 3 // 4, up * 4 // 5], fill=accent_hex, width=w); out["cloud"] = _fin(im)
    return out

class SidebarNavItem(tk.Frame):
    """Строка навигации левой панели настроек (~40 px) с иконкой и подсветкой активного раздела."""
    def __init__(self, parent, icon_img, icon_fallback, label_text, on_click, palette, font_fam="Segoe UI", font_sz=10, height_px=40):
        self._pal = palette
        self._on_click = on_click
        self._active = False
        self._fam = font_fam
        self._fs = font_sz
        super().__init__(parent, bg=palette["panel"], height=height_px, cursor="hand2", bd=0, highlightthickness=0)
        self.pack_propagate(False)
        self.inner = tk.Frame(self, bg=palette["panel"], padx=12, cursor="hand2")
        self.inner.pack(fill="both", expand=True)
        if icon_img is not None:
            self.lbl_ico = tk.Label(self.inner, image=icon_img, bg=palette["panel"], cursor="hand2")
            self.lbl_ico._img_ref = icon_img
        else:
            self.lbl_ico = tk.Label(self.inner, text=icon_fallback, width=2, anchor="center", bg=palette["panel"], fg=palette["muted"], font=(font_fam, font_sz, "bold"), cursor="hand2")
        self.lbl_ico.pack(side="left", padx=(0, 8))
        self.lbl_txt = tk.Label(self.inner, text=label_text, anchor="w", bg=palette["panel"], fg=palette["text"], font=(font_fam, font_sz), cursor="hand2")
        self.lbl_txt.pack(side="left", fill="x", expand=True)
        for w in (self, self.inner, self.lbl_ico, self.lbl_txt):
            w.bind("<Button-1>", self._handle_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _handle_click(self, _e=None):
        if callable(self._on_click):
            self._on_click()

    def _on_enter(self, _e=None):
        if not self._active:
            h_bg = self._pal.get("card", "#182338")
            for w in (self, self.inner, self.lbl_ico, self.lbl_txt):
                w.configure(bg=h_bg)

    def _on_leave(self, _e=None):
        if not self._active:
            n_bg = self._pal.get("panel", "#131c2e")
            for w in (self, self.inner, self.lbl_ico, self.lbl_txt):
                w.configure(bg=n_bg)

    def set_active(self, is_active, text_override=None):
        self._active = bool(is_active)
        if text_override is not None:
            self.lbl_txt.configure(text=text_override)
        bg_c = "#1c2a44" if (self._active and self._pal.get("bg") == "#0b1220") else (self._pal.get("inp_bg") if self._active else self._pal.get("panel"))
        fg_c = self._pal.get("cyan", "#60a5fa") if self._active else self._pal.get("text", "#f1f5f9")
        for w in (self, self.inner, self.lbl_ico, self.lbl_txt):
            w.configure(bg=bg_c)
        self.lbl_txt.configure(fg=fg_c, font=(self._fam, self._fs, "bold" if self._active else "normal"))
        if not hasattr(self.lbl_ico, "_img_ref"):
            self.lbl_ico.configure(fg=fg_c if self._active else self._pal.get("muted", "#94a3b8"))

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
        if lite != self.lite_mode or theme != self.theme or self._cw == 0 or abs(self.winfo_height() - self._ch) > 2:
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
            l_fs = max(11, min(18, h // 3))
            self._text = self.create_text(4, h // 2, anchor="w", text="", fill=self.theme["cyan"], font=(MONO, l_fs, "bold"))
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
