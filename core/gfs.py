# ==============================================================================
# patch-id: gfs-scan-cache-2.07
# [ФАЙЛ: core/gfs.py (v2.08 | 22.11.2026 09:10) — ПЛАНИРОВЩИК GFS, ЗАЩИТА KEEP И РОТАЦИЯ КОПИЙ]
# ==============================================================================
import os
import re
from datetime import datetime, timedelta
from core.files import parse_backup_dt, format_backup_dt, remove_backup_file

_GFS_PLAN_CACHE = {}

def compute_gfs_plan(state):
    bdir = state["backup_dir"]
    os.makedirs(bdir, exist_ok=True)
    keep_n = max(1, int(state.get("keep_last_count", 5)))
    snapshot = []
    try:
        with os.scandir(bdir) as entries:
            for entry in entries:
                if entry.name.startswith(".") or not entry.name.lower().endswith(".zip"):
                    continue
                if not (entry.is_file(follow_symlinks=False) and re.search(r"backup|KEEP", entry.name)):
                    continue
                st = entry.stat(follow_symlinks=False)
                snapshot.append((entry.name, st.st_size, st.st_mtime_ns))
    except Exception:
        snapshot = []
    snapshot.sort(key=lambda item: item[0])

    cache_key = (os.path.normcase(os.path.abspath(bdir)), keep_n, tuple(snapshot))
    cached = _GFS_PLAN_CACHE.get(cache_key)
    if cached is not None:
        return cached

    all_items = []
    for name, sz, mtime_ns in snapshot:
        full = os.path.join(bdir, name)
        dt = parse_backup_dt(name, mtime_ns / 1000000000.0)
        all_items.append({"path": full, "name": name, "size": sz, "dt_str": dt.strftime("%Y-%m-%d %H:%M"), "dt": dt})
    all_items.sort(key=lambda x: x["dt"], reverse=True)

    tags = {}
    for it in all_items:
        if re.search(r"(^|_)KEEP(_|\.)", it["name"]):
            tags[it["path"]] = "KEEP"
    unpinned = [it for it in all_items if it["path"] not in tags]
    for it in unpinned[:keep_n]:
        tags[it["path"]] = "DAILY"

    keep_items, del_items = [], []
    for it in all_items:
        if it["path"] in tags:
            it["new_tag"] = tags[it["path"]]
            keep_items.append(it)
        else:
            it["new_tag"] = "DELETE"
            del_items.append(it)
    result = (all_items, keep_items, del_items)
    _GFS_PLAN_CACHE[cache_key] = result
    if len(_GFS_PLAN_CACHE) > 16:
        _GFS_PLAN_CACHE.pop(next(iter(_GFS_PLAN_CACHE)))
    return result

def toggle_keep_tag(state, filename):
    bdir = state["backup_dir"]
    safe_name = os.path.basename(filename or "")
    old_p = os.path.join(bdir, safe_name)
    if not safe_name or not os.path.isfile(old_p):
        return False, ""
    if re.search(r"(^|_)KEEP(_|\.)", safe_name):
        new_name = re.sub(r"_KEEP(?=_|\.)", "_DAILY", safe_name, count=1)
        if new_name == safe_name:
            new_name = safe_name.replace("KEEP_", "DAILY_", 1)
    else:
        if re.search(r"_(DAILY|WEEKLY|MONTHLY|YEARLY)(?=_|\.)", safe_name):
            new_name = re.sub(r"_(DAILY|WEEKLY|MONTHLY|YEARLY)(?=_|\.)", "_KEEP", safe_name, count=1)
        else:
            new_name = "homegrid_backup_KEEP_" + safe_name
    new_p = os.path.join(bdir, new_name)
    if new_p != old_p and not os.path.exists(new_p):
        os.replace(old_p, new_p)
        old_sha = old_p + ".sha256"
        if os.path.exists(old_sha):
            new_sha = new_p + ".sha256"
            try:
                with open(old_sha, "r", encoding="utf-8") as fs:
                    h_part = next(iter(fs.read().split()), "")
                with open(new_sha, "w", encoding="utf-8") as fs:
                    fs.write(f"{h_part}  {new_name}\n")
                os.remove(old_sha)
            except Exception:
                os.replace(old_sha, new_sha)
        return True, new_name
    return False, safe_name

def apply_gfs_cleanup(engine, skip_prompt=False):
    all_items, keep_items, del_items = compute_gfs_plan(engine.state)
    bdir = engine.state["backup_dir"]
    del_mode = engine.state.get("delete_mode", "trash")
    renamed = 0
    for batch_start in range(0, len(keep_items), 25):
        batch = keep_items[batch_start:batch_start + 25]
        for it in batch:
            old_p = it["path"]
            old_sha = old_p + ".sha256"
            tg = it["new_tag"]
            d_str = format_backup_dt(it["dt"])
            nn = f"homegrid_backup_{tg}_{d_str}.zip"
            new_p = os.path.join(bdir, nn)
            if it["name"] != nn:
                if os.path.exists(new_p):
                    ss = datetime.fromtimestamp(os.path.getmtime(old_p)).strftime("%S")
                    nn = f"homegrid_backup_{tg}_{d_str}_{ss}.zip"
                    new_p = os.path.join(bdir, nn)
                if it["name"] != nn:
                    os.replace(old_p, new_p)
                    if os.path.exists(old_sha):
                        new_sha = new_p + ".sha256"
                        try:
                            with open(old_sha, "r", encoding="utf-8") as fs:
                                hash_part = next(iter(fs.read().split()), "")
                            with open(new_sha, "w", encoding="utf-8") as fs:
                                fs.write(f"{hash_part}  {nn}\n")
                            os.remove(old_sha)
                        except Exception:
                            os.replace(old_sha, new_sha)
                    renamed += 1

    deleted = 0
    del_mb = round(sum(x["size"] for x in del_items) / 1048576.0, 1)
    if del_items:
        action_txt = "Видалити назавжди з диска" if del_mode == "permanent" else "Перемістити у Кошик"
        do_del = True if skip_prompt else engine.ask_modal("confirm", "Очищення старих бекапів", f"{action_txt} {len(del_items)} застарілих копій ({del_mb} МБ)?")
        if do_del:
            batch_size = 25
            for batch_start in range(0, len(del_items), batch_size):
                batch = del_items[batch_start:batch_start + batch_size]
                for it in batch:
                    if remove_backup_file(it["path"], del_mode):
                        deleted += 1
                        sha_p = it["path"] + ".sha256"
                        if os.path.exists(sha_p):
                            remove_backup_file(sha_p, del_mode)
                engine.set_progress(
                    min(100, int((batch_start + len(batch)) * 100 / len(del_items))),
                    f"Ротація GFS: {min(batch_start + len(batch), len(del_items))}/{len(del_items)}"
                )
            done_lbl = "Видалено з диска назавжди" if del_mode == "permanent" else "Переміщено у Кошик"
            engine.log(f"{done_lbl}: {deleted} файл(ів) ({del_mb} МБ).", "ok")
        else:
            engine.log("Очищення застарілих архівів пропущено.", "info")
    return deleted, renamed, del_mb
