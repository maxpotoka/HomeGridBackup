# ==============================================================================
# [ФАЙЛ: core/gfs.py (v1.002 | 18.11.2026 17:14) — ПЛАНИРОВЩИК GFS, ЗАЩИТА KEEP И РОТАЦИЯ КОПИЙ]
# ==============================================================================
import os
import re
from datetime import datetime, timedelta
from core.files import parse_backup_dt, remove_backup_file

def compute_gfs_plan(state):
    bdir = state["backup_dir"]
    os.makedirs(bdir, exist_ok=True)
    all_items = []
    for name in os.listdir(bdir):
        full = os.path.join(bdir, name)
        if os.path.isfile(full) and name.lower().endswith(".zip") and re.search(r"backup|KEEP", name):
            sz = os.path.getsize(full)
            dt = parse_backup_dt(name, os.path.getmtime(full))
            all_items.append({"path": full, "name": name, "size": sz, "dt_str": dt.strftime("%Y-%m-%d %H:%M"), "dt": dt})
    all_items.sort(key=lambda x: x["dt"], reverse=True)

    today = datetime.now().date()
    epoch_mon = datetime(2000, 1, 3)
    daily_days = max(1, int(state.get("daily_days", 7)))
    today_max = max(1, int(state.get("today_max", 2)))
    weekly_cnt = max(0, int(state.get("weekly_count", 4)))
    monthly_cnt = max(0, int(state.get("monthly_count", 12)))
    yearly_cnt = max(0, int(state.get("yearly_count", 3)))

    tags = {}
    for it in all_items:
        if re.search(r"(^|_)KEEP(_|\.)", it["name"]):
            tags[it["path"]] = "KEEP"

    if yearly_cnt > 0:
        seen_years = list(dict.fromkeys(it["dt"].strftime("%Y") for it in all_items))
        for yr in seen_years[:yearly_cnt]:
            grp = [it for it in all_items if it["dt"].strftime("%Y") == yr]
            x = next((it for it in grp if re.search(r"(^|_)YEARLY(_|\.)", it["name"]) and it["path"] not in tags), None)
            if not x and (len(grp) >= 4 or any(re.search(r"(^|_)MONTHLY(_|\.)", it["name"]) for it in grp)):
                x = next((it for it in grp if it["path"] not in tags), None)
            if x:
                tags[x["path"]] = "YEARLY"

    if monthly_cnt > 0:
        seen_months = list(dict.fromkeys(it["dt"].strftime("%Y-%m") for it in all_items))
        for ym in seen_months[:monthly_cnt]:
            grp = [it for it in all_items if it["dt"].strftime("%Y-%m") == ym]
            x = next((it for it in grp if re.search(r"(^|_)MONTHLY(_|\.)", it["name"]) and it["path"] not in tags), None)
            if not x and (len(grp) >= 3 or any(re.search(r"(^|_)WEEKLY(_|\.)", it["name"]) for it in grp)):
                x = next((it for it in grp if it["path"] not in tags), None)
            if x:
                tags[x["path"]] = "MONTHLY"

    if weekly_cnt > 0:
        seen_weeks = list(dict.fromkeys((it["dt"] - epoch_mon).days // 7 for it in all_items))
        for wk in seen_weeks[:weekly_cnt]:
            grp = [it for it in all_items if ((it["dt"] - epoch_mon).days // 7) == wk]
            x = next((it for it in grp if re.search(r"(^|_)WEEKLY(_|\.)", it["name"]) and it["path"] not in tags), None)
            if not x and len(grp) >= 2:
                x = next((it for it in grp if it["path"] not in tags), None)
            if x:
                tags[x["path"]] = "WEEKLY"

    cutoff_date = today - timedelta(days=daily_days - 1)
    past_recent = [it for it in all_items if cutoff_date <= it["dt"].date() < today]
    for ymd in list(dict.fromkeys(it["dt"].strftime("%Y-%m-%d") for it in past_recent)):
        grp = [it for it in past_recent if it["dt"].strftime("%Y-%m-%d") == ymd]
        x = next((it for it in grp if it["path"] not in tags), None)
        if x:
            tags[x["path"]] = "DAILY"

    for it in [it for it in all_items if it["dt"].date() == today and it["path"] not in tags][:today_max]:
        tags[it["path"]] = "DAILY"

    if all_items:
        newest = next(iter(all_items))
        if newest["path"] not in tags:
            tags[newest["path"]] = "DAILY"

    keep_items, del_items = [], []
    for it in all_items:
        if it["path"] in tags:
            it["new_tag"] = tags[it["path"]]
            keep_items.append(it)
        else:
            it["new_tag"] = "DELETE"
            del_items.append(it)
    return all_items, keep_items, del_items

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
    for it in keep_items:
        old_p = it["path"]
        old_sha = old_p + ".sha256"
        tg = it["new_tag"]
        d_str = it["dt"].strftime("%Y-%m-%d_%A_%H-%M")
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
            for it in del_items:
                if remove_backup_file(it["path"], del_mode):
                    deleted += 1
                    sha_p = it["path"] + ".sha256"
                    if os.path.exists(sha_p):
                        remove_backup_file(sha_p, del_mode)
            done_lbl = "Видалено з диска назавжди" if del_mode == "permanent" else "Переміщено у Кошик"
            engine.log(f"{done_lbl}: {deleted} файл(ів) ({del_mb} МБ).", "ok")
        else:
            engine.log("Очищення застарілих архівів пропущено.", "info")
    return deleted, renamed, del_mb
