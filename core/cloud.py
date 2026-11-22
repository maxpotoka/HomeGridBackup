import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from uuid import uuid4

from core.config import SCRIPT_VER
from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW

_REMOTE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_DEVICE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_ARCHIVE_RE = re.compile(r"(backup|KEEP)", re.IGNORECASE)
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
_CLOUD_SYNC_LOCK = threading.Lock()
_RCLONE_VERSION = None
RCLONE_PROVIDERS = (
    ("Google Drive", "drive", "gdrive"),
    ("OneDrive", "onedrive", "onedrive"),
    ("Dropbox", "dropbox", "dropbox"),
    ("Box", "box", "box"),
    ("pCloud", "pcloud", "pcloud"),
    ("MEGA", "mega", "mega"),
    ("Koofr", "koofr", "koofr"),
)


class CloudRateLimitError(RuntimeError):
    pass


def cloud_sync_error_text(error, language="en"):
    if isinstance(error, CloudRateLimitError):
        from core.i18n import tr
        return tr(
            "Хмарний сервіс обмежив частоту запитів. Файли залишено в черзі; повторна синхронізація буде автоматичною. "
            "Для Google Drive рекомендується власний OAuth Client ID та Secret.",
            language,
        )
    return str(error)


def _run(args, timeout):
    return subprocess.run(
        args,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        creationflags=_NO_WINDOW,
    )


def _rclone_executable():
    bundled_name = "rclone.exe" if os.name == "nt" else "rclone"
    app_paths = (sys.executable, sys.argv[0] if sys.argv else "")
    for app_path in app_paths:
        if app_path:
            bundled_path = os.path.join(os.path.dirname(os.path.abspath(app_path)), bundled_name)
            if os.path.isfile(bundled_path):
                return bundled_path
    return shutil.which("rclone")


def _rclone_version():
    global _RCLONE_VERSION
    if _RCLONE_VERSION is None:
        executable = _rclone_executable()
        if not executable:
            _RCLONE_VERSION = "unavailable"
        else:
            try:
                result = _run([executable, "version"], 15)
                _RCLONE_VERSION = result.stdout.splitlines()[0].strip() if result.returncode == 0 else "unknown"
            except (OSError, subprocess.SubprocessError, IndexError):
                _RCLONE_VERSION = "unknown"
    return _RCLONE_VERSION


def new_operation_id():
    return uuid4().hex


def list_rclone_remotes():
    executable = _rclone_executable()
    if not executable:
        raise RuntimeError("rclone is not installed or is not available in PATH.")
    result = _run([executable, "listremotes"], 15)
    if result.returncode:
        raise RuntimeError((result.stderr or "rclone listremotes failed").strip()[-500:])
    return sorted({
        remote[:-1]
        for remote in result.stdout.splitlines()
        if remote.endswith(":") and _REMOTE_RE.fullmatch(remote[:-1])
    })


def start_rclone_remote_setup(remote, backend):
    remote = (remote or "").strip()
    if not _REMOTE_RE.fullmatch(remote):
        raise ValueError("Имя подключения может содержать только буквы, цифры, '.', '_' и '-'.")
    if backend not in {provider[1] for provider in RCLONE_PROVIDERS}:
        raise ValueError("Unsupported cloud provider.")
    if remote in list_rclone_remotes():
        raise ValueError(f"A rclone remote named '{remote}' already exists.")
    executable = _rclone_executable()
    if not executable:
        raise RuntimeError("rclone is not installed or is not available in PATH.")
    return subprocess.Popen(
        [executable, "config", "create", remote, backend],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=_NO_WINDOW,
    )


def test_rclone_remote(remote):
    remote = (remote or "").strip()
    if remote.endswith(":"):
        remote = remote[:-1]
    if not _REMOTE_RE.fullmatch(remote):
        raise ValueError("Select a valid rclone remote.")
    remote_path = f"{remote}:"
    try:
        return _rclone("about", remote_path)
    except RuntimeError as about_error:
        try:
            return _rclone("lsd", remote_path, "--max-depth", "1")
        except RuntimeError as list_error:
            raise RuntimeError(f"rclone about failed: {about_error}; listing failed: {list_error}") from list_error


def delete_rclone_remote(remote):
    remote = (remote or "").strip()
    if remote.endswith(":"):
        remote = remote[:-1]
    if not _REMOTE_RE.fullmatch(remote):
        raise ValueError("Select a valid rclone remote.")
    _rclone("config", "delete", remote)


def validate_cloud_settings(remote, cloud_path):
    if not _REMOTE_RE.fullmatch((remote or "").strip()):
        raise ValueError("Виберіть коректний rclone remote.")
    path = (cloud_path or "").strip().strip("/")
    if not path:
        raise ValueError("Вкажіть окрему папку у хмарі; корінь сховища не допускається.")
    if ":" in path or "\\" in path or any(part in (".", "..") for part in path.split("/")):
        raise ValueError("Папка у хмарі має бути відносним шляхом без сегментів '.' або '..'.")
    return path


def _device_id(state):
    value = str(state.get("device_id") or "")
    if not _DEVICE_ID_RE.fullmatch(value):
        raise ValueError("The device ID is missing or invalid.")
    return value


def _remote_path(state, *parts):
    remote = str(state.get("cloud_remote") or "").strip()
    if not _REMOTE_RE.fullmatch(remote):
        raise ValueError("The configured rclone remote is invalid.")
    root = validate_cloud_settings(remote, state.get("cloud_path", ""))
    suffix = "/".join(str(part).strip("/") for part in parts if str(part).strip("/"))
    path = "/".join(part for part in (root, suffix) if part)
    return f"{remote}:{path}"


def _rclone(*args, timeout=3600):
    executable = _rclone_executable()
    if not executable:
        raise RuntimeError("rclone is not installed or is not available in PATH.")
    retry_args = (
        ["--retries", "3", "--low-level-retries", "10", "--tpslimit", "2"]
        if WINDOWS7_CLOUD_SYNC_PREVIEW
        else ["--retries", "1", "--low-level-retries", "1"]
    )
    result = _run(
        [
            executable,
            *retry_args,
            "--stats", "0",
            *args,
        ],
        timeout,
    )
    if result.returncode:
        message = (result.stderr or result.stdout or "rclone command failed").strip()
        lowered = message.lower()
        if WINDOWS7_CLOUD_SYNC_PREVIEW and any(code in lowered for code in (
            "ratelimitexceeded",
            "rate_limit_exceeded",
            "userratelimitexceeded",
            "quotaexceeded",
        )):
            raise CloudRateLimitError(
                "Cloud API rate limit exceeded after automatic retries. "
                "For Google Drive, use a personal OAuth client to avoid the shared rclone API quota."
            )
        raise RuntimeError(message[-700:])
    return result.stdout


def sync_cloud_backups(engine, prune=False):
    if not engine.state.get("cloud_enabled"):
        return
    pending_path = None
    if WINDOWS7_CLOUD_SYNC_PREVIEW:
        backup_dir = os.path.abspath(engine.state["backup_dir"])
        os.makedirs(backup_dir, exist_ok=True)
        pending_path = os.path.join(backup_dir, ".cloud-archives.pending")
        with open(pending_path, "a", encoding="utf-8"):
            pass
        if not _CLOUD_SYNC_LOCK.acquire(blocking=False):
            return False

    try:
        from core.gfs import compute_gfs_plan

        device_id = _device_id(engine.state)
        remote_dir = _remote_path(engine.state, "backups", device_id)
        _, keep_items, _ = compute_gfs_plan(engine.state)
        keep_names = set()
        for item in keep_items:
            path = item["path"]
            if not os.path.isfile(path):
                continue
            name = os.path.basename(path)
            keep_names.add(name)
            _rclone("copyto", path, f"{remote_dir}/{name}")
            sha_path = path + ".sha256"
            if os.path.isfile(sha_path):
                _rclone("copyto", sha_path, f"{remote_dir}/{name}.sha256")

        if prune:
            names = _rclone("lsf", "--files-only", remote_dir).splitlines()
            stale_archives = {
                name for name in names
                if name.lower().endswith(".zip")
                and _ARCHIVE_RE.search(name)
                and name not in keep_names
            }
            for name in stale_archives:
                _rclone("deletefile", f"{remote_dir}/{name}")
                sha_name = f"{name}.sha256"
                if sha_name in names:
                    _rclone("deletefile", f"{remote_dir}/{sha_name}")
        if pending_path:
            os.remove(pending_path)
        return True
    finally:
        if WINDOWS7_CLOUD_SYNC_PREVIEW:
            _CLOUD_SYNC_LOCK.release()


def cloud_sync_queue_state(engine):
    if not WINDOWS7_CLOUD_SYNC_PREVIEW or not engine.state.get("cloud_enabled"):
        return {"archives": 0, "reports": 0, "total": 0}
    backup_dir = os.path.abspath(engine.state["backup_dir"])
    archives_pending = os.path.isfile(os.path.join(backup_dir, ".cloud-archives.pending"))
    report_dir = os.path.join(backup_dir, "reports", _device_id(engine.state))
    reports_pending = 0
    if os.path.isdir(report_dir):
        names = set(os.listdir(report_dir))
        reports_pending = sum(name.endswith(".jsonl.pending") for name in names)
        reports_pending += sum(
            name.endswith(".jsonl.pending.uploading")
            and name[:-len(".uploading")] not in names
            for name in names
        )
    result = {"archives": int(archives_pending), "reports": reports_pending}
    result["total"] = result["archives"] + result["reports"]
    return result


def _recover_report_upload_markers(report_dir):
    suffix = ".jsonl.pending.uploading"
    for name in os.listdir(report_dir):
        if not name.endswith(suffix):
            continue
        uploading_path = os.path.join(report_dir, name)
        pending_path = uploading_path[:-len(".uploading")]
        if os.path.exists(pending_path):
            os.remove(uploading_path)
        else:
            os.replace(uploading_path, pending_path)





def record_operation_event(engine, operation_id, event, stage="", archive="", size_mb=0.0, duration_sec=None, **details):
    device_id = _device_id(engine.state)
    now = datetime.now().astimezone()
    report_dir = os.path.join(os.path.abspath(engine.state["backup_dir"]), "reports", device_id)
    os.makedirs(report_dir, mode=0o700, exist_ok=True)
    report_path = os.path.join(report_dir, now.strftime("%Y-%m-%d") + ".jsonl")
    marker_path = report_path + ".pending"
    with open(marker_path, "a", encoding="utf-8"):
        pass
    record = {
        "timestamp": now.isoformat(timespec="milliseconds"),
        "device_id": device_id,
        "operation_id": operation_id,
        "event": event,
        "app_version": SCRIPT_VER,
        "platform": platform.system(),
        "platform_version": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "rclone_version": _rclone_version(),
        "archives_total": max(0, int(engine.state.get("all_time_cnt", 0))),
    }
    if stage:
        record["stage"] = stage
    if archive:
        record["archive"] = os.path.basename(archive)
    if size_mb:
        record["size_mb"] = round(float(size_mb), 1)
    if "size_bytes" in details:
        record["size_bytes"] = max(0, int(details.pop("size_bytes")))
    if duration_sec is not None:
        duration_sec = max(0.0, float(duration_sec))
        record["duration_sec"] = round(duration_sec, 3)
        record["duration_ms"] = round(duration_sec * 1000)
    allowed_details = {"files_count", "archive_sequence", "speed_mbps", "result", "error_type"}
    for key in allowed_details.intersection(details):
        value = details[key]
        if value is not None:
            record[key] = value
    with open(report_path, "a", encoding="utf-8") as report:
        report.write(json.dumps(record, ensure_ascii=False) + "\n")


def sync_cloud_reports(engine):
    if not engine.state.get("cloud_enabled"):
        return
    if WINDOWS7_CLOUD_SYNC_PREVIEW and not _CLOUD_SYNC_LOCK.acquire(blocking=False):
        return False
    acquired = WINDOWS7_CLOUD_SYNC_PREVIEW
    try:
        return _sync_cloud_reports(engine)
    finally:
        if acquired:
            _CLOUD_SYNC_LOCK.release()


def _sync_cloud_reports(engine):
    device_id = _device_id(engine.state)
    report_dir = os.path.join(os.path.abspath(engine.state["backup_dir"]), "reports", device_id)
    if not os.path.isdir(report_dir):
        return
    if WINDOWS7_CLOUD_SYNC_PREVIEW:
        _recover_report_upload_markers(report_dir)
    pending = sorted(
        name for name in os.listdir(report_dir)
        if name.endswith(".jsonl.pending")
    )
    for marker in pending:
        marker_path = os.path.join(report_dir, marker)
        uploading_path = None
        if WINDOWS7_CLOUD_SYNC_PREVIEW:
            uploading_path = marker_path + ".uploading"
            try:
                os.replace(marker_path, uploading_path)
            except FileNotFoundError:
                continue
        report_name = marker[:-len(".pending")]
        report_path = os.path.join(report_dir, report_name)
        if not os.path.isfile(report_path):
            os.remove(uploading_path or marker_path)
            continue
        try:
            target = _remote_path(engine.state, "operations", device_id, report_name)
            _rclone("copyto", report_path, target)
        except Exception:
            if uploading_path and os.path.exists(uploading_path):
                if os.path.exists(marker_path):
                    os.remove(uploading_path)
                else:
                    os.replace(uploading_path, marker_path)
            raise
        os.remove(uploading_path or marker_path)
    return True


def sync_pending_cloud_data(engine, force=False):
    if not engine.state.get("cloud_enabled"):
        return cloud_sync_queue_state(engine)
    queue = cloud_sync_queue_state(engine)
    errors = []
    if force or queue["archives"]:
        try:
            sync_cloud_backups(engine, prune=False)
        except Exception as exc:
            errors.append(exc)
    if force or queue["reports"]:
        try:
            sync_cloud_reports(engine)
        except Exception as exc:
            errors.append(exc)
    if errors:
        rate_limit_error = next(
            (error for error in errors if isinstance(error, CloudRateLimitError)),
            None,
        )
        raise rate_limit_error or errors[0]
    return cloud_sync_queue_state(engine)


def start_cloud_sync_worker(engine, force=False, on_complete=None):
    if not WINDOWS7_CLOUD_SYNC_PREVIEW or not engine.state.get("cloud_enabled"):
        return False
    worker_lock = getattr(engine, "cloud_sync_worker_lock", None)
    if worker_lock is None:
        worker_lock = threading.Lock()
        engine.cloud_sync_worker_lock = worker_lock
    if not worker_lock.acquire(blocking=False):
        return False

    def _worker():
        last_error = None
        try:
            for attempt, delay in enumerate((0, 60, 300, 900)):
                if delay:
                    time.sleep(delay)
                if not engine.state.get("cloud_enabled"):
                    return
                while engine.is_running and engine.state.get("cloud_enabled"):
                    time.sleep(1)
                if not engine.state.get("cloud_enabled"):
                    return
                try:
                    queue = sync_pending_cloud_data(
                        engine,
                        force=force and attempt == 0,
                    )
                    if not queue["total"]:
                        if force or attempt:
                            engine.log("Хмарну синхронізацію завершено.", "ok")
                        last_error = None
                        break
                    last_error = RuntimeError("Cloud sync items remain pending.")
                except Exception as exc:
                    last_error = exc
            if last_error:
                engine.log(
                    "Повторні спроби хмарної синхронізації не вдалися; файли залишено в черзі.",
                    "warn",
                )
        finally:
            worker_lock.release()
            if on_complete:
                try:
                    on_complete(last_error)
                except Exception as exc:
                    engine.log(f"Не вдалося оновити стан хмарної синхронізації: {exc}", "warn")

    worker = threading.Thread(target=_worker, name="cloud-sync-retry", daemon=True)
    try:
        worker.start()
    except Exception:
        worker_lock.release()
        raise
    return True
