#!/usr/bin/env python3
# ==============================================================================
# [ФАЙЛ: main.py (v1.130 | 20.11.2026 15:52) — ТОЧКА ВХОДА, MUTEX И ЛЕНИВЫЙ ЗАПУСК РЕЖИМОВ]
# ==============================================================================
import os
import sys
import ctypes
import subprocess
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
            import fcntl, hashlib, socket, tempfile
            _inst_id = hashlib.md5(os.path.realpath(sys.argv[0]).encode("utf-8", errors="ignore")).hexdigest()[:10]
            _lock_p = os.path.join(tempfile.gettempdir(), f"hgb_inst_{_inst_id}.lock")
            _port_p = os.path.join(tempfile.gettempdir(), f"hgb_inst_{_inst_id}.port")
            _APP_MUTEX = open(_lock_p, "w")
            try:
                fcntl.flock(_APP_MUTEX.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError):
                if os.path.exists(_port_p):
                    with open(_port_p, "r") as pf:
                        p_num = int(pf.read().strip() or "0")
                    if p_num > 0:
                        with socket.create_connection(("127.0.0.1", p_num), timeout=0.6) as sk:
                            sk.sendall(b"SHOW")
                os._exit(0)
        except Exception:
            pass

if not is_compiled_app():
    _missing_pkgs = []
    for _mod, _pkg in (("send2trash", "send2trash"), ("keyring", "keyring"), ("pystray", "pystray"), ("PIL", "pillow")):
        try:
            __import__(_mod)
        except ImportError:
            _missing_pkgs.append(_pkg)
    if _missing_pkgs:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "--quiet"] + _missing_pkgs,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=90,
            )
        except Exception:
            pass

from core.config import GUI_MODE, HIDDEN_MODE, SILENT_MODE, CLI_MODE, NO_CLEAN, IS_ANDROID
from core.engine import BackupEngine
from core.backup import run_backup_task

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
            from gui.tray import _start_tray_thread, _force_quit_app
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
    from gui.window import HomeGridApp
    from gui.tray import _start_tray_thread, _start_show_window_listener

    # DPI-awareness нужно включать ДО создания первого окна Tk
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    root = tk.Tk()
    app = HomeGridApp(root, engine)
    engine.app_ref = app
    _start_show_window_listener(engine, _SHOW_EVENT_NAME)
    _start_tray_thread(engine)
    root.mainloop()

if __name__ == "__main__":
    main()
