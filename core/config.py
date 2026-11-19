# ==============================================================================
# [ФАЙЛ: core/config.py (v1.038 | 19.11.2026 06:01) — КОНФИГУРАЦИЯ, СЕКРЕТЫ KEYRING/.ENV И ЛОГИРОВАНИЕ]
# ==============================================================================
import os
import re
import sys
import json
import platform

try:
    import keyring
    KEYRING_SERVICE = "HomeGridMonitorBackup"
    keyring.get_keyring()
    HAS_KEYRING = True
except Exception:
    keyring = None
    KEYRING_SERVICE = "HomeGridMonitorBackup"
    HAS_KEYRING = False

SCRIPT_VER = "1.038"
BUILD_DATE = "19.11.2026 06:01"
DEFAULT_TOK = "pK5hquN9wdrSgIr55FR0WyL16qnpC_cEf1Y6jUjyd14"

IS_ANDROID = ("ANDROID_ARGUMENT" in os.environ) or ("ANDROID_ROOT" in os.environ) or os.path.exists("/system/build.prop")
if IS_ANDROID:
    _and_dl = "/storage/emulated/0/Download"
    _and_base = _and_dl if os.path.isdir(_and_dl) else os.path.expanduser("~")
    DEFAULT_BACKUP_DIR = os.path.join(_and_base, "BackupHGM")
    SECURE_DIR = os.path.join(os.path.expanduser("~"), ".backup_hgm")
else:
    DEFAULT_BACKUP_DIR = os.path.join(os.path.expanduser("~"), "BackupHGM")
    SECURE_DIR = os.path.join(os.path.expanduser("~"), ".backup_hgm")
CFG_FILE = os.path.join(SECURE_DIR, "config.json")
ENV_FILE = os.path.join(SECURE_DIR, ".env")

ARGS_LOW = [a.lower() for a in sys.argv[1:]]
GUI_MODE = any(a in ("--gui", "/gui") for a in ARGS_LOW)
HIDDEN_MODE = any(a in ("--hidden", "--background", "/hidden", "/h") for a in ARGS_LOW)
SILENT_MODE = HIDDEN_MODE or any(a in ("--silent", "-s", "/silent", "/s") for a in ARGS_LOW)
CLI_MODE = any(a in ("--cli", "--console", "-c", "/console") for a in ARGS_LOW)
NO_CLEAN = any(a in ("--no-clean", "/noclean") for a in ARGS_LOW)

SECRET_KEYS = ("client_token", "session_token", "login_pin", "editor_pin")
SCHED_TASK_NAME = "HomeGridBackup"

VALID_PBAR_STYLES = (
    "v8", "amber_pro", "emerald_pro", "s_20s_macos", "classic",
    "s_00s_win7", "s_00s_aqua", "s_00s_winxp",
    "s_90s_win95", "s_80s_mac1", "s_80s_dos", "s_70s_crt", "s_60s_tty",
    "digits_only"
)
VALID_THEMES = ("crt", "norton", "mac_classic", "win95", "winxp", "mac_aqua", "win7", "mac_light", "mac_dark", "dark", "light")
VALID_SCALES = ("auto", "800x600", "1024x600", "1024x768", "1280x720", "1366x768", "1600x900", "1920x1080", "2560x1440")

def get_fast_sysinfo():
    import struct
    arch_os = "64-bit" if (os.environ.get("PROCESSOR_ARCHITEW6432") or "64" in platform.machine() or struct.calcsize("P") == 8) else "32-bit"
    app_bits = f"{struct.calcsize('P') * 8}-bit"
    cpu_name = ""
    os_label = f"{platform.system()} {platform.release()}"

    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                cpu_name = str(winreg.QueryValueEx(k, "ProcessorNameString")[0]).strip()
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as k:
                prod = str(winreg.QueryValueEx(k, "ProductName")[0]).strip()
                build = str(winreg.QueryValueEx(k, "CurrentBuild")[0]).strip()
                disp_ver = ""
                for val_name in ("DisplayVersion", "ReleaseId", "CSDVersion"):
                    try:
                        v = str(winreg.QueryValueEx(k, val_name)[0]).strip()
                        if v:
                            disp_ver = v
                            break
                    except Exception:
                        pass
                if build.isdigit() and int(build) >= 22000 and "Windows 10" in prod:
                    prod = prod.replace("Windows 10", "Windows 11")
                code_part = f" {disp_ver}" if disp_ver else ""
                os_label = f"{prod}{code_part} (Build {build})"
        except Exception:
            pass
    elif IS_ANDROID:
        try:
            import subprocess
            rel = subprocess.check_output(["getprop", "ro.build.version.release"], timeout=0.4).decode().strip()
            sdk = subprocess.check_output(["getprop", "ro.build.version.sdk"], timeout=0.4).decode().strip()
            model = subprocess.check_output(["getprop", "ro.product.model"], timeout=0.4).decode().strip()
            os_label = f"Android {rel} (API {sdk})"
            if model:
                cpu_name = f"{model} ({platform.machine()})"
        except Exception:
            os_label = "Android OS"
    elif sys.platform == "darwin":
        mac_v = (platform.mac_ver()[0] if platform.mac_ver() else "")
        mac_names = {"15": "Sequoia", "14": "Sonoma", "13": "Ventura", "12": "Monterey", "11": "Big Sur"}
        maj = mac_v.split(".")[0] if mac_v else ""
        cname = f" ({mac_names[maj]})" if maj in mac_names else ""
        os_label = f"macOS {mac_v}{cname}"
        try:
            import subprocess
            out = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], timeout=0.4).decode().strip()
            if out:
                cpu_name = out
        except Exception:
            pass

    elif sys.platform.startswith("linux"):
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r", encoding="utf-8") as f_os:
                    for ln in f_os:
                        if ln.startswith("PRETTY_NAME="):
                            os_label = ln.split("=", 1)[1].strip().strip('"')
                            break
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r", encoding="utf-8") as f_cpu:
                    for ln in f_cpu:
                        if ln.lower().startswith("model name") and ":" in ln:
                            cpu_name = ln.split(":", 1)[1].strip()
                            break
        except Exception:
            pass

    if not cpu_name:
        cpu_name = (platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER") or platform.machine() or "Unknown CPU").strip()
    cpu_name = re.sub(r"\s+", " ", cpu_name).replace("(R)", "").replace("(TM)", "").replace("CPU ", "").strip()
    if len(cpu_name) > 42:
        cpu_name = cpu_name[:39] + "..."
    return f"{os_label} [{arch_os}, app {app_bits}] | CPU: {cpu_name}"

def _detect_low_end_or_win7():
    try:
        v = sys.getwindowsversion()
        if v.major == 6 and v.minor <= 1:
            return True, "Windows 7 або старіша ОС"
        cpu_str = " ".join([
            platform.processor() or "",
            os.environ.get("PROCESSOR_IDENTIFIER", ""),
        ]).lower()
        if any(k in cpu_str for k in ("atom", "celeron", "pentium", "geode", "via ")):
            return True, "енергоефективний процесор (Intel Atom / Celeron)"
        if (os.cpu_count() or 4) <= 2:
            return True, "2 або менше потоків процесора"
    except Exception:
        pass
    return False, ""

def _ensure_secure_dir():
    os.makedirs(SECURE_DIR, exist_ok=True)

def _read_env_secrets():
    secrets = {}
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k_low = k.strip().lower()
                    if k_low in SECRET_KEYS:
                        secrets[k_low] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return secrets

def _write_env_secrets(state):
    _ensure_secure_dir()
    tmp_env = ENV_FILE + ".tmp"
    lines = [
        "# HomeGrid Backup — захищені токени та PIN-коди",
        f"CLIENT_TOKEN={state.get('client_token', '')}",
        f"SESSION_TOKEN={state.get('session_token', '')}",
        f"LOGIN_PIN={state.get('login_pin', '')}",
        f"EDITOR_PIN={state.get('editor_pin', '')}",
    ]
    with open(tmp_env, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp_env, ENV_FILE)

def write_file_log(text, target_dir=None):
    from datetime import datetime
    try:
        d = target_dir or DEFAULT_BACKUP_DIR
        os.makedirs(d, exist_ok=True)
        log_path = os.path.join(d, "backup.log")
        if os.path.exists(log_path) and os.path.getsize(log_path) > 2 * 1024 * 1024:
            try:
                with open(log_path, "rb") as f_old:
                    f_old.seek(-512 * 1024, os.SEEK_END)
                    tail = f_old.read().decode("utf-8", errors="replace")
                cut = tail.find("\n")
                if cut != -1:
                    tail = tail[cut + 1:]
                with open(log_path, "w", encoding="utf-8") as f_new:
                    f_new.write("[Лог автоматично скорочено при перевищенні 2 МБ]\n" + tail)
            except Exception:
                pass
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {text}\n")
    except Exception:
        pass

def record_server_history(state, srv_url):
    u = (srv_url or "").strip().rstrip("/")
    if not u:
        return
    hist = [x for x in (state.get("server_history") or []) if isinstance(x, str) and x.strip() and x.strip().rstrip("/") != u]
    hist.insert(0, u)
    state["server_history"] = hist[:15]

def load_state():
    state = {
        "server": "", "server_history": [], "op_history": [], "client_token": "", "session_token": "",
        "login_pin": "", "editor_pin": "", "backup_dir": DEFAULT_BACKUP_DIR,
        "mirror_dir": "", "mirror_enabled": True, "daily_days": 7, "today_max": 2,
        "weekly_count": 4, "monthly_count": 12, "yearly_count": 3, "delete_mode": "trash",
        "lang": "en", "theme": "dark", "ui_scale": "auto", "ui_font": 0, "minimize_to_tray": True,
        "lite_mode": False, "hw_checked": False, "hw_auto_notice": "",
        "progress_style": "v8", "silent_sec_digits": True, "silent_cleanup": False,
        "sched_time": "03:00", "sched_mode": "--hidden", "sched_missed": True,
        "sched_wake": False, "sched_prio": 6, "storage_backend": "none", "dirty": False,
    }
    old_cfg = os.path.join(DEFAULT_BACKUP_DIR, "config.json")
    cfg_to_read = CFG_FILE if os.path.exists(CFG_FILE) else (old_cfg if os.path.exists(old_cfg) else "")
    if cfg_to_read:
        try:
            with open(cfg_to_read, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("server"):
                state["server"] = str(data["server"]).strip()
            if isinstance(data.get("op_history"), list):
                state["op_history"] = data["op_history"][:25]
            if isinstance(data.get("server_history"), list):
                state["server_history"] = [str(x).strip() for x in data["server_history"] if str(x).strip()][:15]
            if data.get("backup_dir"):
                state["backup_dir"] = os.path.expanduser(str(data["backup_dir"]).strip())
            if data.get("mirror_dir"):
                state["mirror_dir"] = os.path.expanduser(str(data["mirror_dir"]).strip())
            if isinstance(data.get("mirror_enabled"), bool):
                state["mirror_enabled"] = data["mirror_enabled"]
            if data.get("lang") in ("en", "uk"):
                state["lang"] = data["lang"]
            if data.get("theme") in VALID_THEMES:
                state["theme"] = data["theme"]
            if data.get("ui_scale") in VALID_SCALES:
                state["ui_scale"] = data["ui_scale"]
            if isinstance(data.get("ui_font"), int) and (data["ui_font"] == 0 or 8 <= data["ui_font"] <= 28):
                state["ui_font"] = data["ui_font"]
            if isinstance(data.get("minimize_to_tray"), bool):
                state["minimize_to_tray"] = data["minimize_to_tray"]
            if data.get("progress_style") in VALID_PBAR_STYLES:
                state["progress_style"] = data["progress_style"]
            if data.get("delete_mode") in ("trash", "direct", "permanent"):
                state["delete_mode"] = data["delete_mode"]
            for bk in ("lite_mode", "hw_checked", "silent_sec_digits", "silent_cleanup", "sched_missed", "sched_wake"):
                if isinstance(data.get(bk), bool):
                    state[bk] = data[bk]
            st_raw = str(data.get("sched_time") or "").strip()
            if ":" in st_raw:
                hh, mm = st_raw.split(":", 1)
                if hh.isdigit() and mm.isdigit() and 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59:
                    state["sched_time"] = f"{int(hh):02d}:{int(mm):02d}"
            if data.get("sched_mode") in ("--hidden", "--silent"):
                state["sched_mode"] = data["sched_mode"]
            if data.get("sched_prio") in (2, 4, 5, 6, 7, 8, 9):
                state["sched_prio"] = data["sched_prio"]
            for ik in ("daily_days", "today_max", "weekly_count", "monthly_count", "yearly_count"):
                if ik in data and isinstance(data[ik], int) and data[ik] >= 0:
                    state[ik] = data[ik]
            for sk in SECRET_KEYS:
                if data.get(sk):
                    state[sk] = str(data[sk]).strip()
                    state["dirty"] = True
        except Exception:
            pass

    if state["server"]:
        record_server_history(state, state["server"])
    if any(a in ("--lite", "/lite") for a in ARGS_LOW):
        state["lite_mode"] = True
    if not state["hw_checked"]:
        state["hw_checked"] = True
        if sys.platform == "darwin":
            try:
                import subprocess
                res_m = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"], capture_output=True, text=True, timeout=0.5)
                is_mac_dark = ("dark" in (res_m.stdout or "").lower())
                state["theme"] = "mac_dark" if is_mac_dark else "mac_light"
                state["hw_auto_notice"] = (
                    f"Виявлено macOS ({'темний' if is_mac_dark else 'світлий'} системний режим).\n\n"
                    f"Автоматично встановлено тему оформлення «{'macOS Sonoma Dark' if is_mac_dark else 'macOS Yosemite Light'}».\n"
                    f"Ви можете змінити її у будь-який момент кнопкою «🎨 Тема» або в налаштуваннях."
                )
            except Exception:
                state["theme"] = "mac_light"
        is_low, reason = _detect_low_end_or_win7()
        if is_low:
            auto_theme = "win7" if "Windows 7" in reason else "win95"
            auto_theme_lbl = "Windows 7 Aero" if auto_theme == "win7" else "Windows 95 / 98 Classic"
            state["theme"] = auto_theme
            state["lite_mode"] = False
            state["hw_auto_notice"] = (
                f"Виявлено старий комп'ютер або {reason}.\n\n"
                f"Для оптимальної швидкодії та читабельності автоматично обрано тему «{auto_theme_lbl}».\n"
                f"Надалі ви можете вільно змінити тему оформлення у налаштуваннях або кнопкою «🎨 Тема» у верхній панелі."
            )
        state["dirty"] = True

    loaded_from_keyring = False
    if HAS_KEYRING:
        try:
            for sk in SECRET_KEYS:
                val = keyring.get_password(KEYRING_SERVICE, sk)
                if val:
                    state[sk] = val.strip()
                    loaded_from_keyring = True
            state["storage_backend"] = "keyring"
        except Exception:
            pass

    if not loaded_from_keyring:
        env_sec = _read_env_secrets()
        for sk in SECRET_KEYS:
            if env_sec.get(sk):
                state[sk] = env_sec[sk]
        if env_sec or not HAS_KEYRING:
            state["storage_backend"] = "env"

    if state["dirty"]:
        commit_state(state)
    return state

def commit_state(state):
    _ensure_secure_dir()
    os.makedirs(state["backup_dir"], exist_ok=True)
    if state.get("server"):
        record_server_history(state, state["server"])
    pub_keys = (
        "server", "server_history", "op_history", "backup_dir", "mirror_dir", "mirror_enabled",
        "daily_days", "today_max", "weekly_count", "monthly_count", "yearly_count",
        "delete_mode", "lang", "theme", "ui_scale", "ui_font", "minimize_to_tray",
        "lite_mode", "hw_checked", "progress_style", "silent_sec_digits", "silent_cleanup",
        "sched_time", "sched_mode", "sched_missed", "sched_wake", "sched_prio"
    )
    payload = {k: state[k] for k in pub_keys}
    tmp_cfg = CFG_FILE + ".tmp"
    with open(tmp_cfg, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_cfg, CFG_FILE)

    saved_to_keyring = False
    if HAS_KEYRING:
        try:
            for sk in SECRET_KEYS:
                val = state.get(sk, "")
                if val:
                    keyring.set_password(KEYRING_SERVICE, sk, val)
                else:
                    try:
                        keyring.delete_password(KEYRING_SERVICE, sk)
                    except Exception:
                        pass
            saved_to_keyring = True
            state["storage_backend"] = "keyring"
            if os.path.exists(ENV_FILE):
                os.remove(ENV_FILE)
        except Exception:
            saved_to_keyring = False

    if not saved_to_keyring:
        _write_env_secrets(state)
        state["storage_backend"] = "env"
    state["dirty"] = False
