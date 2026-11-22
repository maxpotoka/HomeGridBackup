# ==============================================================================
# [ФАЙЛ: gui/tray.py (v2.05 | 22.11.2026 02:07)
# patch-id: macos-quit-and-buttons-2.17
# ==============================================================================
import os
import time
import ctypes
import threading


def _clean_sys_env():
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    if "LD_LIBRARY_PATH_ORIG" in env:
        env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
    else:
        env.pop("LD_LIBRARY_PATH", None)
    if hasattr(os, "getuid"):
        bus_p = f"/run/user/{os.getuid()}/bus"
        cur_bus = env.get("DBUS_SESSION_BUS_ADDRESS", "")
        if os.path.exists(bus_p) and (not cur_bus or ("unix:path=" in cur_bus and not os.path.exists(cur_bus.split("unix:path=", 1)[1].split(",", 1)[0]))):
            env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={bus_p}"
            os.environ["DBUS_SESSION_BUS_ADDRESS"] = env["DBUS_SESSION_BUS_ADDRESS"]
    return env

def _has_appindicator_gi():
    try:
        import gi
        for ns in ("AyatanaAppIndicator3", "AppIndicator3"):
            try:
                gi.require_version(ns, "0.1")
                __import__(f"gi.repository.{ns}")
                return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def _has_gtk_gi():
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        return Gtk is not None
    except (ImportError, ValueError):
        return False


def _has_sni_watcher(env):
    import re
    import shutil
    import subprocess

    commands = (
        ("dbus-send", [
            "--session", "--dest=org.freedesktop.DBus", "--type=method_call",
            "--print-reply", "/org/freedesktop/DBus",
            "org.freedesktop.DBus.NameHasOwner",
            "string:org.kde.StatusNotifierWatcher",
        ]),
        ("gdbus", [
            "call", "--session", "--dest", "org.freedesktop.DBus",
            "--object-path", "/org/freedesktop/DBus", "--method",
            "org.freedesktop.DBus.NameHasOwner",
            "org.kde.StatusNotifierWatcher",
        ]),
        ("busctl", [
            "--user", "call", "org.freedesktop.DBus", "/org/freedesktop/DBus",
            "org.freedesktop.DBus", "NameHasOwner", "s",
            "org.kde.StatusNotifierWatcher",
        ]),
    )
    for executable, args in commands:
        if not shutil.which(executable, path=env.get("PATH")):
            continue
        try:
            out = subprocess.check_output(
                [executable, *args],
                env=env,
                stderr=subprocess.DEVNULL,
                timeout=0.9,
            ).decode("utf-8", errors="ignore")
            if re.search(r"\btrue\b", out, re.I):
                return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False


def _has_x11_tray_manager():
    if not os.environ.get("DISPLAY"):
        return False
    try:
        from ctypes.util import find_library
        x11_path = find_library("X11")
        if not x11_path:
            return False
        x11 = ctypes.CDLL(x11_path)
    except OSError:
        return False

    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
    x11.XDefaultScreen.restype = ctypes.c_int
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XGetSelectionOwner.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XGetSelectionOwner.restype = ctypes.c_ulong
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XCloseDisplay.restype = ctypes.c_int

    display = x11.XOpenDisplay(os.environ["DISPLAY"].encode("utf-8"))
    if not display:
        return False
    try:
        screen = x11.XDefaultScreen(display)
        selection = f"_NET_SYSTEM_TRAY_S{screen}".encode("ascii")
        atom = x11.XInternAtom(display, selection, 0)
        return bool(atom and x11.XGetSelectionOwner(display, atom))
    finally:
        x11.XCloseDisplay(display)


def _detect_linux_tray_backend():
    import sys
    if not sys.platform.startswith("linux"):
        return "native"
    from core.config import IS_WSL
    if IS_WSL or (not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")):
        return ""
    for gp in ("/usr/lib/x86_64-linux-gnu/girepository-1.0", "/usr/lib/aarch64-linux-gnu/girepository-1.0", "/usr/lib/girepository-1.0"):
        if os.path.isdir(gp) and gp not in os.environ.get("GI_TYPELIB_PATH", ""):
            os.environ["GI_TYPELIB_PATH"] = f"{gp}:{os.environ.get('GI_TYPELIB_PATH', '')}".rstrip(":")
    sys_env = _clean_sys_env()
    if _has_sni_watcher(sys_env):
        return "appindicator" if _has_appindicator_gi() else "auto"
    if _has_x11_tray_manager():
        return "gtk" if _has_gtk_gi() else "xorg"
    return ""

_LNX_TRAY_BE = _detect_linux_tray_backend()
if _LNX_TRAY_BE in ("appindicator", "gtk", "xorg") and not os.environ.get("PYSTRAY_BACKEND"):
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
    from core.files import get_app_icon_path
    ico_p = get_app_icon_path()
    base_img = None
    if ico_p:
        try:
            base_img = Image.open(ico_p).convert("RGBA").resize((64, 64), Image.LANCZOS)
        except Exception:
            base_img = None
    if base_img is not None:
        img = base_img.copy()
        p_val = max(0, min(100, int(pct)))
        if p_val > 0:
            drw = ImageDraw.Draw(img)
            drw.ellipse([36, 36, 62, 62], fill=(11, 18, 32, 235), outline=(16, 185, 129, 255), width=3)
            end_ang = -90 + int(360 * p_val / 100.0)
            drw.arc([38, 38, 60, 60], start=-90, end=end_ang, fill=(16, 185, 129, 255), width=4)
        return img
    img = Image.new("RGBA", (64, 64), (11, 18, 32, 255))
    drw = ImageDraw.Draw(img)
    drw.ellipse([3, 3, 61, 61], outline=(43, 127, 255, 255), width=6)
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
    if os.sys.platform != "darwin":
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


def _tray_status_text(engine, language, elapsed_sec=0):
    from core.files import format_duration
    from core.i18n import tr

    if not engine.is_running:
        return tr("Готовий до резервного копіювання", language)
    stage = tr(engine.stage, language) if engine.stage else ""
    progress = int(engine.progress)
    elapsed = format_duration(elapsed_sec, language)
    return f"{tr('Резервне копіювання...', language)} {progress}% | {stage} | {elapsed}"


def _tray_problem():
    import sys
    if not HAS_TRAY:
        return "Трей: не встановлено pystray і Pillow"
    if sys.platform.startswith("linux") and not _LNX_TRAY_BE:
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            return "Немає графічної сесії (DISPLAY не задано) — трей вимкнено"
        de = f"{os.environ.get('XDG_CURRENT_DESKTOP', '')} {os.environ.get('DESKTOP_SESSION', '')}".upper()
        if "XFCE" in de:
            return "Трей XFCE: встановіть xfce4-statusnotifier-plugin і додайте «Status Notifier» на панель"
        if "GNOME" in de or "UNITY" in de:
            return "Трей GNOME: встановіть розширення AppIndicator and KStatusNotifierItem Support"
        if "KDE" in de or "PLASMA" in de:
            return "Трей KDE: перевірте, що увімкнено віджет «Системний лоток»"
        return "Панель не підтримує трей (потрібен StatusNotifier або XEmbed)"
    return "Системний трей недоступний"

def _start_tray_thread(engine):
    global _TRAY_STARTED
    from core.config import IS_WSL, NO_TRAY
    with _TRAY_LOCK:
        if _TRAY_STARTED:
            return
        if NO_TRAY or not engine.state.get("tray_enabled", True):
            _TRAY_STARTED = True
            engine.tray_icon = None
            engine.log("Трей вимкнено (--no-tray або в налаштуваннях).", "info")
            return
        if IS_WSL:
            _TRAY_STARTED = True
            engine.tray_icon = None
            engine.log("Системний трей недоступний у середовищі WSL — робота продовжується без іконки в треї.", "info")
            return
        if not HAS_TRAY or not _can_dock_linux_tray():
            _TRAY_STARTED = True
            engine.tray_icon = None
            engine.log(_tray_problem(), "warn")
            return
        _TRAY_STARTED = True
        _TRAY_STOP.clear()
        engine.tray_ready = False
        engine.tray_error = ""
        engine.tray_ready_event = threading.Event()
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

    def _on_open_folder(icon, item):
        from core.files import open_folder_native
        from core.config import DEFAULT_BACKUP_DIR
        open_folder_native(engine.state.get("backup_dir") or DEFAULT_BACKUP_DIR)

    def _on_open_dialog(method_name):
        def _cb(icon, item):
            if engine.app_ref is not None:
                def _run_ui_dlg():
                    engine.app_ref.show_window()
                    fn = getattr(engine.app_ref, method_name, None)
                    if callable(fn):
                        fn()
                engine.app_ref.root.after(0, _run_ui_dlg)
        return _cb

    run_started_at = None

    def _elapsed_seconds():
        nonlocal run_started_at
        if not engine.is_running:
            run_started_at = None
            return 0
        if run_started_at is None:
            run_started_at = time.monotonic()
        return int(time.monotonic() - run_started_at)

    def _build_tray_menu():
        lng_s = engine.state.get("lang", "en")
        elapsed_sec = _elapsed_seconds()
        st_txt = _tray_status_text(engine, lng_s, elapsed_sec)
        return pystray.Menu(
            pystray.MenuItem(tr("Відкрити HomeGrid Backup", lng_s), _on_open, default=True, enabled=lambda item: engine.app_ref is not None),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(st_txt, lambda i, it: None, enabled=False),
            pystray.MenuItem(tr("▶ Запустити резервне копіювання", lng_s), _on_backup, enabled=lambda item: not engine.is_running),
            pystray.MenuItem(tr("Відкрити папку", lng_s), _on_open_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(tr("Статистика", lng_s), _on_open_dialog("open_stats_modal"), enabled=lambda item: engine.app_ref is not None),
            pystray.MenuItem(tr("Аналіз GFS / SHA-256", lng_s), _on_open_dialog("open_analyze"), enabled=lambda item: engine.app_ref is not None),
            pystray.MenuItem(tr("Налаштування", lng_s), _on_open_dialog("open_settings"), enabled=lambda item: engine.app_ref is not None),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(tr("✖ Вихід", lng_s), _on_exit)
        )

    try:
        icon = pystray.Icon(f"HomeGridBackup_{os.getpid()}", _get_tray_img_safe(0, False, "idle", 0), "HomeGrid Backup", _build_tray_menu())
    except Exception as exc:
        with _TRAY_LOCK:
            _TRAY_STARTED = False
        engine.tray_icon = None
        engine.tray_error = str(exc)
        engine.tray_ready_event.set()
        engine.log("Не вдалося створити значок системного трею.", "err")
        return
    engine.tray_icon = icon

    def _mark_tray_failed(exc):
        global _TRAY_STARTED
        engine.tray_ready = False
        engine.tray_error = str(exc) or "Невідома помилка запуску трею."
        engine.tray_icon = None
        engine.tray_ready_event.set()
        _TRAY_STOP.set()
        with _TRAY_LOCK:
            _TRAY_STARTED = False
        engine.log("Не вдалося запустити значок системного трею.", "err")
        engine.log(f"[TRAY DETAIL] {engine.tray_error}", "err")
        if engine.app_ref is not None:
            try:
                engine.app_ref.root.after(0, engine.app_ref.root.deiconify)
            except Exception:
                pass

    def _refresh_tray_menu():
        if engine.tray_icon is not None:
            engine.tray_icon.menu = _build_tray_menu()
            engine.tray_icon.update_menu()

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
                if not engine.tray_ready:
                    continue
                if not getattr(engine.tray_icon, "visible", True):
                    continue
                cur_pct = int(engine.progress) if engine.is_running else 0
                sig = (cur_pct, engine.is_running, engine.pill_type)
                elapsed_sec = _elapsed_seconds()
                lng_s = engine.state.get("lang", "en")
                if os.sys.platform == "darwin" and engine.is_running:
                    new_title = f"HomeGrid Backup: {_tray_status_text(engine, lng_s, elapsed_sec)}"
                else:
                    new_title = f"HomeGrid Backup ({cur_pct}%): {(engine.stage or '')[:45]}" if engine.is_running else "HomeGrid Backup"
                if os.sys.platform == "darwin":
                    sig_changed = sig != last_sig
                    if sig_changed:
                        last_sig = sig
                        if engine.app_ref is not None:
                            _im_mac = _get_tray_img_safe(cur_pct, engine.is_running, engine.pill_type, 0)
                            engine.app_ref.root.after(0, lambda im=_im_mac: setattr(engine.tray_icon, "icon", im) if engine.tray_icon else None)
                    if engine.is_running or sig_changed:
                        if engine.app_ref is not None:
                            engine.app_ref.root.after(0, _refresh_tray_menu)
                        else:
                            _refresh_tray_menu()
                    if new_title != last_title:
                        last_title = new_title
                        if engine.app_ref is not None:
                            engine.app_ref.root.after(0, lambda t=new_title: setattr(engine.tray_icon, "title", t) if engine.tray_icon else None)
                else:
                    sig_changed = sig != last_sig
                    if sig_changed:
                        engine.tray_icon.icon = _get_tray_img_safe(cur_pct, engine.is_running, engine.pill_type, 0)
                        last_sig = sig
                    if os.sys.platform != "darwin" or sig_changed:
                        engine.tray_icon.menu = _build_tray_menu()
                        engine.tray_icon.update_menu()
                    if new_title != last_title:
                        engine.tray_icon.title = new_title
                        last_title = new_title
                err_streak = 0
            except AssertionError as exc:
                _mark_tray_failed(exc)
                break
            except Exception as exc:
                err_streak += 1
                if err_streak >= 3:
                    _mark_tray_failed(exc)
                    break

    def _on_icon_setup(ready_icon):
        try:
            ready_icon.visible = True
            engine.tray_ready = True
        except Exception as exc:
            _mark_tray_failed(exc)
        else:
            engine.tray_ready_event.set()

    def _run_icon_safe():
        try:
            icon.run(setup=_on_icon_setup)
        except Exception as exc:
            _mark_tray_failed(exc)

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
