# ==============================================================================
# [ФАЙЛ: core/files.py (v2.06 | 21.11.2026 07:34) — ФАЙЛОВЫЕ УТИЛИТЫ WINDOWS (КОРЗИНА, ПАПКИ, ДАТЫ)]
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

def choose_folder_native(initial_dir, lang="en"):
    import sys, subprocess
    from core.i18n import tr
    dlg_t = tr("Оберіть папку", lang)
    if sys.platform.startswith("linux"):
        start_d = (initial_dir.rstrip("/") + "/") if initial_dir and os.path.isdir(initial_dir) else os.path.expanduser("~/")
        de = (os.environ.get("XDG_CURRENT_DESKTOP") or "").upper()
        tools = [("kdialog", ["kdialog", "--getexistingdirectory", start_d, "--title", dlg_t]),
                 ("zenity", ["zenity", "--file-selection", "--directory", f"--title={dlg_t}", f"--filename={start_d}"])]
        if not any(k in de for k in ("KDE", "LXQT")):
            tools.reverse()
        for bin_name, cmd in tools:
            if shutil.which(bin_name):
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    if res.returncode == 0 and res.stdout.strip():
                        return os.path.normpath(res.stdout.strip())
                    if res.returncode == 1:
                        return ""
                except Exception:
                    pass
    try:
        from tkinter import filedialog
        chosen = filedialog.askdirectory(initialdir=initial_dir, title=dlg_t)
        return os.path.normpath(chosen) if chosen else ""
    except Exception:
        return ""

_ENG_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_ENG_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")

def format_backup_dt(dt):
    wday = _ENG_WEEKDAYS[dt.weekday()]
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{wday}_{dt.hour:02d}-{dt.minute:02d}"

def parse_backup_dt(filename, fallback_ts):
    m_num = re.search(r"(\d{4})-(\d{2})-(\d{2})_[^_]+_(\d{2})-(\d{2})", filename)
    if m_num:
        try:
            y, mo, d, hh, mm = (int(x) for x in m_num.groups())
            return datetime(y, mo, d, hh, mm)
        except Exception:
            pass
    m_mon = re.search(r"(\d{4})-([A-Za-z]+)-(\d{2})_[^_]+_(\d{2})-(\d{2})", filename)
    if m_mon:
        try:
            y_s, mon_s, d_s, hh_s, mm_s = m_mon.groups()
            mon_idx = next((i + 1 for i, nm in enumerate(_ENG_MONTHS) if nm.lower() == mon_s.lower()), 0)
            if mon_idx:
                return datetime(int(y_s), mon_idx, int(d_s), int(hh_s), int(mm_s))
        except Exception:
            pass
    return datetime.fromtimestamp(fallback_ts)

def format_duration(sec, lang="uk"):
    raw = max(0.0, float(sec or 0.0))
    s = 1 if raw < 1.0 else int(round(raw))
    if s < 60:
        return f"{s} с" if lang == "uk" else f"{s} s"
    mins, rem = divmod(s, 60)
    return f"{mins} хв {rem} с ({s} с)" if lang == "uk" else f"{mins}m {rem}s ({s}s)"

def get_app_icon_path():
    import sys
    cands = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.ico"),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "icon.ico"),
        os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "icon.ico"),
        os.path.join(getattr(sys, "_MEIPASS", ""), "icon.ico"),
        os.path.join(os.getcwd(), "icon.ico"),
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return ""
