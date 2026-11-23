import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from uuid import uuid4

# patch-id: pcloud-only-simple-ui-2.27
# patch-id: pcloud-clean-hints-2.30
# patch-id: cloud-speed-stats-2.31
# patch-id: pcloud-disable-and-freespace-2.57
# patch-id: pcloud-retention-count-size-2.52
# patch-id: destination-copies-network-journal-2.58-1b
# patch-id: pcloud-speed-progress-gradient-2.33
# patch-id: archives-label-and-logs-dir-2.60
# patch-id: dest-stats-bg-worker-2.61
from core.config import SCRIPT_VER, get_logs_dir
_PCT_RE = re.compile(r"(\d+)%")

def _rclone_upload_with_progress(src_path, dst_remote_file, progress_cb=None, timeout=3600):
    exe = _rclone_executable()
    if not exe:
        raise RuntimeError("Не знайдено rclone. Покладіть rclone.exe (або rclone) поруч із програмою.")
    cmd = [
        exe, "copyto", src_path, dst_remote_file,
        "--transfers", "4", "--multi-thread-streams", "4",
        "--buffer-size", "32M", "--pcloud-upload-cutoff", "64M",
        "--retries", "3", "--low-level-retries", "10",
        "--stats", "1s", "--stats-one-line",
    ]
    proc = subprocess.Popen(
        cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=_NO_WINDOW
    )
    tail = []
    for raw in proc.stdout:
        ln = raw.strip()
        if ln:
            tail.append(ln)
            if len(tail) > 8: tail.pop(0)
            if progress_cb:
                m = _PCT_RE.search(ln)
                pct = int(m.group(1)) if m else None
                parts = [p.strip() for p in ln.split(",") if p.strip()]
                info = " | ".join(parts[:3]) if parts else ln
                progress_cb(pct, info)
    rc = proc.wait(timeout=timeout)
    if rc != 0:
        raise RuntimeError((" ".join(tail) or "rclone upload failed")[-700:])

from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW

_REMOTE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_DEVICE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_ARCHIVE_RE = re.compile(r"(backup|KEEP)", re.IGNORECASE)
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
_CLOUD_SYNC_LOCK = threading.Lock()
_RCLONE_VERSION = None
RCLONE_PROVIDERS = (("pCloud", "pcloud", "pcloud"),)
WINDOWS7_RCLONE_PROVIDERS = (("pCloud", "pcloud", "pcloud"),)


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


def available_rclone_providers():
    if WINDOWS7_CLOUD_SYNC_PREVIEW:
        return WINDOWS7_RCLONE_PROVIDERS
    return RCLONE_PROVIDERS


def list_rclone_remotes():
    executable = _rclone_executable()
    if not executable:
        raise RuntimeError("Не знайдено rclone. Покладіть rclone.exe (або rclone) поруч із програмою.")
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
    if backend not in {provider[1] for provider in available_rclone_providers()}:
        raise ValueError("Unsupported cloud provider.")
    if remote in list_rclone_remotes():
        raise ValueError(f"A rclone remote named '{remote}' already exists.")
    executable = _rclone_executable()
    if not executable:
        raise RuntimeError("Не знайдено rclone. Покладіть rclone.exe (або rclone) поруч із програмою.")
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


def create_rclone_remote(remote, backend, username, password):
    remote = (remote or "").strip()
    if not _REMOTE_RE.fullmatch(remote):
        raise ValueError("Имя подключения может содержать только буквы, цифры, '.', '_' и '-'.")
    if backend not in {provider[1] for provider in available_rclone_providers()}:
        raise ValueError("Unsupported cloud provider.")
    if backend not in ("mega", "koofr"):
        raise ValueError("Credential setup is only available for MEGA and Koofr.")
    username = (username or "").strip()
    if not username or not password:
        raise ValueError("Введіть ім'я користувача та пароль.")
    if remote in list_rclone_remotes():
        raise ValueError(f"A rclone remote named '{remote}' already exists.")
    executable = _rclone_executable()
    if not executable:
        raise RuntimeError("Не знайдено rclone. Покладіть rclone.exe (або rclone) поруч із програмою.")

    password_key = "pass" if backend == "mega" else "password"
    options = ["user", username, password_key, password]
    if backend == "koofr":
        options.extend(("provider", "koofr"))
    try:
        result = _run(
            [executable, "config", "create", remote, backend, *options, "--obscure", "--non-interactive"],
            60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        message = str(exc).replace(password, "[redacted]")
        raise RuntimeError(message[-700:]) from exc
    if result.returncode:
        message = (result.stderr or result.stdout or "rclone remote creation failed").strip()
        if password:
            message = message.replace(password, "[redacted]")
        raise RuntimeError(message[-700:])
    return result.stdout


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


def check_rclone_remote(remote):
    """Проверяет подключение одним вызовом rclone about.

    Возвращает {"total", "used", "free"} в байтах. Значение None означает,
    что облако не сообщает объем (подключение при этом работает).
    """
    remote = (remote or "").strip()
    if remote.endswith(":"):
        remote = remote[:-1]
    if not _REMOTE_RE.fullmatch(remote):
        raise ValueError("Select a valid rclone remote.")
    remote_path = f"{remote}:"
    unknown = {"total": None, "used": None, "free": None}
    try:
        output = _rclone("about", remote_path, "--json", timeout=60)
    except RuntimeError as about_error:
        try:
            _rclone("lsd", remote_path, "--max-depth", "1", timeout=60)
        except RuntimeError as list_error:
            raise RuntimeError(
                f"rclone about failed: {about_error}; listing failed: {list_error}"
            ) from list_error
        return unknown
    try:
        data = json.loads(output)
    except ValueError:
        return unknown
    if not isinstance(data, dict):
        return unknown
    usage = {}
    for key in ("total", "used", "free"):
        value = data.get(key)
        usage[key] = int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None
    return usage


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
        raise RuntimeError("Не знайдено rclone. Покладіть rclone.exe (або rclone) поруч із програмою.")
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


def _ensure_cloud_free_space(engine, remote_dir, needed_bytes):
    if not engine.state.get("cloud_fit_free_space", True):
        return
    remote = str(engine.state.get("cloud_remote") or "pcloud").strip()
    try:
        usage = check_rclone_remote(remote)
    except Exception:
        return
    free_b = usage.get("free")
    if free_b is None:
        return
    safety_b = 64 * 1024 * 1024
    target_free = max(0, int(needed_bytes)) + safety_b
    if free_b >= target_free:
        return
    raw_ls = _rclone("lsjson", "--files-only", remote_dir)
    entries = json.loads(raw_ls) if raw_ls.strip() else []
    arcs = [
        e for e in entries
        if isinstance(e, dict)
        and str(e.get("Name", "")).lower().endswith(".zip")
        and _ARCHIVE_RE.search(str(e.get("Name", "")))
    ]
    arcs.sort(key=lambda e: (1 if "_KEEP_" in str(e.get("Name", "")).upper() else 0, str(e.get("ModTime", ""))))
    all_names = {str(e.get("Name", "")) for e in entries}
    freed_b, del_cnt = 0, 0
    for e in arcs:
        if free_b + freed_b >= target_free:
            break
        nm = str(e.get("Name", ""))
        sz_b = max(0, int(e.get("Size", 0) or 0))
        _rclone("deletefile", f"{remote_dir}/{nm}")
        if f"{nm}.sha256" in all_names:
            _rclone("deletefile", f"{remote_dir}/{nm}.sha256")
        freed_b += sz_b
        del_cnt += 1
    if del_cnt:
        engine.log(f"pCloud автоочищення: звільнено {round(freed_b / 1048576.0, 1)} МБ (видалено {del_cnt} старих архівів) під вільне місце.", "info")

def sync_cloud_backups(engine, prune=False, progress_cb=None):
    if not engine.state.get("cloud_enabled") or not engine.state.get("cloud_save_archives", True):
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
        shared_user_folder = WINDOWS7_CLOUD_SYNC_PREVIEW
        remote_dir = _remote_path(
            engine.state, "backups"
        ) if shared_user_folder else _remote_path(engine.state, "backups", device_id)
        remote_device_prefix = device_id + "_" if shared_user_folder else ""
        _, keep_items, _ = compute_gfs_plan(engine.state)
        keep_names = set()
        for item in keep_items:
            path = item["path"]
            if not os.path.isfile(path):
                continue
            local_name = os.path.basename(path)
            remote_name = remote_device_prefix + local_name
            keep_names.add(remote_name)
            try:
                _write_cloud_archive_status(engine, path, "queued")
                _ensure_cloud_free_space(engine, remote_dir, os.path.getsize(path))
                _rclone_upload_with_progress(path, f"{remote_dir}/{remote_name}", progress_cb=progress_cb)
                sha_path = path + ".sha256"
                if os.path.isfile(sha_path):
                    if shared_user_folder:
                        with open(sha_path, "r", encoding="utf-8") as source:
                            sha_parts = source.read().split()
                        if not sha_parts or not re.fullmatch(r"[0-9a-fA-F]{64}", sha_parts[0]):
                            raise ValueError(f"Invalid SHA-256 sidecar: {sha_path}")
                        digest = sha_parts[0]
                        with tempfile.TemporaryDirectory(prefix="homegrid-cloud-sha-") as temp_dir:
                            cloud_sha_path = os.path.join(temp_dir, remote_name + ".sha256")
                            with open(cloud_sha_path, "w", encoding="utf-8", newline="\n") as target:
                                target.write(f"{digest.lower()}  {remote_name}\n")
                            _rclone("copyto", cloud_sha_path, f"{remote_dir}/{remote_name}.sha256")
                    else:
                        _rclone("copyto", sha_path, f"{remote_dir}/{remote_name}.sha256")
                _write_cloud_archive_status(engine, path, "uploaded")
            except Exception:
                _write_cloud_archive_status(engine, path, "error")
                raise

        max_cnt = max(0, int(engine.state.get("cloud_max_archives", 0) or 0))
        max_gb = max(0.0, float(engine.state.get("cloud_max_size_gb", 0.0) or 0.0))
        if prune or max_cnt > 0 or max_gb > 0.0:
            raw_ls = _rclone("lsjson", "--files-only", remote_dir)
            entries = json.loads(raw_ls) if raw_ls.strip() else []
            arc_entries = [
                e for e in entries
                if isinstance(e, dict)
                and str(e.get("Name", "")).lower().endswith(".zip")
                and _ARCHIVE_RE.search(str(e.get("Name", "")))
                and str(e.get("Name", "")).startswith(remote_device_prefix)
            ]
            arc_entries.sort(key=lambda e: str(e.get("ModTime", "")), reverse=True)
            all_zip_names = {str(e.get("Name", "")) for e in entries if str(e.get("Name", "")).lower().endswith(".zip")}
            to_remove = set()
            if prune:
                for e in arc_entries:
                    nm = str(e.get("Name", ""))
                    if nm not in keep_names:
                        to_remove.add(nm)
            kept_after_prune = [e for e in arc_entries if str(e.get("Name", "")) not in to_remove]
            if max_cnt > 0 and len(kept_after_prune) > max_cnt:
                for e in kept_after_prune[max_cnt:]:
                    nm = str(e.get("Name", ""))
                    if "_KEEP_" not in nm.upper():
                        to_remove.add(nm)
            kept_after_cnt = [e for e in kept_after_prune if str(e.get("Name", "")) not in to_remove]
            if max_gb > 0.0 and len(kept_after_cnt) > 1:
                limit_bytes = int(max_gb * (1024 ** 3))
                acc_bytes = 0
                for idx_e, e in enumerate(kept_after_cnt):
                    nm = str(e.get("Name", ""))
                    sz_b = max(0, int(e.get("Size", 0) or 0))
                    if idx_e == 0 or "_KEEP_" in nm.upper():
                        acc_bytes += sz_b
                        continue
                    if acc_bytes + sz_b > limit_bytes:
                        to_remove.add(nm)
                    else:
                        acc_bytes += sz_b
            all_names_set = {str(e.get("Name", "")) for e in entries}
            for nm in sorted(to_remove):
                _rclone("deletefile", f"{remote_dir}/{nm}")
                sha_nm = f"{nm}.sha256"
                if sha_nm in all_names_set:
                    _rclone("deletefile", f"{remote_dir}/{sha_nm}")
            if to_remove:
                engine.log(f"pCloud ротація: видалено {len(to_remove)} застарілих архівів у хмарі.", "info")
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
    archives_pending = bool(engine.state.get("cloud_save_archives", True)) and os.path.isfile(os.path.join(backup_dir, ".cloud-archives.pending"))
    report_dir = os.path.join(get_logs_dir(engine.state), "reports", _device_id(engine.state))
    reports_pending = 0
    if engine.state.get("cloud_save_logs", True) and os.path.isdir(report_dir):
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


def _cloud_archive_status_path(engine, archive):
    status_dir = os.path.join(os.path.abspath(engine.state["backup_dir"]), ".cloud-status")
    return os.path.join(status_dir, os.path.basename(archive) + ".json")


def _write_cloud_archive_status(engine, archive, status):
    if not WINDOWS7_CLOUD_SYNC_PREVIEW:
        return
    status_path = _cloud_archive_status_path(engine, archive)
    os.makedirs(os.path.dirname(status_path), exist_ok=True)
    remote = str(engine.state.get("cloud_remote") or "").strip()
    cloud_path = validate_cloud_settings(remote, engine.state.get("cloud_path", ""))
    payload = {"status": status, "remote": remote, "cloud_path": cloud_path}
    temp_path = status_path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as status_file:
            json.dump(payload, status_file)
        os.replace(temp_path, status_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def cloud_archive_sync_status(engine, archive):
    if not WINDOWS7_CLOUD_SYNC_PREVIEW or not engine.state.get("cloud_enabled"):
        return "unknown"
    status_path = _cloud_archive_status_path(engine, archive)
    try:
        with open(status_path, "r", encoding="utf-8") as status_file:
            payload = json.load(status_file)
    except FileNotFoundError:
        return "queued" if os.path.isfile(
            os.path.join(os.path.abspath(engine.state["backup_dir"]), ".cloud-archives.pending")
        ) else "unknown"
    remote = str(engine.state.get("cloud_remote") or "").strip()
    cloud_path = validate_cloud_settings(remote, engine.state.get("cloud_path", ""))
    if payload.get("remote") != remote or payload.get("cloud_path") != cloud_path:
        return "unknown"
    status = payload.get("status")
    return status if status in ("uploaded", "queued", "error") else "error"


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


def _collect_report_records(source_dirs, device_id=None):
    records = {}
    for source_dir in source_dirs:
        if not os.path.isdir(source_dir):
            continue
        for root, dirs, names in os.walk(source_dir):
            dirs.sort()
            for name in sorted(names):
                if not name.endswith(".jsonl"):
                    continue
                source_path = os.path.join(root, name)
                relative_path = os.path.relpath(source_path, source_dir)
                with open(source_path, "r", encoding="utf-8") as source:
                    for line_number, line in enumerate(source, 1):
                        try:
                            record = json.loads(line)
                        except (TypeError, ValueError) as exc:
                            raise ValueError(
                                f"Invalid JSON in cloud report source {relative_path}:{line_number}"
                            ) from exc
                        if not isinstance(record, dict):
                            raise ValueError(
                                f"Invalid cloud report event in {relative_path}:{line_number}"
                            )
                        if device_id is not None and record.get("device_id") != device_id:
                            continue
                        event_key = tuple(
                            record.get(key, "")
                            for key in ("device_id", "operation_id", "event", "timestamp", "stage")
                        )
                        if not all(event_key[:4]):
                            event_key = (relative_path, line_number, line.rstrip("\r\n"))
                        records[event_key] = record
    return records


def _ordered_report_records(records):
    def sort_key(record):
        timestamp = record.get("timestamp", "")
        try:
            timestamp_key = datetime.fromisoformat(timestamp).timestamp()
        except (TypeError, ValueError, OverflowError):
            timestamp_key = 0.0
        return (
            timestamp_key,
            record.get("device_id", ""),
            record.get("operation_id", ""),
            record.get("event", ""),
            record.get("stage", ""),
        )

    return sorted(records.values(), key=sort_key)


def _write_jsonl_report(records, output_path):
    ordered = _ordered_report_records(records)
    with open(output_path, "w", encoding="utf-8", newline="\n") as output:
        for record in ordered:
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return len(ordered)


def _write_plain_text_report(records, output_path):
    ordered = _ordered_report_records(records)
    fixed_fields = {
        "timestamp", "device_id", "operation_id", "event",
        "platform", "platform_version", "architecture",
    }
    with open(output_path, "w", encoding="utf-8", newline="\n") as output:
        for record in ordered:
            platform_name = " ".join(
                str(record.get(key, "")).strip()
                for key in ("platform", "platform_version", "architecture")
                if record.get(key)
            ) or "unknown"
            fields = [
                f"[{record.get('timestamp', 'unknown')}]",
                f"OS={platform_name}",
                f"device={record.get('device_id', 'unknown')}",
                f"event={record.get('event', 'unknown')}",
            ]
            if record.get("operation_id"):
                fields.append(f"operation={record['operation_id']}")
            for key in sorted(record):
                if key not in fixed_fields:
                    value = json.dumps(record[key], ensure_ascii=False, sort_keys=True)
                    fields.append(f"{key}={value}")
            output.write(" | ".join(fields) + "\n")
    return len(ordered)


def _write_speed_csv_report(records, output_path):
    import csv
    ordered = [r for r in _ordered_report_records(records) if r.get("event") == "success"]
    cols = (
        "timestamp", "device_id", "platform", "platform_version", "architecture",
        "app_version", "archive", "size_mb", "files_count", "duration_sec",
        "download_duration_sec", "download_speed_mbps", "server_duration_sec",
        "crc_duration_sec", "sha256_duration_sec", "mirror_duration_sec", "summary",
    )
    with open(output_path, "w", encoding="utf-8-sig", newline="") as out_f:
        writer = csv.writer(out_f, delimiter=";")
        writer.writerow(cols)
        for rec in ordered:
            writer.writerow([rec.get(c, "") for c in cols])
    return len(ordered)


def sync_network_shared_journal(engine):
    state = engine.state
    net_dir = os.path.expanduser((state.get("net_dir") or "").strip())
    if not net_dir or not os.path.isdir(net_dir):
        raise RuntimeError("Мережева папка недоступна для обміну журналом.")
    device_id = _device_id(state)
    report_dir = os.path.join(get_logs_dir(state), "reports", device_id)
    net_sources = os.path.join(net_dir, ".HomeGridBackup-sources")
    os.makedirs(net_sources, exist_ok=True)
    own_records = _collect_report_records((net_sources, report_dir), device_id=device_id)
    if own_records:
        tmp_src = os.path.join(net_sources, f"{device_id}.jsonl.tmp")
        _write_jsonl_report(own_records, tmp_src)
        os.replace(tmp_src, os.path.join(net_sources, f"{device_id}.jsonl"))
    all_records = _collect_report_records((net_sources,))
    tmp_log = os.path.join(net_dir, "HomeGridBackup.log.tmp")
    _write_plain_text_report(all_records, tmp_log)
    os.replace(tmp_log, os.path.join(net_dir, "HomeGridBackup.log"))
    tmp_csv = os.path.join(net_dir, "speed_journal.csv.tmp")
    _write_speed_csv_report(all_records, tmp_csv)
    os.replace(tmp_csv, os.path.join(net_dir, "speed_journal.csv"))
    return True


def _sync_shared_root_report(engine, device_id, report_dir):
    source_remote_dir = _remote_path(engine.state, ".HomeGridBackup-sources")
    legacy_remote_dir = _remote_path(engine.state, "operations")
    remote = str(engine.state["cloud_remote"]).strip()
    cloud_path = validate_cloud_settings(remote, engine.state.get("cloud_path", ""))
    cache_key = hashlib.sha256(
        (remote + "\0" + cloud_path).encode("utf-8")
    ).hexdigest()[:16]
    legacy_cache = os.path.join(
        os.path.abspath(engine.state["backup_dir"]), ".cloud-report-cache", cache_key
    )
    os.makedirs(legacy_cache, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="homegrid-cloud-report-") as temp_dir:
        source_dir = os.path.join(temp_dir, "sources")
        os.makedirs(source_dir)
        _rclone("mkdir", source_remote_dir)
        _rclone("copy", source_remote_dir, source_dir, "--include", "*.jsonl")
        _rclone("mkdir", legacy_remote_dir)
        _rclone("copy", legacy_remote_dir, legacy_cache, "--include", "*.jsonl")

        own_records = _collect_report_records(
            (source_dir, report_dir, legacy_cache), device_id=device_id
        )
        own_source_path = os.path.join(source_dir, device_id + ".jsonl")
        if own_records:
            _write_jsonl_report(own_records, own_source_path)
            _rclone(
                "copyto", own_source_path,
                _remote_path(engine.state, ".HomeGridBackup-sources", device_id + ".jsonl"),
            )

        all_records = _collect_report_records((source_dir, legacy_cache))
        shared_log = os.path.join(temp_dir, "HomeGridBackup.log")
        _write_plain_text_report(all_records, shared_log)
        _rclone("copyto", shared_log, _remote_path(engine.state, "HomeGridBackup.log"))
        shared_csv = os.path.join(temp_dir, "speed_journal.csv")
        _write_speed_csv_report(all_records, shared_csv)
        _rclone("copyto", shared_csv, _remote_path(engine.state, "speed_journal.csv"))



def record_operation_event(engine, operation_id, event, stage="", archive="", size_mb=0.0, duration_sec=None, **details):
    device_id = _device_id(engine.state)
    now = datetime.now().astimezone()
    report_dir = os.path.join(get_logs_dir(engine.state), "reports", device_id)
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
    allowed_details = {
        "files_count", "archive_sequence", "speed_mbps", "download_speed_mbps",
        "download_duration_sec", "server_duration_sec", "server_preparing_sec",
        "server_copying_sec", "server_processing_sec", "server_packing_sec",
        "server_checking_sec", "crc_duration_sec", "sha256_duration_sec",
        "mirror_enabled", "mirror_duration_sec", "gfs_removed_count",
        "system_info", "summary", "result", "error_type",
    }
    for key in allowed_details.intersection(details):
        value = details[key]
        if value is not None:
            record[key] = value
    with open(report_path, "a", encoding="utf-8") as report:
        report.write(json.dumps(record, ensure_ascii=False) + "\n")


def sync_cloud_reports(engine):
    if not engine.state.get("cloud_enabled") or not engine.state.get("cloud_save_logs", True):
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
    report_dir = os.path.join(get_logs_dir(engine.state), "reports", device_id)
    if WINDOWS7_CLOUD_SYNC_PREVIEW:
        os.makedirs(report_dir, mode=0o700, exist_ok=True)
        _recover_report_upload_markers(report_dir)
        pending = sorted(
            name for name in os.listdir(report_dir)
            if name.endswith(".jsonl.pending")
        )
        uploading_markers = []
        for marker in pending:
            marker_path = os.path.join(report_dir, marker)
            uploading_path = marker_path + ".uploading"
            try:
                os.replace(marker_path, uploading_path)
            except FileNotFoundError:
                continue
            uploading_markers.append((marker_path, uploading_path))
        try:
            _sync_shared_root_report(engine, device_id, report_dir)
        except Exception:
            for marker_path, uploading_path in uploading_markers:
                if not os.path.exists(uploading_path):
                    continue
                if os.path.exists(marker_path):
                    os.remove(uploading_path)
                else:
                    os.replace(uploading_path, marker_path)
            raise
        for _, uploading_path in uploading_markers:
            if os.path.exists(uploading_path):
                os.remove(uploading_path)
        return True

    if not os.path.isdir(report_dir):
        return
    pending = sorted(
        name for name in os.listdir(report_dir)
        if name.endswith(".jsonl.pending")
    )
    for marker in pending:
        marker_path = os.path.join(report_dir, marker)
        report_name = marker[:-len(".pending")]
        report_path = os.path.join(report_dir, report_name)
        if not os.path.isfile(report_path):
            os.remove(marker_path)
            continue
        target = _remote_path(engine.state, "operations", device_id, report_name)
        _rclone("copyto", report_path, target)
        os.remove(marker_path)
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

def fetch_cloud_speed_stats(engine, refresh=True):
    state = engine.state
    net_dir = os.path.expanduser((state.get("net_dir") or "").strip())
    has_net_src = bool(net_dir and os.path.isdir(os.path.join(net_dir, ".HomeGridBackup-sources")))
    if not state.get("cloud_enabled") and not has_net_src:
        raise RuntimeError("Увімкніть синхронізацію з pCloud або вкажіть доступну мережеву папку у Налаштуваннях.")
    remote = str(state.get("cloud_remote") or "pcloud").strip()
    cloud_path = validate_cloud_settings(remote, state.get("cloud_path", "HomeGridBackup"))
    ckey = hashlib.sha256((remote + "\0" + cloud_path).encode("utf-8")).hexdigest()[:16]
    base_cache = os.path.join(os.path.abspath(state["backup_dir"]), ".cloud-report-cache", f"all_{ckey}")
    src_dir, ops_dir = os.path.join(base_cache, "sources"), os.path.join(base_cache, "operations")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(ops_dir, exist_ok=True)
    if refresh and state.get("cloud_enabled"):
        for rem_p, loc_p in ((_remote_path(state, ".HomeGridBackup-sources"), src_dir), (_remote_path(state, "operations"), ops_dir)):
            try:
                _rclone("copy", rem_p, loc_p, "--include", "*.jsonl", timeout=90)
            except Exception:
                pass
    scan_dirs = [src_dir, ops_dir]
    if net_dir and os.path.isdir(os.path.join(net_dir, ".HomeGridBackup-sources")):
        scan_dirs.append(os.path.join(net_dir, ".HomeGridBackup-sources"))
    recs = _collect_report_records(tuple(scan_dirs))
    grouped = {}
    for r in _ordered_report_records(recs):
        did = str(r.get("device_id") or "unknown")
        oid = str(r.get("operation_id") or r.get("timestamp") or "")
        g = grouped.setdefault((did, oid), {"device_id": did, "operation_id": oid})
        for k, v in r.items():
            if v not in (None, "", 0, 0.0) or k not in g:
                g[k] = v
    own_id = str(state.get("device_id") or "")
    ops = []
    for op in grouped.values():
        dur = float(op.get("duration_sec") or 0.0)
        mb = float(op.get("size_mb") or 0.0)
        if dur <= 0.0 or (mb <= 0.0 and not str(op.get("archive", "")).lower().endswith(".zip")):
            continue
        dl_d = float(op.get("download_duration_sec") or 0.0)
        spd = float(op.get("download_speed_mbps") or 0.0)
        if spd <= 0.0 and mb > 0.0 and dl_d > 0.0:
            spd = round(mb / dl_d, 2)
        if spd <= 0.0:
            spd = float(op.get("speed_mbps") or (round(mb / dur, 2) if mb > 0.0 else 0.0))
        os_n = " ".join(str(op.get(k) or "").strip() for k in ("platform", "platform_version") if op.get(k)).strip() or "OS"
        did = op["device_id"]
        tag = f"#{did[:4]}" if len(did) >= 4 else ""
        op["dev_label"] = (f"★ {os_n} ({tag})" if did == own_id else f"{os_n} ({tag})").strip()
        op["dur_f"], op["mb_f"], op["spd_f"] = round(dur, 1), round(mb, 1), round(spd, 2)
        ops.append(op)
    ops.sort(key=lambda x: str(x.get("timestamp") or ""), reverse=True)
    by_dev = {}
    for op in ops:
        by_dev.setdefault(op["device_id"], []).append(op)
    dev_stats = []
    for did, d_ops in by_dev.items():
        last2 = d_ops[:2]
        avg_dur = round(sum(x["dur_f"] for x in last2) / len(last2), 1)
        avg_spd = round(sum(x["spd_f"] for x in last2) / len(last2), 2)
        dev_stats.append({
            "device_id": did, "label": d_ops[0]["dev_label"], "is_own": did == own_id,
            "total_cnt": len(d_ops), "sample_cnt": len(last2),
            "avg_dur": avg_dur, "min_dur": min(x["dur_f"] for x in last2), "avg_spd": avg_spd,
        })
    dev_stats.sort(key=lambda d: (-d["avg_spd"], d["avg_dur"]))
    return {"ops": ops, "devices": dev_stats}


def get_cloud_dest_stats(state):
    if not state.get("cloud_enabled"):
        return None
    if not _rclone_executable():
        return {"ok": False, "reason": "немає rclone"}
    remote = str(state.get("cloud_remote") or "pcloud").strip()
    try:
        if remote not in list_rclone_remotes():
            return {"ok": False, "reason": "не підключено"}
    except Exception:
        return {"ok": False, "reason": "не підключено"}
    free_gb = -1.0
    try:
        usage = check_rclone_remote(remote)
        if usage.get("free") is not None:
            free_gb = round(float(usage["free"]) / 1073741824.0, 1)
    except Exception:
        return {"ok": False, "reason": "не підключено"}
    device_id = _device_id(state)
    shared = WINDOWS7_CLOUD_SYNC_PREVIEW
    remote_dir = _remote_path(state, "backups") if shared else _remote_path(state, "backups", device_id)
    prefix = (device_id + "_") if shared else ""
    cnt, total_b = 0, 0
    try:
        raw_ls = _rclone("lsjson", "--files-only", remote_dir, timeout=35)
        entries = json.loads(raw_ls) if raw_ls.strip() else []
        for e in entries:
            if not isinstance(e, dict):
                continue
            nm = str(e.get("Name", ""))
            if nm.lower().endswith(".zip") and _ARCHIVE_RE.search(nm) and nm.startswith(prefix):
                cnt += 1
                total_b += max(0, int(e.get("Size", 0) or 0))
    except Exception:
        pass
    bdir = os.path.abspath(state.get("backup_dir") or "")
    pending = bool(bdir and os.path.isfile(os.path.join(bdir, ".cloud-archives.pending")))
    return {"ok": True, "count": cnt, "mb": round(total_b / 1048576.0, 1), "free_gb": free_gb, "pending": pending}

