import csv
import json
import os
import platform
import re
from datetime import datetime
from uuid import uuid4

from core.config import SCRIPT_VER, get_logs_dir

_DEVICE_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class CloudRateLimitError(RuntimeError):
    pass


def cloud_sync_error_text(error, language="en"):
    return str(error)


def new_operation_id():
    return uuid4().hex


def validate_cloud_settings(remote, cloud_path):
    path = (cloud_path or "").strip().strip("/")
    return path or "HomeGridBackup"


def _device_id(state):
    value = str(state.get("device_id") or "")
    if not _DEVICE_ID_RE.fullmatch(value):
        raise ValueError("The device ID is missing or invalid.")
    return value


def sync_cloud_backups(engine, prune=False, progress_cb=None):
    return False


def sync_cloud_reports(engine):
    return False


def sync_pending_cloud_data(engine, force=False):
    return {"archives": 0, "reports": 0, "total": 0}


def start_cloud_sync_worker(engine, force=False, on_complete=None):
    return False


def cloud_sync_queue_state(engine):
    return {"archives": 0, "reports": 0, "total": 0}


def cloud_archive_sync_status(engine, archive):
    return "unknown"


def get_cloud_dest_stats(state):
    return None


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
                try:
                    with open(source_path, "r", encoding="utf-8") as source:
                        for line_number, line in enumerate(source, 1):
                            if not line.strip():
                                continue
                            record = json.loads(line)
                            if not isinstance(record, dict):
                                continue
                            if device_id is not None and record.get("device_id") != device_id:
                                continue
                            event_key = tuple(
                                record.get(key, "")
                                for key in ("device_id", "operation_id", "event", "timestamp", "stage")
                            )
                            if not all(event_key[:4]):
                                event_key = (relative_path, line_number, line.strip())
                            records[event_key] = record
                except Exception:
                    continue
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
    ordered = _ordered_report_records(records)[-50:]
    with open(output_path, "w", encoding="utf-8", newline="") as output:
        for record in ordered:
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + chr(10))
    return len(ordered)


def _write_plain_text_report(records, output_path):
    ordered = _ordered_report_records(records)
    fixed_fields = {
        "timestamp", "device_id", "operation_id", "event",
        "platform", "platform_version", "architecture",
    }
    with open(output_path, "w", encoding="utf-8", newline="") as output:
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
            output.write(" | ".join(fields) + chr(10))
    return len(ordered)


def _write_speed_csv_report(records, output_path):
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


def record_operation_event(engine, operation_id, event, stage="", archive="", size_mb=0.0, duration_sec=None, **details):
    if str(event).startswith("stage_"):
        return
    device_id = _device_id(engine.state)
    now = datetime.now().astimezone()
    report_dir = os.path.join(get_logs_dir(engine.state), "reports", device_id)
    os.makedirs(report_dir, mode=0o700, exist_ok=True)
    report_path = os.path.join(report_dir, "operations.jsonl")
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
        "mirror_enabled", "mirror_duration_sec", "net_enabled", "net_duration_sec",
        "net_speed_mbps", "gfs_removed_count", "system_info", "summary", "result", "error_type",
    }
    for key in allowed_details.intersection(details):
        value = details[key]
        if value is not None:
            record[key] = value
    with open(report_path, "a", encoding="utf-8") as report:
        report.write(json.dumps(record, ensure_ascii=False) + chr(10))
    try:
        for fn in os.listdir(report_dir):
            if fn.endswith(".jsonl") and fn != "operations.jsonl":
                os.remove(os.path.join(report_dir, fn))
        with open(report_path, "r", encoding="utf-8") as rf:
            lines = [ln for ln in rf if ln.strip()]
        if len(lines) > 50:
            tmp_p = report_path + ".tmp"
            with open(tmp_p, "w", encoding="utf-8") as wf:
                wf.writelines(lines[-50:])
            os.replace(tmp_p, report_path)
    except Exception:
        pass

def sync_network_shared_journal(engine):
    state = engine.state
    net_dir = os.path.expanduser((state.get("net_dir") or "").strip())
    if not net_dir or not os.path.isdir(net_dir):
        return False
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


def fetch_cloud_speed_stats(engine, refresh=True):
    state = engine.state
    net_dir = os.path.expanduser((state.get("net_dir") or "").strip())
    local_reports = os.path.join(get_logs_dir(state), "reports")
    scan_dirs = [local_reports]
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
        _op = str(op.get("platform") or "").strip()
        _ov = str(op.get("platform_version") or "").strip().partition("-").__getitem__(0)
        if _op == "Linux" and "." in _ov:
            _a, _, _b = _ov.partition(".")
            _ov = f"{_a}.{_b.partition('.').__getitem__(0)}"
        elif _op == "Darwin":
            _op = "macOS"
            _ov = _ov.partition(".").__getitem__(0)
        os_n = f"{_op} {_ov}".strip() or "OS"
        did = op["device_id"]
        op["dev_label"] = (f"* {os_n}" if did == own_id else os_n).strip()
        op["dur_f"], op["mb_f"], op["spd_f"] = round(dur, 1), round(mb, 1), round(spd, 2)
        net_d = float(op.get("net_duration_sec") or 0.0)
        op["net_spd_f"] = round(float(op.get("net_speed_mbps") or (mb / net_d if net_d > 0 else 0)), 2)
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
        ns = [x for x in last2 if x.get("net_spd_f", 0) > 0]
        dev_stats.append({
            "device_id": did, "label": d_ops[0]["dev_label"], "is_own": did == own_id,
            "total_cnt": len(d_ops), "sample_cnt": len(last2),
            "avg_dur": avg_dur, "min_dur": min(x["dur_f"] for x in last2),
            "avg_net_spd": round(sum(x["net_spd_f"] for x in ns) / len(ns), 1) if ns else 0.0,
            "avg_spd": avg_spd,
        })
    dev_stats.sort(key=lambda d: (-d["avg_spd"], d["avg_dur"]))
    return {"ops": ops, "devices": dev_stats}
