#!/usr/bin/env python3
# ==============================================================================
# [ФАЙЛ: main.py (v1.50) — ТОЧКА ВХОДА, MUTEX И ЛЕНИВЫЙ ЗАПУСК РЕЖИМОВ]
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

from core.config import GUI_MODE, HIDDEN_MODE, SILENT_MODE, CLI_MODE, NO_CLEAN
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

    import tkinter as tk
    from gui.window import HomeGridApp
    from gui.tray import _start_tray_thread, _start_show_window_listener

    root = tk.Tk()
    app = HomeGridApp(root, engine)
    engine.app_ref = app
    _start_show_window_listener(engine, _SHOW_EVENT_NAME)
    _start_tray_thread(engine)
    root.mainloop()

if __name__ == "__main__":
    main()
