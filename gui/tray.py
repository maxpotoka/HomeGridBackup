# ==============================================================================
# [ФАЙЛ: gui/tray.py (v1.057 | 19.11.2026 15:35) — СИСТЕМНЫЙ ТРЕЙ WINDOWS (PYSTRAY) И СЛУШАТЕЛЬ ОКНА]
# ==============================================================================
import os
import time
import ctypes
import threading

def _detect_linux_tray_backend():
    import sys, subprocess
    if not sys.platform.startswith("linux"):
        return "native"
    if os.environ.get("WSL_DISTRO_NAME") or os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop"):
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
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except Exception:
    pystray = None
    Image = None
    ImageDraw = None
    HAS_TRAY = False

def create_tray_image(pct=0, spin_idx=0):
    img = Image.new("RGBA", (64, 64), (11, 18, 32, 255))
    drw = ImageDraw.Draw(img)
    drw.ellipse([4, 4, 60, 60], outline=(43, 127, 255, 255), width=5)
    if pct > 0:
        end_ang = -90 + int(360 * min(100, pct) / 100.0)
        drw.arc([4, 4, 60, 60], start=-90, end=end_ang, fill=(16, 185, 129, 255), width=6)
    drw.text((14, 24), f"{int(pct)}%" if pct > 0 else "HGB", fill=(255, 255, 255, 255))
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
    if not HAS_TRAY or not _can_dock_linux_tray():
        engine.tray_icon = None
        return
    from core.backup import run_backup_task

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

    menu = pystray.Menu(
        pystray.MenuItem("Відкрити HomeGrid Backup", _on_open, default=True),
        pystray.MenuItem("▶ Запустити резервне копіювання", _on_backup),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("✖ Вихід", _on_exit)
    )
    icon = pystray.Icon(f"HomeGridBackup_{os.getpid()}", _get_tray_img_safe(0, False, "idle", 0), "HomeGrid Backup", menu)
    engine.tray_icon = icon

    def _anim_loop():
        err_streak = 0
        while True:
            time.sleep(1.2 if engine.state.get("lite_mode", False) else 0.7)
            try:
                if engine.tray_icon is None:
                    break
                if not getattr(engine.tray_icon, "visible", True):
                    continue
                if engine.is_running:
                    engine.tray_spin_idx = (engine.tray_spin_idx + 1) % 8
                engine.tray_icon.icon = _get_tray_img_safe(engine.progress, engine.is_running, engine.pill_type, engine.tray_spin_idx)
                engine.tray_icon.title = f"HomeGrid Backup ({engine.progress}%): {(engine.stage or 'Готовий')[:45]}"
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
                    pf.write(str(srv.getsockname()))
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
