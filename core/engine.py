# ==============================================================================
# [ФАЙЛ: core/engine.py (v1.017 | 18.11.2026 19:50) — ЯДРО ДВИЖКА BACKUPENGINE]
# ==============================================================================
import os
import re
import time
import shutil
import getpass
import threading
from datetime import datetime
from core.config import (
    SCRIPT_VER, BUILD_DATE, HIDDEN_MODE, SILENT_MODE, CLI_MODE, NO_CLEAN,
    load_state, write_file_log, get_fast_sysinfo
)

_CON_TR_MAP = (
    ("Систему запущено", "System started"),
    ("сховище:", "storage:"),
    ("Каталог:", "Dir:"),
    ("Перевірку сайту/порту пропущено для", "Host/port check skipped for"),
    ("Сервер HGM онлайн", "HGM server online"),
    ("Активну сесію підтверджено.", "Active session confirmed."),
    ("Збережена сесія застаріла. Повторний вхід...", "Saved session expired. Re-login..."),
    ("Авторизація успішна!", "Authorization successful!"),
    ("Авторизацію підтверджено сервером!", "Authorization confirmed by server!"),
    ("Збірка архіву на сервері", "Building archive on server"),
    ("Етап сервера", "Server stage"),
    ("Копіювання бази та файлів", "Copying database and files"),
    ("Перевірка файлів", "Checking files"),
    ("Стиснення ZIP-архіву", "Packing ZIP archive"),
    ("Підготовка на сервері", "Preparing on server"),
    ("Архів готовий", "Archive ready"),
    ("Завантаження ZIP-архіву з", "Downloading ZIP archive from"),
    ("Архів завантажено:", "Archive downloaded:"),
    ("Цілісність перевірено", "Integrity verified"),
    ("файлів", "files"),
    ("файл(ів)", "file(s)"),
    ("Збережено", "Saved"),
    ("Дзеркальну копію збережено у:", "Mirror copy saved to:"),
    ("Попередження: не вдалося скопіювати у дзеркальну папку", "Warning: failed to copy to mirror dir"),
    ("Налаштування та ключі захищено збережено.", "Settings and keys securely saved."),
    ("Режим збереження: очищення застарілих архівів пропущено.", "Keep mode: old archive cleanup skipped."),
    ("Переміщено у Кошик:", "Moved to Recycle Bin:"),
    ("Видалено з диска назавжди:", "Deleted permanently:"),
    ("Очищення застарілих архівів пропущено.", "Old archive cleanup skipped."),
    ("УСПІХ! Резервне копіювання завершено за", "SUCCESS! Backup completed in"),
    ("ПОМИЛКА:", "ERROR:"),
    ("Адресу не вказано. Запуск автопошуку в LAN...", "Address empty. Starting LAN auto-scan..."),
    ("Сканування підмереж:", "Scanning subnets:"),
    ("Активні мережеві адаптери LAN не знайдено!", "No active LAN network adapters found!"),
    ("Автоматично обрано сервер:", "Auto-selected server:"),
    ("Сервер скинув завдання. Повторний запуск збірки...", "Server reset job. Restarting build..."),
    ("Збій завантаження", "Download failed"),
    ("завантажено лише", "downloaded only"),
    ("обрив потоку", "stream interrupted"),
    ("Повтор", "Retry"),
    ("через", "in"),
    ("ICMP Ping до", "ICMP Ping to"),
    ("без відповіді, перевірка з'єднання", "no reply, checking connection"),
)

_CON_TR_SORTED = sorted(_CON_TR_MAP, key=lambda x: len(x), reverse=True)

def _to_con_en(txt):
    s = str(txt)
    for uk, en in _CON_TR_SORTED:
        s = s.replace(uk, en)
    s = re.sub(r"\bМБ/с\b", "MB/s", s)
    s = re.sub(r"\bКБ/с\b", "KB/s", s)
    s = re.sub(r"\bМБ\b", "MB", s)
    s = re.sub(r"\bмс\b", "ms", s)
    s = re.sub(r"(?<=\d)\s*с(?=\b|\.)", " s", s)
    s = re.sub(r"\bза\s+(?=\d)", "in ", s)
    s = re.sub(r"\bіз\s+(?=\d)", "of ", s)
    return s

class BackupEngine:
    def __init__(self):
        self.state = load_state()
        self.lock = threading.Lock()
        self.is_running = False
        self.show_hw_notice = bool(self.state.get("hw_auto_notice"))
        self.progress = 0
        self.indeterminate = False
        self.sys_summary = get_fast_sysinfo()
        self.stage = "Готовий до резервного копіювання"
        self.pill_text = f"v{SCRIPT_VER} | {BUILD_DATE}"
        self.pill_type = "idle"
        self.op_history = list(self.state.get("op_history") or [])
        self.diag_net = "Не перевірено"
        self.diag_ping = "— мс"
        self.logs = []
        self.modal = None
        self.modal_event = threading.Event()
        self.modal_result = None
        self.exit_code = 0
        self.tray_icon = None
        self.tray_spin_idx = 0
        self.app_ref = None
        self._last_cli_print = 0.0
        self._cli_inline_active = False
        self._storage_stats_cache = None
        self._storage_stats_cache_time = 0.0
        self._storage_stats_cache_dir = None

        os.makedirs(self.state["backup_dir"], exist_ok=True)
        mode_lbl = "HIDDEN" if HIDDEN_MODE else ("SILENT" if SILENT_MODE else ("CLI" if CLI_MODE else "APP"))
        sec_lbl = "Keyring" if self.state["storage_backend"] == "keyring" else ".env"
        self.log(f"Систему запущено (v{SCRIPT_VER} від {BUILD_DATE}, {mode_lbl}, сховище: {sec_lbl}). Каталог: {self.state['backup_dir']}", "info")
        self.log(f"ОС та залізо: {self.sys_summary}", "info")

    def log(self, msg, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        write_file_log(f"[{level.upper()}] {msg}", self.state.get("backup_dir"))
        if CLI_MODE or (SILENT_MODE and not HIDDEN_MODE):
            from console.terminal import _finish_cli_inline, _safe_con_write
            _finish_cli_inline(self)
            tot_p = max(0, min(100, int(self.progress)))
            _safe_con_write(f"[{ts}] ({tot_p:3d}%) {_to_con_en(msg)}\n")
        with self.lock:
            self.logs.append({"ts": ts, "msg": msg, "level": level})
            if len(self.logs) > 400:
                self.logs = self.logs[-400:]

    def set_progress(self, pct, stage_text=None):
        with self.lock:
            if pct is None:
                self.indeterminate = True
            else:
                self.indeterminate = False
                self.progress = max(0, min(100, int(pct)))
            if stage_text is not None:
                self.stage = stage_text
        if not HIDDEN_MODE and (CLI_MODE or SILENT_MODE):
            from console.terminal import _print_cli_line
            _print_cli_line(self)

    def set_pill(self, text, state_type="idle"):
        with self.lock:
            self.pill_text = text
            self.pill_type = state_type

    def ask_modal(self, mtype, title, text, default_val=""):
        if SILENT_MODE:
            return (not NO_CLEAN) if mtype == "confirm" else ""
        if CLI_MODE:
            from console.terminal import _finish_cli_inline
            _finish_cli_inline(self)
            if mtype == "pin":
                return getpass.getpass(f"[{title}] Enter PIN: ").strip()
            elif mtype == "confirm":
                ans = input(f"[{title}] Confirm? [y/N]: ").strip().lower()
                return ans in ("y", "yes", "так", "д")
            return ""
        self.modal_event.clear()
        self.modal_result = None
        with self.lock:
            self.modal = {"id": int(time.time() * 1000), "type": mtype, "title": title, "text": text, "default": default_val}
        self.modal_event.wait()
        return self.modal_result

    def submit_modal(self, val):
        with self.lock:
            self.modal = None
        self.modal_result = val
        self.modal_event.set()

    def get_storage_stats(self, force=False):
        bdir = self.state["backup_dir"]
        now = time.time()
        cache_valid = (
            not force
            and self._storage_stats_cache is not None
            and self._storage_stats_cache_dir == bdir
            and (now - self._storage_stats_cache_time) < 8.0
        )
        if cache_valid:
            return self._storage_stats_cache
        os.makedirs(bdir, exist_ok=True)
        zips = [os.path.join(bdir, f) for f in os.listdir(bdir) if not f.startswith(".") and f.lower().endswith(".zip")]
        total_mb = round(sum(os.path.getsize(p) for p in zips) / 1048576.0, 1)
        try:
            _, _, free_b = shutil.disk_usage(bdir)
            free_gb = round(free_b / 1073741824.0, 1)
        except Exception:
            free_gb = -1.0
        result = (len(zips), total_mb, free_gb)
        self._storage_stats_cache = result
        self._storage_stats_cache_time = now
        self._storage_stats_cache_dir = bdir
        return result

    def record_op_event(self, status_lbl, detail_txt, size_mb=0.0):
        from datetime import datetime
        from core.config import commit_state
        entry = {
            "ts": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "status": status_lbl,
            "detail": detail_txt,
            "size_mb": round(float(size_mb), 1)
        }
        if not hasattr(self, "op_history"):
            self.op_history = list(self.state.get("op_history") or [])
        self.op_history.insert(0, entry)
        self.op_history = self.op_history[:25]
        self.state["op_history"] = self.op_history
        try:
            commit_state(self.state)
        except Exception:
            pass

    def get_last_backup_info(self):
        from datetime import datetime
        bdir = self.state.get("backup_dir", "")
        if not bdir or not os.path.isdir(bdir):
            return "Ще немає створених копій", "idle"
        try:
            zips = [
                os.path.join(bdir, f) for f in os.listdir(bdir)
                if not f.startswith(".") and f.lower().endswith(".zip") and os.path.isfile(os.path.join(bdir, f))
            ]
            if not zips:
                return "Ще немає створених копій", "idle"
            latest = max(zips, key=os.path.getmtime)
            st = os.stat(latest)
            dt_s = datetime.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y о %H:%M")
            mb_s = round(st.st_size / 1048576.0, 1)
            has_sha = os.path.exists(latest + ".sha256")
            if has_sha:
                return f"{dt_s}  •  {mb_s} МБ  •  SHA-256 ✔", "ok"
            return f"{dt_s}  •  {mb_s} МБ  •  Без .sha256", "warn"
        except Exception:
            return "Невідомо", "idle"

    def record_op_event(self, status_lbl, detail_txt, size_mb=0.0):
        from datetime import datetime
        from core.config import commit_state
        entry = {
            "ts": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "status": status_lbl,
            "detail": detail_txt,
            "size_mb": round(float(size_mb), 1)
        }
        if not hasattr(self, "op_history"):
            self.op_history = list(self.state.get("op_history") or [])
        self.op_history.insert(0, entry)
        self.op_history = self.op_history[:25]
        self.state["op_history"] = self.op_history
        try:
            commit_state(self.state)
        except Exception:
            pass

    def get_last_backup_info(self):
        from datetime import datetime
        bdir = self.state.get("backup_dir", "")
        if not bdir or not os.path.isdir(bdir):
            return "Ще немає створених копій", "idle"
        try:
            zips = [
                os.path.join(bdir, f) for f in os.listdir(bdir)
                if not f.startswith(".") and f.lower().endswith(".zip") and os.path.isfile(os.path.join(bdir, f))
            ]
            if not zips:
                return "Ще немає створених копій", "idle"
            latest = max(zips, key=os.path.getmtime)
            st = os.stat(latest)
            dt_s = datetime.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y о %H:%M")
            mb_s = round(st.st_size / 1048576.0, 1)
            has_sha = os.path.exists(latest + ".sha256")
            if has_sha:
                return f"{dt_s}  •  {mb_s} МБ  •  SHA-256 ✔", "ok"
            return f"{dt_s}  •  {mb_s} МБ  •  Без .sha256", "warn"
        except Exception:
            return "Невідомо", "idle"

