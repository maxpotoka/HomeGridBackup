# ==============================================================================
# [ФАЙЛ: gui/tray.py (v1.130 | 20.11.2026 15:52) — СИСТЕМНЫЙ ТРЕЙ WINDOWS (PYSTRAY) И СЛУШАТЕЛЬ ОКНА]
# ==============================================================================
import os
import time
import ctypes
import threading

def _detect_linux_tray_backend():
    import sys, subprocess
    if not sys.platform.startswith("linux"):
        return "native"
    from core.config import IS_WSL
    if IS_WSL:
        return ""
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        return ""
    try:
        out = subprocess.check_output(
            ["dbus-send", "--session", "--dest=org.freedesktop.DBus", "--type=method_call",
             "--print-reply", "/org/freedesktop/DBus", "org.freedesktop.DBus.NameHasOwner",
             "string:org.kde.StatusNotifierWatcher"],
            stderr=subprocess.DEVNULL, timeout=0.6
        ).decode("utf-8", errors="ignore")
        if "boolean true" in out:
            return "appindicator"
    except Exception:
        pass
    try:
        out_x = subprocess.check_output(["xprop", "-root", "_NET_SYSTEM_TRAY_S0"], stderr=subprocess.DEVNULL, timeout=0.5).decode("utf-8", errors="ignore")
        if "window id #" in out_x and "0x0" not in out_x:
            return "xorg"
    except Exception:
        pass
    de = (os.environ.get("XDG_CURRENT_DESKTOP") or "").upper()
    if any(k in de for k in ("XFCE", "KDE", "LXQT", "MATE", "CINNAMON")):
        return "appindicator"
    return ""

_LNX_TRAY_BE = _detect_linux_tray_backend()
if _LNX_TRAY_BE in ("appindicator", "xorg") and not os.environ.get("PYSTRAY_BACKEND"):
    os.environ["PYSTRAY_BACKEND"] = _LNX_TRAY_BE

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    HAS_TRAY = True
except Exception:
    pystray = None
    Image = None
    ImageDraw = None
    ImageFont = None
    HAS_TRAY = False

_TRAY_LOCK = threading.Lock()
_TRAY_STARTED = False
_TRAY_STOP = threading.Event()
_TRAY_FONT = None

def _get_tray_font():
    global _TRAY_FONT
    if _TRAY_FONT is not None:
        return _TRAY_FONT
    for fp in ("arialbd.ttf", "segoeui.ttf", "DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            _TRAY_FONT = ImageFont.truetype(fp, 18)
            return _TRAY_FONT
        except Exception:
            pass
    _TRAY_FONT = ImageFont.load_default()
    return _TRAY_FONT

def create_tray_image(pct=0, spin_idx=0):
    img = Image.new("RGBA", (64, 64), (11, 18, 32, 255))
    drw = ImageDraw.Draw(img)
    drw.ellipse([3, 3, 61, 61], outline=(43, 127, 255, 255), width=6)
    p_val = max(0, min(100, int(pct)))
    if p_val > 0:
        end_ang = -90 + int(360 * p_val / 100.0)
        drw.arc([3, 3, 61, 61], start=-90, end=end_ang, fill=(16, 185, 129, 255), width=8)
    if os.name != "nt":
        drw.ellipse([21, 21, 43, 43], fill=(16, 185, 129, 255) if p_val > 0 else (43, 127, 255, 255))
        return img
    lbl = f"{p_val}" if p_val > 0 else "HG"
    fnt = _get_tray_font()
    bbox = drw.textbbox((0, 0), lbl, font=fnt) if hasattr(drw, "textbbox") else (0, 0, len(lbl) * 10, 16)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    drw.text(((64 - tw) // 2, (64 - th) // 2 - 1), lbl, fill=(255, 255, 255, 255), font=fnt)
    return img

def _get_tray_img_safe(pct, is_run, pill_type, spin_idx=0):
    try:
        return create_tray_image(pct, spin_idx)
    except Exception:
        img = Image.new("RGBA", (64, 64), (16, 185, 129, 255) if pill_type == "ok" else (43, 127, 255, 255))
        drw = ImageDraw.Draw(img)
        drw.rectangle((4, 4, 60, 60), outline=(255, 255, 255, 220), width=3)
        drw.text((12, 22), f"{int(pct)}%" if is_run else "HGB", fill=(255, 255, 255, 255))
        return img

def _force_quit_app(engine):
    _TRAY_STOP.set()
    try:
        if engine.tray_icon is not None:
            engine.tray_icon.visible = False
            engine.tray_icon.stop()
            engine.tray_icon = None
            time.sleep(0.12)
    except Exception:
        pass
    try:
        if engine.app_ref is not None:
            engine.app_ref.root.quit()
            engine.app_ref.root.destroy()
    except Exception:
        pass
    os._exit(0)

def _can_dock_linux_tray():
    return bool(_LNX_TRAY_BE)

def _start_tray_thread(engine):
    global _TRAY_STARTED
    from core.config import IS_WSL
    with _TRAY_LOCK:
        if _TRAY_STARTED:
            return
        if IS_WSL:
            _TRAY_STARTED = True
            engine.tray_icon = None
            engine.log("Системний трей недоступний у середовищі WSL — робота продовжується без іконки в треї.", "info")
            return
        if not HAS_TRAY or not _can_dock_linux_tray():
            _TRAY_STARTED = True
            engine.tray_icon = None
            engine.log("Системний трей недоступний (потрібне розширення AppIndicator у GNOME).", "warn")
            return
        _TRAY_STARTED = True
        _TRAY_STOP.clear()
    from core.backup import run_backup_task
    from core.i18n import tr

    def _on_open(icon, item):
        if engine.app_ref is not None:
            engine.app_ref.root.after(0, engine.app_ref.show_window)

    def _on_backup(icon, item):
        if engine.is_running:
            return
        threading.Thread(
            target=run_backup_task,
            args=(engine, engine.state.get("server", ""), False, False, False),
            daemon=True
        ).start()

    def _on_exit(icon, item):
        _force_quit_app(engine)

    _lng = engine.state.get("lang", "en")
    menu = pystray.Menu(
        pystray.MenuItem(tr("Відкрити HomeGrid Backup", _lng), _on_open, default=True, enabled=lambda item: engine.app_ref is not None),
        pystray.MenuItem(tr("▶ Запустити резервне копіювання", _lng), _on_backup),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(tr("✖ Вихід", _lng), _on_exit)
    )
    icon = pystray.Icon(f"HomeGridBackup_{os.getpid()}", _get_tray_img_safe(0, False, "idle", 0), "HomeGrid Backup", menu)
    engine.tray_icon = icon

    def _anim_loop():
        err_streak = 0
        last_sig, last_title = None, ""
        while not _TRAY_STOP.is_set():
            _TRAY_STOP.wait(1.0)
            if _TRAY_STOP.is_set():
                break
            try:
                if engine.tray_icon is None:
                    break
                if not getattr(engine.tray_icon, "visible", True):
                    continue
                cur_pct = int(engine.progress) if engine.is_running else 0
                sig = (cur_pct, engine.is_running, engine.pill_type)
                if sig != last_sig:
                    engine.tray_icon.icon = _get_tray_img_safe(cur_pct, engine.is_running, engine.pill_type, 0)
                    last_sig = sig
                new_title = f"HomeGrid Backup ({cur_pct}%): {(engine.stage or '')[:45]}" if engine.is_running else "HomeGrid Backup"
                if new_title != last_title:
                    engine.tray_icon.title = new_title
                    last_title = new_title
                err_streak = 0
            except AssertionError:
                engine.tray_icon = None
                break
            except Exception:
                err_streak += 1
                if err_streak >= 3:
                    engine.tray_icon = None
                    break

    def _run_icon_safe():
        try:
            icon.run()
        except Exception:
            engine.tray_icon = None

    threading.Thread(target=_anim_loop, daemon=True).start()
    threading.Thread(target=_run_icon_safe, daemon=True).start()

def _start_show_window_listener(engine, event_name=r"Global\HomeGridBackup_ShowWindow_v1"):
    if os.name != "nt":
        def _posix_wait_loop():
            try:
                import sys, hashlib, socket, tempfile
                _inst_id = hashlib.md5(os.path.realpath(sys.argv[0]).encode("utf-8", errors="ignore")).hexdigest()[:10]
                _port_p = os.path.join(tempfile.gettempdir(), f"hgb_inst_{_inst_id}.port")
                srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                srv.bind(("127.0.0.1", 0))
                srv.listen(2)
                with open(_port_p, "w") as pf:
                    pf.write(str(srv.getsockname()[1]))
                while True:
                    conn, _ = srv.accept()
                    data = conn.recv(16)
                    conn.close()
                    if b"SHOW" in data and engine.app_ref is not None:
                        engine.app_ref.root.after(0, engine.app_ref.show_window)
            except Exception:
                pass
        threading.Thread(target=_posix_wait_loop, daemon=True).start()
        return
    def _wait_loop():
        try:
            k32 = ctypes.windll.kernel32
            h_ev = k32.CreateEventW(None, False, False, event_name)
            while h_ev:
                if k32.WaitForSingleObject(h_ev, 1000) == 0 and engine.app_ref is not None:
                    engine.app_ref.root.after(0, engine.app_ref.show_window)
        except Exception:
            pass
    threading.Thread(target=_wait_loop, daemon=True).start()
