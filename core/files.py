# ==============================================================================
# [ФАЙЛ: core/files.py (v1.002 | 18.11.2026 17:14) — ФАЙЛОВЫЕ УТИЛИТЫ WINDOWS (КОРЗИНА, ПАПКИ, ДАТЫ)]
# ==============================================================================
import os
import re
import shutil
from datetime import datetime

try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

def pretty_phase(ph):
    return {
        "copying": "Копіювання бази та файлів",
        "checking": "Перевірка файлів",
        "packing": "Стиснення ZIP-архіву",
        "preparing": "Підготовка на сервері",
        "ready": "Архів готовий",
    }.get(ph, "Обробка")

def send_to_recycle_bin(filepath):
    abs_path = os.path.abspath(filepath)
    if send2trash is not None:
        try:
            send2trash(abs_path)
            return True
        except Exception:
            pass
    try:
        trash_dir = os.path.join(os.path.dirname(abs_path), ".trash_hgm")
        os.makedirs(trash_dir, exist_ok=True)
        shutil.move(abs_path, os.path.join(trash_dir, os.path.basename(abs_path)))
        return True
    except Exception:
        return False

def remove_backup_file(filepath, delete_mode="trash"):
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        return True
    if delete_mode in ("direct", "permanent"):
        try:
            os.remove(abs_path)
            return True
        except Exception:
            return False
    return send_to_recycle_bin(abs_path)

def _open_path_os(target_path):
    import sys
    import subprocess
    if os.name == "nt":
        os.startfile(target_path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target_path])
    else:
        subprocess.Popen(["xdg-open", target_path])

def open_folder_native(folder_path):
    os.makedirs(folder_path, exist_ok=True)
    try:
        _open_path_os(folder_path)
        return True
    except Exception:
        return False

def open_file_native(file_path):
    parent = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(parent, exist_ok=True)
    if not os.path.exists(file_path):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass
    try:
        _open_path_os(file_path)
        return True
    except Exception:
        return False

def choose_folder_native(initial_dir):
    try:
        from tkinter import filedialog
        chosen = filedialog.askdirectory(initialdir=initial_dir, title="Оберіть папку")
        return os.path.normpath(chosen) if chosen else ""
    except Exception:
        return ""

def parse_backup_dt(filename, fallback_ts):
    for pattern, fmt in (
        (r"(\d{4}-\d{2}-\d{2}_[A-Za-z]+_\d{2}-\d{2})", "%Y-%m-%d_%A_%H-%M"),
        (r"(\d{4}-[A-Za-z]+-\d{2}_[A-Za-z]+_\d{2}-\d{2})", "%Y-%B-%d_%A_%H-%M"),
    ):
        m = re.search(pattern, filename)
        if m:
            try:
                return datetime.strptime(m.group(1), fmt)
            except Exception:
                pass
    return datetime.fromtimestamp(fallback_ts)
