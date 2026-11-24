# ==============================================================================
# patch-id: pcloud-speed-progress-gradient-2.33
# patch-id: linux-wayland-sni-bridge-2.32
# patch-id: linux-xorg-tray-menu-2.26
# patch-id: macos-tray-quit-apps-2.41
# patch-id: cumulative-linux-tray-pcloud-menu-2.42
# [ФАЙЛ: gui/tray.py (v2.09 | 23.11.2026 16:20)
# patch-id: macos-quit-and-buttons-2.17
# ==============================================================================
import os
import time
import ctypes
import threading


import queue as _queue_mod
_TRAY_UI_QUEUE = _queue_mod.SimpleQueue()

def _enqueue_tray_ui(fn):
    if callable(fn):
        _TRAY_UI_QUEUE.put(fn)

def drain_tray_ui_queue():
    while True:
        try:
            fn = _TRAY_UI_QUEUE.get_nowait()
        except Exception:
            break
        try:
            fn()
        except Exception:
            pass

def _linux_tray_diag_line():
    sess = os.environ.get("XDG_SESSION_TYPE", "?")
    de = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "?"
    disp = os.environ.get("DISPLAY", "-")
    wdisp = os.environ.get("WAYLAND_DISPLAY", "-")
    dbus = "yes" if os.environ.get("DBUS_SESSION_BUS_ADDRESS") else "no"
    return f"[TRAY DIAG] OS=Linux | session={sess} | DE={de} | DISPLAY={disp} | WAYLAND={wdisp} | DBUS={dbus} | backend={_LNX_TRAY_BE or 'none'}"

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
    if not getattr(sys, "frozen", False):
        for gp in ("/usr/lib/x86_64-linux-gnu/girepository-1.0", "/usr/lib/i386-linux-gnu/girepository-1.0", "/usr/lib/aarch64-linux-gnu/girepository-1.0", "/usr/lib/girepository-1.0"):
            if os.path.isdir(gp) and gp not in os.environ.get("GI_TYPELIB_PATH", ""):
                os.environ["GI_TYPELIB_PATH"] = f"{gp}:{os.environ.get('GI_TYPELIB_PATH', '')}".rstrip(":")
    sys_env = _clean_sys_env()
    if _has_sni_watcher(sys_env):
        return "appindicator" if _has_appindicator_gi() else "sni-bridge"
    if _has_x11_tray_manager():
        return "gtk" if _has_gtk_gi() else "xorg"
    return ""

_LNX_TRAY_BE = ""
_LNX_TRAY_PROBED = False
_LNX_PROBE_LOCK = threading.Lock()

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

# Режимы трея, которые пользователь выбирает вручную в настройках (state["tray_backend"]).
# "auto" — как раньше, автоопределение.
_LINUX_TRAY_MODES = ("auto", "appindicator", "sni-bridge", "gtk", "xorg", "none")
_MAC_TRAY_MODES = ("auto", "pystray", "none")
TRAY_MODE_HINTS = {
    "appindicator": "Ubuntu/GNOME/XFCE с AppIndicator: нужен пакет gir1.2-ayatanaappindicator3-0.1. Значок должен появиться в верхней панели.",
    "sni-bridge": "Wayland или панель StatusNotifier без доступного gi: используется системный /usr/bin/python3. Смотрите строку «AppIndicator bridge» в логе.",
    "gtk": "X11: Tkinter-меню внутри окна/панели, запасной вариант, если нет AppIndicator.",
    "xorg": "Классический XEmbed-трей: работает только на панелях с X11 System Tray.",
    "none": "Трей выключен, программа работает без значка.",
    "pystray": "macOS: значок в верхнем Menu Bar через pystray. Если значка нет, смотрите «[TRAY DETAIL]» в логе.",
}


def _requested_tray_backend(engine):
    raw = str(engine.state.get("tray_backend", "auto") or "auto").strip().lower()
    allowed = _LINUX_TRAY_MODES if os.sys.platform.startswith("linux") else _MAC_TRAY_MODES
    if raw in ("", "auto"):
        return ""
    if raw not in allowed:
        engine.log(f"[TRAY MODE] невідомий режим '{raw}', використано auto", "warn")
        return ""
    return raw


def _status_gradient_rgb(pct, is_run, pill_type):
    if pill_type == "err":
        return (239, 68, 68, 255)
    if pill_type == "warn":
        return (245, 158, 11, 255)
    if not is_run:
        return (16, 185, 129, 255)
    t = max(0.0, min(1.0, float(pct) / 100.0))
    if t <= 0.5:
        k = t / 0.5
        return (int(16 + (14 - 16) * k), int(185 + (165 - 185) * k), int(129 + (233 - 129) * k), 255)
    k = (t - 0.5) / 0.5
    return (int(14 + (245 - 14) * k), int(165 + (158 - 165) * k), int(233 + (11 - 233) * k), 255)

def _show_wayland_fallback_badge(engine):
    import sys
    import tkinter as tk
    if not sys.platform.startswith("linux") or engine.app_ref is None:
        return
    app = engine.app_ref
    if getattr(app, "_wl_badge", None) is not None:
        return
    try:
        top = tk.Toplevel(app.root)
        top.wm_overrideredirect(True)
        top.attributes("-topmost", True)
        lbl = tk.Label(top, text="● HomeGrid", fg="#ffffff", bg="#10b981", font=("Ubuntu", 9, "bold"), padx=10, pady=4, cursor="hand2")
        lbl.pack()
        lbl.bind("<Button-1>", lambda _e: app.show_window())
        top.geometry("+14+38")
        app._wl_badge = top
        def _tick():
            if not top.winfo_exists(): return
            r, g, b, _ = _status_gradient_rgb(engine.progress if engine.is_running else 0, engine.is_running, getattr(engine, "pill_type", "idle"))
            hx = f"#{r:02x}{g:02x}{b:02x}"
            txt = f"● {int(engine.progress)}%" if engine.is_running else "● HGB OK"
            lbl.configure(bg=hx, text=txt)
            top.after(1000, _tick)
        _tick()
    except Exception:
        pass

_BASE_ICON_CACHE = {}

def _get_base_icon(ico_p):
    if not ico_p:
        return None
    if ico_p not in _BASE_ICON_CACHE:
        try:
            _BASE_ICON_CACHE[ico_p] = Image.open(ico_p).convert("RGBA").resize((64, 64), Image.LANCZOS)
        except Exception:
            _BASE_ICON_CACHE[ico_p] = None
    return _BASE_ICON_CACHE[ico_p]

def create_tray_image(pct=0, spin_idx=0, pill_type="idle"):
    from core.files import get_app_icon_path
    ico_p = get_app_icon_path()
    base_img = _get_base_icon(ico_p)
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
    col_g = _status_gradient_rgb(pct, pct > 0, pill_type)
    drw.ellipse([3, 3, 61, 61], fill=col_g, outline=(255, 255, 255, 220), width=4)
    return img

def _get_tray_img_safe(pct, is_run, pill_type, spin_idx=0):
    try:
        return create_tray_image(pct, spin_idx, pill_type)
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


def _tray_backend_available():
    return HAS_TRAY and (
        not os.sys.platform.startswith("linux") or _can_dock_linux_tray()
    )


def _tray_status_text(engine, language, elapsed_sec=0):
    from core.i18n import tr

    if not engine.is_running:
        return tr("Готовий до резервного копіювання", language)
    progress = int(engine.progress)
    elapsed_sec = max(0, int(elapsed_sec))
    hours, remainder = divmod(elapsed_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    elapsed = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
    return f"{tr('Архівація', language)} · {elapsed} · {progress}%"


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
    global _TRAY_STARTED, _LNX_TRAY_BE, _LNX_TRAY_PROBED

    if os.sys.platform.startswith("linux"):
        with _LNX_PROBE_LOCK:
            if not _LNX_TRAY_PROBED:
                _LNX_TRAY_PROBED = True
                engine.tray_ready_event = threading.Event()

                def _probe_linux_tray():
                    global _LNX_TRAY_BE
                    forced = _requested_tray_backend(engine)
                    if forced:
                        _LNX_TRAY_BE = "" if forced == "none" else forced
                        engine.log(f"[TRAY MODE] вибрано вручну: {forced}. {TRAY_MODE_HINTS.get(forced, '')} Після зміни режиму перезапустіть застосунок.", "info")
                    else:
                        _LNX_TRAY_BE = _detect_linux_tray_backend()
                    engine.log(_linux_tray_diag_line(), "info")
                    if _LNX_TRAY_BE == "sni-bridge":
                        if _start_wayland_sni_bridge(engine):
                            with _TRAY_LOCK:
                                _TRAY_STARTED = True
                            return
                        _LNX_TRAY_BE = "xorg" if _has_x11_tray_manager() else ""
                    if _LNX_TRAY_BE in ("appindicator", "gtk", "xorg") and not os.environ.get("PYSTRAY_BACKEND"):
                        os.environ["PYSTRAY_BACKEND"] = _LNX_TRAY_BE
                    if not _LNX_TRAY_BE:
                        with _TRAY_LOCK:
                            _TRAY_STARTED = False
                        engine.tray_ready = False
                        engine.tray_icon = None
                        engine.tray_ready_event.set()
                        if forced == "none":
                            engine.log("[TRAY MODE] трей вимкнено вручну в налаштуваннях.", "info")
                        else:
                            engine.log(_tray_problem(), "warn")
                        _enqueue_tray_ui(lambda: _show_wayland_fallback_badge(engine))
                        return
                    _start_tray_thread(engine)

                threading.Thread(target=_probe_linux_tray, daemon=True).start()
                return

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
        if os.sys.platform == "darwin" and _requested_tray_backend(engine) == "none":
            _TRAY_STARTED = True
            engine.tray_icon = None
            engine.log("[TRAY MODE] трей вимкнено вручну в налаштуваннях.", "info")
            return
        if not _tray_backend_available():
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
            _enqueue_tray_ui(engine.app_ref.show_window)

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
                _enqueue_tray_ui(_run_ui_dlg)
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
            pystray.MenuItem("☁ " + ("Статистика pCloud" if lng_s == "uk" else "pCloud Stats"), _on_open_dialog("open_cloud_stats_modal"), enabled=lambda item: engine.app_ref is not None),
            pystray.MenuItem(tr("Журнал операцій", lng_s), _on_open_dialog("open_ops_history"), enabled=lambda item: engine.app_ref is not None),
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
            _enqueue_tray_ui(engine.app_ref.show_window)

    def _anim_loop():
        err_streak = 0
        last_sig, last_menu_sig, last_title = None, None, ""
        last_menu_ts = 0.0
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
                lng_s = engine.state.get("lang", "en")
                sig = (cur_pct, engine.is_running, engine.pill_type)
                menu_sig = (cur_pct if engine.is_running else 0, engine.is_running, lng_s, engine.app_ref is not None)
                elapsed_sec = _elapsed_seconds()
                new_title = (
                    f"HomeGrid Backup: {_tray_status_text(engine, lng_s, elapsed_sec)}"
                    if engine.is_running else "HomeGrid Backup"
                )
                if sig != last_sig:
                    engine.tray_icon.icon = _get_tray_img_safe(cur_pct, engine.is_running, engine.pill_type, 0)
                    last_sig = sig
                now_m = time.monotonic()
                menu_due = (now_m - last_menu_ts) >= 3.0
                if menu_sig != last_menu_sig or (engine.is_running and menu_due):
                    engine.tray_icon.menu = _build_tray_menu()
                    engine.tray_icon.update_menu()
                    last_menu_sig = menu_sig
                    last_menu_ts = now_m
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
            engine.log(f"Значок системного трею активовано ({type(ready_icon).__module__}).", "info")
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
    if os.sys.platform == "darwin":
        def _start_mac_detached():
            try:
                if hasattr(icon, "run_detached"):
                    icon.run_detached(setup=_on_icon_setup)
                else:
                    _on_icon_setup(icon)
            except Exception as exc:
                _mark_tray_failed(exc)
        if engine.app_ref is not None:
            engine.app_ref.root.after(0, _start_mac_detached)
        else:
            _start_mac_detached()
    else:
        threading.Thread(target=_run_icon_safe, daemon=True).start()



_SNI_HELPER = """
import sys, json, threading, signal, gi
gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AI
except Exception:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3 as AI
from gi.repository import Gtk, GLib

ind = AI.Indicator.new("homegrid-backup", sys.argv, AI.IndicatorCategory.APPLICATION_STATUS)
ind.set_status(AI.IndicatorStatus.ACTIVE)
menu = Gtk.Menu()
items = {}
for k, lbl in json.loads(sys.argv):
    if lbl is None:
        menu.append(Gtk.SeparatorMenuItem())
        continue
    mi = Gtk.MenuItem(label=lbl)
    if k == "status":
        mi.set_sensitive(False)
    else:
        mi.connect("activate", lambda _w, c=k: print(json.dumps({"cmd": c}), flush=True))
    menu.append(mi)
    items[k] = mi
menu.show_all()
ind.set_menu(menu)
print(json.dumps({"ready": True}), flush=True)

def _in_loop():
    for ln in sys.stdin:
        try:
            d = json.loads(ln)
            if "status" in d: GLib.idle_add(items["status"].set_label, d["status"])
            if "running" in d: GLib.idle_add(items["backup"].set_sensitive, not d["running"])
            if d.get("quit"): break
        except Exception:
            pass
    GLib.idle_add(Gtk.main_quit)

threading.Thread(target=_in_loop, daemon=True).start()
signal.signal(signal.SIGINT, signal.SIG_DFL)
Gtk.main()
"""

def _start_wayland_sni_bridge(engine):
    import subprocess, json
    from core.files import get_app_icon_path, open_folder_native
    from core.config import DEFAULT_BACKUP_DIR
    from core.backup import run_backup_task
    from core.i18n import tr

    sys_py = "/usr/bin/python3" if os.path.exists("/usr/bin/python3") else None
    if not sys_py:
        return False
    lng = engine.state.get("lang", "en")
    spec = [
        ("open", tr("Відкрити HomeGrid Backup", lng)), ("s1", None),
        ("status", _tray_status_text(engine, lng, 0)),
        ("backup", tr("▶ Запустити резервне копіювання", lng)),
        ("folder", tr("Відкрити папку", lng)), ("s2", None),
        ("stats", tr("Статистика", lng)), ("cstats", "☁ Статистика pCloud"),
        ("history", tr("Журнал операцій", lng)), ("analyze", tr("Аналіз GFS / SHA-256", lng)),
        ("settings", tr("Налаштування", lng)), ("s3", None), ("exit", tr("✖ Вихід", lng)),
    ]
    ico = get_app_icon_path() or "drive-harddisk"
    try:
        proc = subprocess.Popen(
            [sys_py, "-c", _SNI_HELPER, ico, json.dumps(spec, ensure_ascii=False)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1, env=_clean_sys_env()
        )
        if '"ready": true' not in proc.stdout.readline().lower():
            proc.terminate()
            return False
    except Exception:
        return False

    class _ProcTrayWrap:
        visible = True
        def stop(self):
            try:
                proc.stdin.write('{"quit":true}\n'); proc.stdin.flush(); proc.terminate()
            except Exception:
                pass

    engine.tray_icon = _ProcTrayWrap()
    engine.tray_ready = True
    engine.tray_error = ""
    if getattr(engine, "tray_ready_event", None):
        engine.tray_ready_event.set()
    engine.log("Активовано системний трей Wayland (AppIndicator bridge).", "info")

    def _dispatch(cmd):
        app = engine.app_ref
        if cmd == "exit":
            _force_quit_app(engine)
        elif cmd == "folder":
            open_folder_native(engine.state.get("backup_dir") or DEFAULT_BACKUP_DIR)
        elif cmd == "backup" and not engine.is_running:
            threading.Thread(target=run_backup_task, args=(engine, engine.state.get("server", ""), False, False, False), daemon=True).start()
        elif app is not None:
            acts = {
                "open": app.show_window,
                "stats": lambda: (app.show_window(), app.open_stats_modal()),
                "cstats": lambda: (app.show_window(), app.open_cloud_stats_modal()),
                "history": lambda: (app.show_window(), app.open_ops_history()),
                "analyze": lambda: (app.show_window(), app.open_analyze()),
                "settings": lambda: (app.show_window(), app.open_settings()),
            }
            if cmd in acts:
                _enqueue_tray_ui(acts[cmd])

    def _read_loop():
        for ln in proc.stdout:
            try:
                c = json.loads(ln).get("cmd")
                if c: _dispatch(c)
            except Exception:
                pass

    def _sync_loop():
        t0, last_st, last_run, last_send = None, "", None, 0.0
        while not _TRAY_STOP.is_set() and proc.poll() is None:
            _TRAY_STOP.wait(1.0)
            if not engine.is_running: t0 = None
            elif t0 is None: t0 = time.monotonic()
            sec = int(time.monotonic() - t0) if t0 else 0
            st_s = _tray_status_text(engine, engine.state.get("lang", "en"), sec)
            now_s = time.monotonic()
            if st_s != last_st or engine.is_running != last_run:
                if engine.is_running == last_run and (now_s - last_send) < 2.0:
                    continue
                try:
                    proc.stdin.write(json.dumps({"status": st_s, "running": bool(engine.is_running)}, ensure_ascii=False) + "\n")
                    proc.stdin.flush()
                    last_st, last_run, last_send = st_s, bool(engine.is_running), now_s
                except Exception:
                    break

    threading.Thread(target=_read_loop, daemon=True).start()
    threading.Thread(target=_sync_loop, daemon=True).start()
    return True


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
                import atexit
                atexit.register(lambda p=_port_p: os.path.exists(p) and os.remove(p))
                with open(_port_p, "w") as pf:
                    pf.write(str(srv.getsockname()[1]))
                while True:
                    conn, _ = srv.accept()
                    data = conn.recv(16)
                    conn.close()
                    if b"SHOW" in data and engine.app_ref is not None:
                        _enqueue_tray_ui(engine.app_ref.show_window)
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
