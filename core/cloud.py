import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from uuid import uuid4

from core.config import SECURE_DIR

_REMOTE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_DEVICE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_ARCHIVE_RE = re.compile(r"(backup|KEEP)", re.IGNORECASE)


def new_operation_id():
    return uuid4().hex


def list_rclone_remotes():
    executable = shutil.which("rclone")
    if not executable:
        raise RuntimeError("rclone is not installed or is not available in PATH.")
    result = subprocess.run(
        [executable, "listremotes"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    if result.returncode:
        raise RuntimeError((result.stderr or "rclone listremotes failed").strip()[-500:])
    return sorted({
        remote[:-1]
        for remote in result.stdout.splitlines()
        if remote.endswith(":") and _REMOTE_RE.fullmatch(remote[:-1])
    })


def validate_cloud_settings(remote, cloud_path):
    if not _REMOTE_RE.fullmatch((remote or "").strip()):
        raise ValueError("Виберіть коректний rclone remote.")
    path = (cloud_path or "").strip().strip("/")
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
    executable = shutil.which("rclone")
    if not executable:
        raise RuntimeError("rclone is not installed or is not available in PATH.")
    result = subprocess.run(
        [executable, "--retries", "1", "--low-level-retries", "1", "--stats", "0", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        message = (result.stderr or result.stdout or "rclone command failed").strip()
        raise RuntimeError(message[-700:])
    return result.stdout


def sync_cloud_backups(engine, prune=False):
    if not engine.state.get("cloud_enabled"):
        return
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

    if not prune:
        return

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


def record_operation_event(engine, operation_id, event, stage="", archive="", size_mb=0.0, duration_sec=None):
    if not engine.state.get("cloud_enabled"):
        return
    device_id = _device_id(engine.state)
    now = datetime.now().astimezone()
    report_dir = os.path.join(SECURE_DIR, "cloud_reports", device_id)
    os.makedirs(report_dir, mode=0o700, exist_ok=True)
    report_path = os.path.join(report_dir, now.strftime("%Y-%m-%d") + ".jsonl")
    marker_path = report_path + ".pending"
    with open(marker_path, "a", encoding="utf-8"):
        pass
    record = {
        "timestamp": now.isoformat(timespec="seconds"),
        "device_id": device_id,
        "operation_id": operation_id,
        "event": event,
    }
    if stage:
        record["stage"] = stage
    if archive:
        record["archive"] = os.path.basename(archive)
    if size_mb:
        record["size_mb"] = round(float(size_mb), 1)
    if duration_sec is not None:
        record["duration_sec"] = round(float(duration_sec), 1)
    with open(report_path, "a", encoding="utf-8") as report:
        report.write(json.dumps(record, ensure_ascii=False) + "\n")


def sync_cloud_reports(engine):
    if not engine.state.get("cloud_enabled"):
        return
    device_id = _device_id(engine.state)
    report_dir = os.path.join(SECURE_DIR, "cloud_reports", device_id)
    if not os.path.isdir(report_dir):
        return
    pending = sorted(
        name for name in os.listdir(report_dir)
        if name.endswith(".jsonl.pending")
    )
    for marker in pending:
        report_name = marker[:-len(".pending")]
        report_path = os.path.join(report_dir, report_name)
        if not os.path.isfile(report_path):
            os.remove(os.path.join(report_dir, marker))
            continue
        target = _remote_path(engine.state, "operations", device_id, report_name)
        _rclone("copyto", report_path, target)
        os.remove(os.path.join(report_dir, marker))
