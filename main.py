#!/usr/bin/env python3
# ==========================================================================
# patch-id: crash-faulthandler-2.03
# patch-id: android-no-pip-install-2.02
# [ФАЙЛ: main.py (v2.03 | 23.11.2026 16:35) — ТОЧКА ВХОДА, MUTEX, CRASH-ЛОГ И ЛЕНИВЫЙ ЗАПУСК РЕЖИМОВ]
# ==============================================================================
import ctypes
import os
import subprocess
import sys

try:
    import faulthandler
    _crash_dir = os.path.join(os.path.expanduser("~"), ".backup_hgm")
    os.makedirs(_crash_dir, exist_ok=True)
    _crash_fp = open(os.path.join(_crash_dir, "crash.log"), "a", encoding="utf-8")
    faulthandler.enable(_crash_fp)
except Exception:
    pass

from core.config import IS_ANDROID
from core.scheduler import is_compiled_app

_APP_MUTEX = None
_SHOW_EVENT_NAME = "Global\\HomeGridBackup_ShowWindow_v1"
_IS_PY_CONSOLE_LAUNCHER = (
    not is_compiled_app()
    and sys.executable.lower().endswith("python.exe")
    and not any(a.lower() in ("--cli", "--console", "-c", "/console", "--silent", "-s", "/silent", "/s") for a in sys.argv[1:])
)

if not _IS_PY_CONSOLE_LAUNCHER:
    try:
        _k32 = ctypes.windll.kernel32
        _APP_MUTEX = _k32.CreateMutexW(None, True, "Global\\HomeGridBackup_SingleInstance_v1")
        if _k32.GetLastError() == 183:
            _h_ev = _k32.OpenEventW(0x0002, False, _SHOW_EVENT_NAME)
            if _h_ev:
                _k32.SetEvent(_h_ev)
                _k32.CloseHandle(_h_ev)
            os._exit(0)
    except Exception:
        pass
    if os.name != "nt":
        try:
            import fcntl
            import hashlib
            import socket
            import tempfile
            _inst_id = hashlib.md5(os.path.realpath(sys.argv[0]).encode("utf-8", errors="ignore")).hexdigest()[:10]
            _lock_p = os.path.join(tempfile.gettempdir(), f"hgb_inst_{_inst_id}.lock")
            _port_p = os.path.join(tempfile.gettempdir(), f"hgb_inst_{_inst_id}.port")
            _APP_MUTEX = open(_lock_p, "w")
            try:
                fcntl.flock(_APP_MUTEX.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                if os.path.exists(_port_p):
                    with open(_port_p, "r") as pf:
                        p_num = int(pf.read().strip() or "0")
                    if p_num > 0:
                        with socket.create_connection(("127.0.0.1", p_num), timeout=0.6) as sk:
                            sk.sendall(b"SHOW")
                os._exit(0)
        except Exception:
            pass

if not is_compiled_app() and not IS_ANDROID:
    _missing_pkgs = []
    for _mod, _pkg in (("send2trash", "send2trash"), ("keyring", "keyring"), ("pystray", "pystray"), ("PIL", "pillow")):
        try:
            __import__(_mod)
        except ImportError:
            _missing_pkgs.append(_pkg)
    if _missing_pkgs:
        print(f"[HomeGrid Backup] Устанавливаю недостающие пакеты: {', '.join(_missing_pkgs)} ...", flush=True)
        try:
            _res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user"] + _missing_pkgs,
                timeout=300,
            )
            if _res.returncode != 0:
                print(f"[HomeGrid Backup] Ошибка установки (код {_res.returncode}). Установите вручную: pip install {' '.join(_missing_pkgs)}", flush=True)
        except Exception as _e:
            print(f"[HomeGrid Backup] Не удалось установить пакеты: {_e}", flush=True)

from core.backup import run_backup_task
from core.config import CLI_MODE, GUI_MODE, HIDDEN_MODE, NO_CLEAN, SILENT_MODE
from core.engine import BackupEngine


def main():
    if (SILENT_MODE or CLI_MODE) and not HIDDEN_MODE:
        from console.terminal import _init_console_for_cli
        _init_console_for_cli()

    engine = BackupEngine()
    state = engine.state
    silent_skip_clean = bool(NO_CLEAN or not state.get("silent_cleanup", False))

    if CLI_MODE and not GUI_MODE:
        from console.terminal import _finish_cli_inline
        run_backup_task(engine, state.get("server", ""), False, NO_CLEAN, False)
        _finish_cli_inline(engine)
        sys.exit(engine.exit_code)

    if (SILENT_MODE or HIDDEN_MODE) and not GUI_MODE:
        if HIDDEN_MODE:
            from gui.tray import _force_quit_app, _start_tray_thread
            _start_tray_thread(engine)
            run_backup_task(engine, state.get("server", ""), True, silent_skip_clean, True)
            _force_quit_app(engine)
        else:
            from console.terminal import run_silent_exit_countdown
            run_backup_task(engine, state.get("server", ""), True, silent_skip_clean, False)
            run_silent_exit_countdown(engine, 8)
            os._exit(engine.exit_code)
        return

    if IS_ANDROID:
        from mobile.android_app import run_android_ui
        run_android_ui(engine)
        return

    import tkinter as tk

    from gui.tray import _start_show_window_listener, _start_tray_thread
    from gui.window import HomeGridApp

    # DPI-awareness нужно включать ДО создания первого окна Tk
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    root = tk.Tk(className="HomeGridBackup")
    app = HomeGridApp(root, engine)
    engine.app_ref = app
    _start_show_window_listener(engine, _SHOW_EVENT_NAME)
    _start_tray_thread(engine)
    root.mainloop()

if __name__ == "__main__":
    main()
