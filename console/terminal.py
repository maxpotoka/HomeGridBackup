# ==============================================================================
# patch-id: stage-window-2.21
# [ФАЙЛ: console/terminal.py (v2.02 | 22.11.2026 09:10) — ВЫВОД В КОНСОЛЬ WINDOWS 7/10/11]
# ==============================================================================
import os
import re
import sys
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
from core.config import SCRIPT_VER, BUILD_DATE, HIDDEN_MODE, SILENT_MODE, CLI_MODE

_STAGE_TR_MAP = (
    ("Обробка на сервері", "Processing on server"),
    ("Перевірка сайту та сервера HGM...", "Checking HGM host and server..."),
    ("Перевірка сесії та авторизація...", "Checking session and auth..."),
    ("Запит на підготовку бекапу...", "Requesting backup preparation..."),
    ("Підготовка на сервері", "Preparing on server"),
    ("Копіювання бази та файлів", "Copying DB & files"),
    ("Перевірка файлів", "Checking files"),
    ("Стиснення ZIP-архіву", "Packing ZIP"),
    ("Архів готовий (75%). Завантаження...", "Archive ready (75%). Downloading..."),
    ("Архів готовий", "Archive ready"),
    ("Обробка", "Processing"),
    ("Збірка архіву на сервері", "Building archive on server"),
    ("Етап сервера", "Server stage"),
    ("Сервер HGM онлайн", "HGM server online"),
    ("Сервер http", "Server http"),
    ("Сервер ", "Server "),
    ("Завантаження", "Downloading"),
    ("Швидкість:", "Speed:"),
    ("МБ/с", "MB/s"),
    ("КБ/с", "KB/s"),
    ("МБ", "MB"),
    ("Перевірка CRC32", "Verifying CRC32"),
    ("Розрахунок SHA-256:", "Calculating SHA-256:"),
    ("Старі копії збережено (авторежим без видалення)...", "Old backups kept (no-clean mode)..."),
    ("Ротація бекапів за обраною стратегією...", "Running GFS backup rotation..."),
    ("Готово! Архів збережено", "Done! Archive saved"),
    ("Помилка:", "Error:"),
)

def _stage_to_en(txt):
    s = re.sub(r"^\[[^\]]+\]\s*", "", (txt or "").strip())
    for uk, en in _STAGE_TR_MAP:
        s = s.replace(uk, en)
    return s

def _safe_con_write(text):
    if not text:
        return
    if os.name == "nt":
        try:
            k32 = ctypes.windll.kernel32
            h_out = k32.GetStdHandle(-11)
            if h_out and h_out != -1 and h_out != 0:
                written = wintypes.DWORD(0)
                if k32.WriteConsoleW(h_out, ctypes.c_wchar_p(text), len(text), ctypes.byref(written), None):
                    return
        except Exception:
            pass
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except Exception:
        try:
            enc = getattr(sys.stdout, "encoding", None) or "cp866"
            sys.stdout.write(text.encode(enc, errors="replace").decode(enc, errors="replace"))
            sys.stdout.flush()
        except Exception:
            pass

def _print_cli_banner():
    from core.config import get_fast_sysinfo
    sys_line = get_fast_sysinfo()
    title_line = f"  HomeGrid Backup v{SCRIPT_VER} ({BUILD_DATE}) - Inverter Data Backup"
    os_line = f"  {sys_line}"[:76]
    _safe_con_write("+" + ("-" * 76) + "+\n")
    _safe_con_write("|" + title_line.ljust(76) + "|\n")
    _safe_con_write("|" + os_line.ljust(76) + "|\n")
    _safe_con_write("+" + ("-" * 76) + "+\n")

def _init_console_for_cli():
    if os.name != "nt":
        try:
            if sys.stdout.isatty():
                _safe_con_write(f"\033]0;HomeGrid Backup v{SCRIPT_VER}\007")
        except Exception:
            pass
        _print_cli_banner()
        return
    try:
        k32 = ctypes.windll.kernel32
        if k32.GetConsoleWindow() == 0:
            if not k32.AttachConsole(-1):
                k32.AllocConsole()
        try:
            k32.SetConsoleOutputCP(65001)
            k32.SetConsoleCP(65001)
            k32.SetConsoleTitleW(f"HomeGrid Backup v{SCRIPT_VER} ({BUILD_DATE}) - Inverter Data Backup")
        except Exception:
            pass
        try:
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
            sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
        except Exception:
            pass
        _print_cli_banner()
    except Exception:
        pass

def _print_cli_line(engine, force=False):
    if HIDDEN_MODE or not (CLI_MODE or SILENT_MODE):
        return
    now = time.time()
    if not force and (now - engine._last_cli_print) < 1.0:
        return
    engine._last_cli_print = now

    st_txt = _stage_to_en(engine.stage)
    if engine.indeterminate:
        bar = "[  working...  ]"
        pct_s = " ..."
    else:
        p = max(0, min(100, int(engine.progress)))
        filled = int(round((p / 100.0) * 16))
        bar = "[" + ("#" * filled) + ("." * (16 - filled)) + "]"
        pct_s = f"{p:3d}%"

    max_st = 54
    if len(st_txt) > max_st:
        st_txt = st_txt[:max_st - 3] + "..."
    raw_line = f"{bar} {pct_s} | {st_txt}"

    if SILENT_MODE and not CLI_MODE:
        _safe_con_write("\r" + raw_line[:78].ljust(78))
        engine._cli_inline_active = True
    else:
        ts = datetime.now().strftime("%H:%M:%S")
        _safe_con_write(f"[{ts}] {raw_line}\n")

def _finish_cli_inline(engine):
    if getattr(engine, "_cli_inline_active", False):
        _safe_con_write("\r" + (" " * 78) + "\r")
        engine._cli_inline_active = False

def run_silent_exit_countdown(engine, total_sec=8):
    if HIDDEN_MODE or not SILENT_MODE:
        return
    _finish_cli_inline(engine)
    _safe_con_write("-" * 78 + "\n")
    for rem in range(total_sec, 0, -1):
        msg = f"[OK] Done! Window will close automatically in {rem}s..."
        _safe_con_write("\r" + msg.ljust(78))
        time.sleep(1.0)
    _safe_con_write("\r" + (" " * 78) + "\r")
