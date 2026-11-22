# ==============================================================================
# patch-id: io-pause-buf128-2.18
# patch-id: stage-window-2.21
# patch-id: adaptive-status-poll-2.11
# [ФАЙЛ: core/backup.py (v2.12 | 22.11.2026 09:10) — АВТОРИЗАЦИЯ, СКАЧИВАНИЕ ZIP, CRC32/SHA-256 И ЗЕРКАЛО]
# ==============================================================================
import os
import re
import json
import time
import zlib
import shutil
import hashlib
import zipfile
import urllib.request
import http.cookiejar
from urllib.parse import urlparse
from datetime import datetime
from core.config import DEFAULT_TOK, SILENT_MODE, NO_CLEAN, commit_state, SCRIPT_VER, get_fast_sysinfo
from core.files import pretty_phase, format_duration, format_backup_dt
from core.network import BROWSER_UA, _seed_cookie, invoke_http, normalize_server_url, verify_host_and_hgm, scan_lan_servers

def _record_cloud_event(engine, operation_id, event, **details):
    try:
        from core.cloud import record_operation_event
        record_operation_event(engine, operation_id, event, **details)
    except Exception as exc:
        engine.log(f"Попередження: не вдалося записати локальний звіт: {exc}", "warn")

def _cloud_sync_warning(engine, prefix, exc):
    from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW
    from core.cloud import CloudRateLimitError, cloud_sync_error_text
    if WINDOWS7_CLOUD_SYNC_PREVIEW and isinstance(exc, CloudRateLimitError):
        engine.log(cloud_sync_error_text(exc, engine.state.get("lang", "en")), "warn")
    else:
        engine.log(f"{prefix}{exc}", "warn")

def _sync_cloud_reports(engine):
    if not engine.state.get("cloud_enabled"):
        return
    try:
        from core.cloud import sync_cloud_reports
        sync_cloud_reports(engine)
    except Exception as exc:
        _cloud_sync_warning(engine, "Попередження: не вдалося передати хмарний звіт: ", exc)
        from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW
        if WINDOWS7_CLOUD_SYNC_PREVIEW:
            from core.cloud import start_cloud_sync_worker
            start_cloud_sync_worker(engine)

def _sync_cloud_backups(engine, prune=False):
    if not engine.state.get("cloud_enabled"):
        return False
    try:
        from core.cloud import sync_cloud_backups
        return sync_cloud_backups(engine, prune=prune) is not False
    except Exception as exc:
        _cloud_sync_warning(engine, "Попередження: не вдалося синхронізувати хмарні архіви: ", exc)
        from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW
        if WINDOWS7_CLOUD_SYNC_PREVIEW:
            from core.cloud import start_cloud_sync_worker
            start_cloud_sync_worker(engine)
        return False

def _desktop_notify(title, text):
    import sys, subprocess
    try:
        if sys.platform.startswith("linux"):
            if (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) and shutil.which("notify-send"):
                subprocess.Popen(
                    ["notify-send", "-a", "HomeGrid Backup", title, text],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
        elif sys.platform == "darwin":
            t_esc = str(title).replace('\\', '\\\\').replace('"', '\\"')
            m_esc = str(text).replace('\\', '\\\\').replace('"', '\\"')
            subprocess.Popen(
                ["osascript", "-e", f'display notification "{m_esc}" with title "{t_esc}"'],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        elif os.name == "nt":
            t_ps = str(title).replace("'", "''")
            m_ps = str(text).replace("'", "''")
            ps_cmd = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$n=New-Object System.Windows.Forms.NotifyIcon;"
                "$n.Icon=[System.Drawing.SystemIcons]::Information;"
                "$n.Visible=$true;"
                f"$n.ShowBalloonTip(5000,'{t_ps}','{m_ps}',[System.Windows.Forms.ToolTipIcon]::Info);"
                "Start-Sleep -Seconds 6;$n.Dispose()"
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=0x08000000
            )
    except Exception:
        pass

def _backup_stage1_prepare(engine, raw_url, force_skip):
    bdir = engine.state["backup_dir"]
    os.makedirs(bdir, exist_ok=True)
    srv, has_bang = normalize_server_url(raw_url if raw_url is not None else engine.state["server"])
    skip_check = force_skip or has_bang

    if not srv:
        engine.log("Адресу не вказано. Запуск автопошуку в LAN...", "info")
        servers = scan_lan_servers(engine)
        if not servers:
            raise RuntimeError("Сервери HomeGrid Monitor у мережі не знайдено.")
        sel_ip, _, _ = next(iter(servers))
        srv = f"http://{sel_ip}:18899"
        engine.log(f"Автоматично обрано сервер: {srv}", "ok")

    parsed = urlparse(srv)
    p_host = parsed.hostname or srv
    c_port = parsed.port or (443 if parsed.scheme == "https" else 80)

    if skip_check:
        engine.log(f"Перевірку сайту/порту пропущено для {p_host}:{c_port}.", "warn")
    else:
        engine.set_progress(5, "Перевірка сайту та сервера HGM...")
        ok_v, _, v_msg, tcp_ping, api_ping = verify_host_and_hgm(engine, srv)
        if not ok_v:
            engine.diag_net = f"{p_host}:{c_port} (ОФЛАЙН)"
            raise RuntimeError(v_msg)
        engine.diag_net = f"{p_host}:{c_port} (ОНЛАЙН)"
        engine.diag_ping = f"TCP {tcp_ping} мс | API {api_ping} мс"
        engine.log(f"Сервер HGM онлайн (TCP: {tcp_ping} мс, API: {api_ping} мс)", "ok")

    if srv != engine.state["server"]:
        engine.state["server"] = srv
        engine.state["dirty"] = True

    engine.set_progress(12, "Перевірка сесії та авторизація...")
    need_login = (engine.state["session_token"] == "")
    if not need_login:
        ts = int(time.time() * 1000)
        _, _, ar_body, _, _, _ = invoke_http(f"{srv}/api/auth/status?_t={ts}", engine.state)
        if not re.search(r'"authenticated"\s*:\s*true', ar_body):
            need_login = True
            engine.state["session_token"] = ""
            engine.log("Збережена сесія застаріла. Повторний вхід...", "warn")

    if need_login:
        while True:
            p1 = engine.state["login_pin"] or engine.ask_modal("pin", "Авторизація HomeGrid", "Введіть LOGIN PIN:")
            if not p1:
                raise RuntimeError("Вхід скасовано (не введено LOGIN PIN).")
            _, _, l_body, l_ses, l_err, _ = invoke_http(
                f"{srv}/api/auth/login", engine.state, "POST", json.dumps({"pin": p1}), srv, f"{srv}/login", 10.0, send_ses=False
            )
            if not l_body:
                raise RuntimeError(f"Мережева помилка під час входу: {l_err}")
            if re.search(r'"ok"\s*:\s*false', l_body):
                engine.log("Невірний LOGIN PIN!", "err")
                engine.state["login_pin"] = ""
                if SILENT_MODE:
                    raise RuntimeError("Збережений LOGIN PIN відхилено сервером.")
                continue
            engine.state["login_pin"] = p1
            engine.state["dirty"] = True
            if l_ses:
                engine.state["session_token"] = l_ses
                engine.log("Авторизація успішна!", "ok")
                break
            if re.search(r'"ok"\s*:\s*true', l_body):
                engine.log("Авторизацію підтверджено сервером!", "ok")
                break
            raise RuntimeError("Сервер не повернув cookie сесії.")
    else:
        engine.log("Активну сесію підтверджено.", "ok")

    engine.set_progress(20, "Запит на підготовку бекапу...")
    _, pr_code, pr_body, _, pr_err, _ = invoke_http(f"{srv}/api/migration/export/prepare", engine.state, "POST", "{}", timeout=15.0)
    tried_login_as_editor = False
    while pr_body and "editor_pin_required" in pr_body:
        if engine.state["editor_pin"]:
            p2 = engine.state["editor_pin"]
        elif not tried_login_as_editor and engine.state["login_pin"]:
            p2 = engine.state["login_pin"]
            tried_login_as_editor = True
        else:
            p2 = engine.ask_modal("pin", "Права редактора", "Для експорту потрібен EDITOR PIN:")
            if not p2:
                raise RuntimeError("Експорт скасовано (не введено EDITOR PIN).")
        _, _, u_body, u_ses, u_err, _ = invoke_http(
            f"{srv}/api/auth/editor/unlock", engine.state, "POST", json.dumps({"pin": p2}), srv, f"{srv}/service.html", 10.0
        )
        if not u_body:
            raise RuntimeError(f"Помилка розблокування редактора: {u_err}")
        if re.search(r'"ok"\s*:\s*false', u_body):
            engine.state["editor_pin"] = ""
            if SILENT_MODE and not tried_login_as_editor:
                raise RuntimeError("Збережений EDITOR PIN відхилено.")
            continue
        engine.state["editor_pin"] = p2
        engine.state["dirty"] = True
        if u_ses:
            engine.state["session_token"] = u_ses
        _, pr_code, pr_body, _, pr_err, _ = invoke_http(f"{srv}/api/migration/export/prepare", engine.state, "POST", "{}", timeout=15.0)

    if not pr_body or not pr_body.strip():
        raise RuntimeError(f"Помилка підготовки (порожня відповідь сервера, HTTP {pr_code}): {pr_err}")
    try:
        pr_data = json.loads(pr_body)
    except Exception:
        snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", pr_body)).strip()[:120]
        raise RuntimeError(f"Сервер повернув некоректну відповідь замість JSON (HTTP {pr_code}): {snippet or 'порожньо'}")
    job_id = pr_data.get("job_id")
    if not job_id:
        raise RuntimeError(f"Сервер не створив завдання експорту: {pr_body[:160]}")
    srv_label = f"{p_host}:{c_port}" if c_port not in (80, 443) else p_host
    return srv, srv_label, job_id

VERIFY_PAUSE_LITE = 0.012  # пауза в LITE, с на каждые 4 МБ (подбирается замером)

def verify_single_archive(zip_path, progress_callback=None, overall_start=0, overall_total=0, buf_size=1048576, cancel_flag=None, io_pause=0.0):
    name = os.path.basename(zip_path)
    if not os.path.isfile(zip_path):
        return {"name": name, "status": "err", "detail": "Файл не знайдено"}
    processed = 0
    since_sleep = 0
    last_rep_t = 0.0
    chunk_sz = max(4096, int(buf_size))

    def report(stage):
        nonlocal last_rep_t
        if not progress_callback:
            return
        now = time.time()
        if (now - last_rep_t) < 0.15:
            return
        last_rep_t = now
        pct = int(min(99, (overall_start + processed) * 100.0 / overall_total)) if overall_total else 0
        progress_callback(pct, f"{stage}: {name}")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            infos = zf.infolist()
            cnt = len(infos)
            if cnt < 1:
                return {"name": name, "status": "err", "detail": "Порожній ZIP-архів"}
            for info in infos:
                crc = 0
                with zf.open(info, "r") as member:
                    while True:
                        if cancel_flag and cancel_flag.get("stop"):
                            return {"name": name, "status": "warn", "detail": "Перевірку перервано"}
                        chunk = member.read(chunk_sz)
                        if not chunk:
                            break
                        crc = zlib.crc32(chunk, crc)
                        processed += len(chunk)
                        since_sleep += len(chunk)
                        if io_pause and since_sleep >= 4194304:
                            since_sleep = 0
                            time.sleep(io_pause)
                        report(f"CRC32 {processed / 1048576.0:.1f} МБ")
                if (crc & 0xFFFFFFFF) != info.CRC:
                    return {"name": name, "status": "err", "detail": f"Пошкоджений CRC32 у файлі: {info.filename}"}
    except Exception as e:
        return {"name": name, "status": "err", "detail": f"Помилка читання ZIP: {e}"}

    sha_path = zip_path + ".sha256"
    if not os.path.exists(sha_path):
        return {"name": name, "status": "warn", "detail": f"ZIP OK ({cnt} файлів), але файл .sha256 відсутній"}

    try:
        with open(sha_path, "r", encoding="utf-8") as fs:
            expected_hash = next(iter(fs.read().split()), "").strip().lower()
        h = hashlib.sha256()
        with open(zip_path, "rb") as f_in:
            while True:
                if cancel_flag and cancel_flag.get("stop"):
                    return {"name": name, "status": "warn", "detail": "Перевірку перервано"}
                blk = f_in.read(chunk_sz)
                if not blk:
                    break
                h.update(blk)
                processed += len(blk)
                since_sleep += len(blk)
                if io_pause and since_sleep >= 4194304:
                    since_sleep = 0
                    time.sleep(io_pause)
                report(f"SHA-256 {processed / 1048576.0:.1f} МБ")
        if h.hexdigest().lower() == expected_hash and expected_hash:
            return {"name": name, "status": "ok", "detail": f"Цілісність 100% підтверджена ({cnt} файлів)"}
        return {"name": name, "status": "err", "detail": "УВАГА! Контрольна сума SHA-256 не збігається"}
    except Exception as e:
        return {"name": name, "status": "err", "detail": f"Помилка перевірки SHA-256: {e}"}

def verify_all_archives(state, progress_callback=None, buf_size=1048576, cancel_flag=None):
    t0 = time.time()
    io_pause = VERIFY_PAUSE_LITE if state.get("lite_mode") else 0.0
    bdir = state["backup_dir"]
    os.makedirs(bdir, exist_ok=True)
    zips = sorted([os.path.join(bdir, f) for f in os.listdir(bdir) if f.lower().endswith(".zip")], key=os.path.getmtime, reverse=True)
    work_sizes = [os.path.getsize(p) * 3 for p in zips]
    total_work, completed_work, results = sum(work_sizes), 0, []
    for index, path in enumerate(zips, 1):
        if cancel_flag and cancel_flag.get("stop"):
            break
        if progress_callback:
            progress_callback(int(completed_work * 100 / max(1, total_work)), f"Архів {index}/{len(zips)}: {os.path.basename(path)}")
        results.append(verify_single_archive(path, progress_callback, completed_work, total_work, buf_size=buf_size, cancel_flag=cancel_flag, io_pause=io_pause))
        completed_work += work_sizes[index - 1]
    elapsed = max(0.001, time.time() - t0)
    total_mb = sum(os.path.getsize(p) for p in zips) / 1048576.0
    speed_mbs = total_mb / elapsed
    return {"total": len(results), "ok_cnt": sum(1 for r in results if r["status"] == "ok"), "warn_cnt": sum(1 for r in results if r["status"] == "warn"), "err_cnt": sum(1 for r in results if r["status"] == "err"), "elapsed": round(elapsed, 2), "speed_mbs": round(speed_mbs, 1), "total_mb": round(total_mb, 1), "cancelled": bool(cancel_flag and cancel_flag.get("stop")), "items": results}

def _copy_to_mirror(engine, out_file, sha_file):
    if not bool(engine.state.get("mirror_enabled", False)):
        return
    mirror_dir = (engine.state.get("mirror_dir") or "").strip()
    if not mirror_dir or mirror_dir in (".", "./", ".\\", "/", "\\"):
        return
    try:
        src_real = os.path.normcase(os.path.realpath(os.path.dirname(out_file)))
        dst_real = os.path.normcase(os.path.realpath(os.path.expanduser(mirror_dir)))
        if src_real == dst_real:
            return
        os.makedirs(dst_real, exist_ok=True)
        shutil.copy2(out_file, os.path.join(dst_real, os.path.basename(out_file)))
        if os.path.exists(sha_file):
            shutil.copy2(sha_file, os.path.join(dst_real, os.path.basename(sha_file)))
        engine.log(f"Дзеркальну копію збережено у: {dst_real}", "ok")
    except Exception as e:
        engine.log(f"Попередження: не вдалося скопіювати у дзеркальну папку ({mirror_dir}): {e}", "warn")

def _download_backup_zip(engine, srv, srv_label, job_id, bdir, operation_id):
    engine.log(f"Збірка архіву на сервері {srv_label}...", "info")
    last_phase = ""
    phase_start_t = time.time()
    srv_times = {"preparing": 0.0, "copying": 0.0, "processing": 0.0, "packing": 0.0, "checking": 0.0}
    tot_b = 0
    job_retries = 0
    bad_json_cnt = 0
    poll_interval = 1.5
    while True:
        time.sleep(poll_interval)
        _, sr_code, sr_body, _, sr_err, _ = invoke_http(f"{srv}/api/migration/export/status?job_id={job_id}", engine.state, timeout=45.0)
        if not sr_body or not sr_body.strip():
            bad_json_cnt += 1
            if bad_json_cnt >= 45:
                raise RuntimeError(f"Сервер {srv_label} перестав відповідати під час збірки (HTTP {sr_code}): {sr_err}")
            time.sleep(1.5)
            continue
        try:
            st = json.loads(sr_body)
            bad_json_cnt = 0
        except Exception:
            bad_json_cnt += 1
            if bad_json_cnt >= 15:
                snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", sr_body)).strip()[:100]
                raise RuntimeError(f"Сайт {srv_label} повернув HTML замість статусу JSON (HTTP {sr_code}): {snippet}")
            time.sleep(0.8)
            continue

        if st.get("ok") is False:
            err_code = st.get("error") or "невідома помилка сервера"
            if err_code == "backup_job_not_found" and job_retries < 4:
                job_retries += 1
                wait_sec = 4 * job_retries
                engine.log(f"Сервер скинув завдання ({srv_label}). Повтор {job_retries}/4 через {wait_sec} с...", "warn")
                for left_s in range(wait_sec, 0, -1):
                    engine.set_progress(22, f"[{srv_label}] Перезапуск збірки ({job_retries}/4) через {left_s} с...")
                    time.sleep(1.0)
                _, _, pr_body2, _, pr_err2, _ = invoke_http(f"{srv}/api/migration/export/prepare", engine.state, "POST", "{}", timeout=20.0)
                if pr_body2 and "editor_pin_required" in pr_body2:
                    pin_ed = engine.state.get("editor_pin") or engine.state.get("login_pin") or ""
                    if pin_ed:
                        _, _, _, u_ses2, _, _ = invoke_http(
                            f"{srv}/api/auth/editor/unlock", engine.state, "POST", json.dumps({"pin": pin_ed}), srv, f"{srv}/service.html", 10.0
                        )
                        if u_ses2:
                            engine.state["session_token"] = u_ses2
                        _, _, pr_body2, _, pr_err2, _ = invoke_http(f"{srv}/api/migration/export/prepare", engine.state, "POST", "{}", timeout=20.0)
                if not pr_body2 or not pr_body2.strip():
                    raise RuntimeError(f"Помилка повторної підготовки: {pr_err2}")
                try:
                    job_id = json.loads(pr_body2).get("job_id")
                except Exception:
                    raise RuntimeError("Сервер повернув некоректну відповідь під час повторного запуску.")
                if not job_id:
                    raise RuntimeError(f"Сервер не створив нове завдання експорту: {pr_body2[:140]}")
                last_phase = ""
                continue
            raise RuntimeError(f"Сервер {srv_label} перервав збірку архіву: {err_code}")

        pct = int(st.get("progress", 0))
        ph = st.get("phase") or "working"
        poll_interval = 1.5 if ph in ("preparing", "ready") else (4.0 if ph in ("checking", "packing") else 2.5)
        tot_b = st.get("total_bytes", 0) or 0
        proc_b = st.get("processed_bytes", 0) or 0
        if ph != last_phase:
            if last_phase:
                phase_duration = max(0.0, time.time() - phase_start_t)
                srv_times[last_phase if last_phase in srv_times else "processing"] += phase_duration
                _record_cloud_event(
                    engine, operation_id, "stage_completed",
                    stage=f"server_{last_phase}", duration_sec=phase_duration
                )
            last_phase = ph
            phase_start_t = time.time()
            _record_cloud_event(engine, operation_id, "stage_started", stage=f"server_{ph}")
            engine.log(f"Етап сервера ({srv_label}): {pretty_phase(ph)}", "info")

        elapsed_ph = max(0.05, time.time() - phase_start_t)
        if tot_b > 0:
            spd_ph = (proc_b / 1048576.0) / elapsed_ph if proc_b > 0 and elapsed_ph > 0.25 else 0.0
            spd_part = f", {spd_ph:.1f} МБ/с" if spd_ph > 0.05 else ""
            sz_txt = f" ({proc_b/1048576:.1f}/{tot_b/1048576:.1f} МБ{spd_part})"
        else:
            sz_txt = ""

        if ph == "checking":
            engine.set_progress(None, f"[{srv_label}] {pretty_phase(ph)} ({elapsed_ph:.1f} с)...")
        else:
            phase_ranges = {"preparing": (25, 30), "copying": (30, 55), "processing": (55, 60), "packing": (60, 75), "ready": (75, 75)}
            p_start, p_end = phase_ranges.get(ph, (25, 75))
            overall_pct = p_start + int((pct / 100.0) * (p_end - p_start))
            engine.set_progress(overall_pct, f"[{srv_label}] {pretty_phase(ph)}: {pct}%{sz_txt}")

        if ph == "ready" or st.get("ready") is True:
            if last_phase and last_phase != "ready":
                phase_duration = max(0.0, time.time() - phase_start_t)
                srv_times[last_phase if last_phase in srv_times else "processing"] += phase_duration
                _record_cloud_event(
                    engine, operation_id, "stage_completed",
                    stage=f"server_{last_phase}", duration_sec=phase_duration
                )
            engine._last_srv_timings = {k: round(v, 1) for k, v in srv_times.items()}
            engine._last_srv_timings["dl_t0"] = time.time()
            engine.set_progress(75, f"[{srv_label}] Архів готовий (75%). Завантаження...")
            break
        if st.get("status") == "error" or ph == "error":
            raise RuntimeError(f"Сервер {srv_label} повідомив про помилку під час створення архіву!")

    date_eng = format_backup_dt(datetime.now())
    out_file = os.path.join(bdir, f"homegrid_backup_DAILY_{date_eng}.zip")
    collision_id = 1
    while os.path.exists(out_file):
        out_file = os.path.join(bdir, f"homegrid_backup_DAILY_{date_eng}_{collision_id}.zip")
        collision_id += 1
    part_file = out_file + ".part"
    cli_tok = engine.state["client_token"] or DEFAULT_TOK
    ses_tok = engine.state["session_token"]
    dt_tok = st.get("download_token") or cli_tok
    du = f"{srv}{st['download_url']}" if st.get("download_url") else f"{srv}/api/migration/export?_t={int(time.time()*1000)}&job_id={job_id}&_download_token={dt_tok}"

    engine.log(f"Завантаження ZIP-архіву з {srv_label}...", "info")
    download_started = time.time()
    _record_cloud_event(engine, operation_id, "stage_started", stage="archive_download")
    eb = float(tot_b) if tot_b > 0 else 0.0
    max_attempts = 7
    retry_delays = (10, 15, 20, 25, 25, 25)
    for attempt in range(1, max_attempts + 1):
        if os.path.exists(part_file):
            os.remove(part_file)
        d0 = time.time()
        dl_ok = False
        dl_err = ""
        net_h = None
        for no_proxy in (True, False):
            try:
                jar = engine.state.get("_jar") or http.cookiejar.CookieJar()
                _seed_cookie(jar, du, "hg_client", cli_tok)
                _seed_cookie(jar, du, "homegrid_dash_session", ses_tok)
                handlers = [urllib.request.HTTPCookieProcessor(jar)]
                if no_proxy:
                    handlers.append(urllib.request.ProxyHandler({}))
                opener = urllib.request.build_opener(*handlers)
                req = urllib.request.Request(du, headers={"User-Agent": BROWSER_UA, "Accept-Encoding": "identity"})
                with opener.open(req, timeout=300) as resp, open(part_file, "wb", buffering=1048576) as out_f:
                    srv_sha = (resp.headers.get("X-Checksum-Sha256") or st.get("sha256") or "").strip().lower()
                    net_h = hashlib.sha256()
                    cb = 0
                    last_ui = time.time()
                    last_speed_t = d0
                    last_speed_bytes = 0
                    smooth_speed = None
                    while True:
                        chunk = resp.read(1048576)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        net_h.update(chunk)
                        cb += len(chunk)
                        now = time.time()
                        if now - last_ui >= 1.0:
                            last_ui = now
                            cm = cb / 1048576.0
                            sample_sec = max(0.001, now - last_speed_t)
                            sample_speed = ((cb - last_speed_bytes) / 1048576.0) / sample_sec
                            smooth_speed = sample_speed if smooth_speed is None else (0.35 * sample_speed + 0.65 * smooth_speed)
                            last_speed_t = now
                            last_speed_bytes = cb
                            speed_txt = f"{smooth_speed:.2f} МБ/с" if smooth_speed >= 1.0 else f"{smooth_speed * 1024:.0f} КБ/с"
                            att_lbl = f" [спроба {attempt}/{max_attempts}]" if attempt > 1 else ""
                            if eb > 0:
                                dpct = min(99, int((cb / eb) * 100))
                                engine.set_progress(75 + int(dpct * 0.17), f"Завантаження{att_lbl}: {cm:.1f}/{eb/1048576.0:.1f} МБ | Швидкість: {speed_txt}")
                            else:
                                engine.set_progress(83, f"Завантаження{att_lbl}: {cm:.1f} МБ | Швидкість: {speed_txt}")
                dl_ok = True
                break
            except Exception as e:
                dl_err = str(e)
                if os.path.exists(part_file):
                    os.remove(part_file)
        actual_sz = os.path.getsize(part_file) if os.path.exists(part_file) else 0
        size_valid = (actual_sz >= int(tot_b * 0.99)) if tot_b > 0 else (actual_sz >= 1024)
        net_sha_hex = net_h.hexdigest().lower() if (dl_ok and net_h is not None) else ""
        if dl_ok and size_valid and srv_sha and len(srv_sha) == 64 and net_sha_hex != srv_sha:
            dl_ok = False
            dl_err = "SHA-256 не збігається з контрольним хешем сервера"
            if os.path.exists(part_file):
                os.remove(part_file)
        if dl_ok and size_valid:
            os.replace(part_file, out_file)
            download_duration = time.time() - download_started
            engine.log(f"Архів завантажено: {actual_sz / 1048576.0:.2f} МБ за {round(download_duration, 1)} с", "ok")
            _record_cloud_event(
                engine, operation_id, "stage_completed", stage="archive_download",
                archive=out_file, size_mb=actual_sz / 1048576.0,
                size_bytes=actual_sz, duration_sec=download_duration,
                speed_mbps=(actual_sz / 1048576.0) / max(download_duration, 0.001)
            )
            return out_file, net_sha_hex
        if dl_ok and not size_valid:
            dl_err = f"завантажено лише {actual_sz/1048576.0:.1f} із {tot_b/1048576.0:.1f} МБ (обрив потоку)"
            if os.path.exists(part_file):
                os.remove(part_file)
        if attempt < max_attempts:
            wait_s = retry_delays[min(attempt - 1, len(retry_delays) - 1)]
            engine.log(f"Збій завантаження ({dl_err}). Повтор {attempt + 1}/{max_attempts} через {wait_s} с...", "warn")
            for left_s in range(wait_s, 0, -1):
                engine.set_progress(75, f"Очікування мережі: повтор {attempt + 1}/{max_attempts} через {left_s} с...")
                time.sleep(1.0)
        else:
            raise RuntimeError(f"Помилка завантаження після {max_attempts} спроб: {dl_err}")

def run_backup_task(engine, raw_url=None, force_skip=False, skip_cleanup=False, auto_quiet=False):
    with engine.lock:
        if engine.is_running:
            return
        engine.is_running = True
    engine.set_pill("Резервне копіювання...", "work")
    t_total_start = time.time()
    ts_start_str = datetime.now().strftime("%H:%M:%S")
    from core.cloud import new_operation_id
    operation_id = new_operation_id()
    out_file = ""
    total_mb = 0.0
    _record_cloud_event(
        engine, operation_id, "started", stage="server_connection",
        archive_sequence=max(0, int(engine.state.get("all_time_cnt", 0))) + 1
    )
    try:
        bdir = engine.state["backup_dir"]
        t_prep0 = time.time()
        _record_cloud_event(engine, operation_id, "stage_started", stage="server_connection_and_preparation")
        srv, srv_label, job_id = _backup_stage1_prepare(engine, raw_url, force_skip)
        _record_cloud_event(
            engine, operation_id, "stage_completed", stage="server_connection_and_preparation",
            duration_sec=time.time() - t_prep0, result="success"
        )
        t_dl0 = time.time()
        _record_cloud_event(engine, operation_id, "milestone", stage="server_job_ready")
        out_file, net_sha_hex = _download_backup_zip(engine, srv, srv_label, job_id, bdir, operation_id)
        t_ver0 = time.time()

        total_bytes = os.path.getsize(out_file)
        total_mb = total_bytes / 1048576.0
        _record_cloud_event(engine, operation_id, "stage_started", stage="archive_crc32_verification", archive=out_file)
        engine.set_progress(None, f"Перевірка CRC32 ({total_mb:.1f} МБ)...")
        with zipfile.ZipFile(out_file, "r") as zf:
            infos = zf.infolist()
            cnt = len(infos)
            if cnt < 1:
                os.remove(out_file)
                raise RuntimeError("ZIP-архів порожній!")
            for info in infos:
                crc = 0
                with zf.open(info, "r") as member:
                    for chunk in iter(lambda: member.read(1048576), b""):
                        crc = zlib.crc32(chunk, crc)
                if (crc & 0xFFFFFFFF) != info.CRC:
                    os.remove(out_file)
                    raise RuntimeError(f"Пошкоджений файл в архіві: {info.filename}")
        t_sha0 = time.time()
        crc_duration = max(0.001, t_sha0 - t_ver0)
        crc_sec = round(max(0.1, crc_duration), 1)
        _record_cloud_event(
            engine, operation_id, "stage_completed", stage="archive_crc32_verification",
            archive=out_file, duration_sec=crc_duration, files_count=cnt
        )

        _record_cloud_event(engine, operation_id, "stage_started", stage="archive_sha256_verification", archive=out_file)
        h = hashlib.sha256()
        processed = 0
        last_ui = time.time()
        with open(out_file, "rb") as f_in:
            for blk in iter(lambda: f_in.read(1048576), b""):
                h.update(blk)
                processed += len(blk)
                if time.time() - last_ui >= 0.8:
                    last_ui = time.time()
                    pct = 92 + int((processed / max(1, total_bytes)) * 5)
                    engine.set_progress(pct, f"Розрахунок SHA-256: {processed / 1048576.0:.1f} / {total_mb:.1f} МБ")

        disk_sha_low = h.hexdigest().lower()
        if net_sha_hex and disk_sha_low != net_sha_hex:
            os.remove(out_file)
            raise RuntimeError("Помилка запису на диск: SHA-256 файлу на носії не збігається зі завантаженим потоком!")
        zip_hash = disk_sha_low.upper()
        sha_file = out_file + ".sha256"
        with open(sha_file, "w", encoding="utf-8") as f_sha:
            f_sha.write(f"{zip_hash.lower()}  {os.path.basename(out_file)}\n")
        sha_duration = max(0.001, time.time() - t_sha0)
        sha_sec = round(max(0.1, sha_duration), 1)
        ver_sec = round(crc_sec + sha_sec, 1)
        engine.log(f"Цілісність перевірено ({cnt} файлів) за {ver_sec} с. Збережено {os.path.basename(sha_file)}", "ok")
        _record_cloud_event(
            engine, operation_id, "stage_completed", stage="archive_sha256_verification",
            archive=out_file, size_mb=total_mb, duration_sec=sha_duration, files_count=cnt,
            size_bytes=total_bytes
        )

        mir_active = bool(engine.state.get("mirror_enabled", False)) and bool((engine.state.get("mirror_dir") or "").strip())
        mir_sec = 0.0
        if mir_active:
            t_mir0 = time.time()
            _record_cloud_event(engine, operation_id, "stage_started", stage="local_mirror", archive=out_file)
            _copy_to_mirror(engine, out_file, sha_file)
            mir_duration = max(0.001, time.time() - t_mir0)
            mir_sec = round(max(0.1, mir_duration), 1)
            _record_cloud_event(
                engine, operation_id, "stage_completed", stage="local_mirror",
                archive=out_file, duration_sec=mir_duration
            )

        if engine.state["dirty"]:
            commit_state(engine.state)
            engine.log("Налаштування та ключі захищено збережено.", "ok")

        from core.gfs import compute_gfs_plan, apply_gfs_cleanup
        engine.set_progress(98, "Ротація бекапів за обраною стратегією...")
        gfs_started = time.time()
        _record_cloud_event(engine, operation_id, "stage_started", stage="gfs_rotation", archive=out_file)
        _, _, del_it = compute_gfs_plan(engine.state)
        old_cnt_before = len(del_it)
        gfs_cleanup_applied = False
        if not skip_cleanup and not NO_CLEAN and (auto_quiet or bool(engine.state.get("silent_cleanup", False))):
            deleted_count, _, _ = apply_gfs_cleanup(engine, skip_prompt=True, sync_cloud=False)
            gfs_cleanup_applied = deleted_count == len(del_it)
        _record_cloud_event(
            engine, operation_id, "stage_completed", stage="gfs_rotation",
            archive=out_file, duration_sec=time.time() - gfs_started
        )
        cloud_sync_started = time.time()
        cloud_synced = _sync_cloud_backups(engine, prune=gfs_cleanup_applied)
        _record_cloud_event(
            engine, operation_id, "stage_completed", stage="cloud_archive_sync",
            archive=out_file, duration_sec=time.time() - cloud_sync_started,
            result="success" if cloud_synced else ("disabled" if not engine.state.get("cloud_enabled") else "failed")
        )

        t_end = time.time()
        ts_end_str = datetime.now().strftime("%H:%M:%S")
        _st_t = getattr(engine, "_last_srv_timings", {})
        dl_t0_real = _st_t.get("dl_t0", t_dl0)
        dl_sec = round(max(0.1, t_ver0 - dl_t0_real), 1)
        srv_prep_s = round(_st_t.get("preparing", 0.0), 1)
        srv_copy_s = round(_st_t.get("copying", 0.0), 1)
        srv_pack_s = round(_st_t.get("packing", 0.0), 1)
        srv_proc_s = round(_st_t.get("processing", 0.0), 1)
        srv_chk_s = round(_st_t.get("checking", 0.0), 1)
        total_sec = round(max(0.1, t_end - t_total_start), 1)
        srv_sec = round(srv_prep_s + srv_copy_s + srv_proc_s + srv_pack_s + srv_chk_s, 1)
        spd_mbs = round(total_mb / max(0.1, dl_sec), 1)
        final_name = os.path.basename(out_file)
        engine.set_progress(100, f"Готово! Архів збережено ({total_mb:.2f} МБ)")
        engine.set_pill(f"ГОТОВО | {total_mb:.1f} МБ", "ok")
        tot_fmt = format_duration(total_sec, engine.state.get("lang", "en"))
        engine.log(f"УСПІХ! Резервне копіювання завершено за {tot_fmt} ({ts_start_str} → {ts_end_str}).", "ok")
        engine.log(f"[SUMMARY] v{SCRIPT_VER} | {get_fast_sysinfo()} | download {spd_mbs} MB/s ({dl_sec} s) | server {srv_sec} s | total {total_sec} s | files {cnt}", "info")
        from core.i18n import tr as _tr_n
        _lng_n = engine.state.get("lang", "en")
        _desktop_notify("HomeGrid Backup", _tr_n(f"Резервну копію створено: {final_name} ({total_mb:.1f} МБ)", _lng_n))
        engine.state["all_time_cnt"] = max(int(engine.state.get("all_time_cnt", 0)), 0) + 1
        engine.state["all_time_mb"] = round(max(float(engine.state.get("all_time_mb", 0.0)), 0.0) + total_mb, 1)
        commit_state(engine.state)
        if hasattr(engine, "record_op_event"):
            engine.record_op_event("Успішно", final_name, round(total_mb, 1), dur_sec=total_sec)
        _record_cloud_event(
            engine, operation_id, "success", archive=final_name,
            size_mb=total_mb, size_bytes=total_bytes, files_count=cnt,
            duration_sec=t_end - t_total_start,
            speed_mbps=total_mb / max(t_end - t_total_start, 0.001)
        )
        _sync_cloud_reports(engine)
        if not SILENT_MODE and not auto_quiet:
            z_cnt, z_mb, free_gb = engine.get_storage_stats()
            rep = {"file": final_name, "srv": srv, "size_mb": round(total_mb, 2), "files_cnt": cnt, "ts_start": ts_start_str, "ts_end": ts_end_str, "total_sec": total_sec, "srv_prep_sec": srv_prep_s, "srv_copy_sec": srv_copy_s, "srv_proc_sec": srv_proc_s, "srv_pack_sec": srv_pack_s, "srv_chk_sec": srv_chk_s, "dl_sec": dl_sec, "spd_mbs": spd_mbs, "crc_sec": crc_sec, "sha_sec": sha_sec, "mir_active": mir_active, "mir_sec": mir_sec, "z_cnt": z_cnt, "z_mb": z_mb, "free_gb": free_gb, "old_cnt": old_cnt_before}
            engine.ask_modal("backup_report", "Звіт про резервне копіювання", json.dumps(rep, ensure_ascii=False))
    except Exception as exc:
        engine.exit_code = 1
        engine.log(f"ПОМИЛКА: {exc}", "err")
        from core.i18n import tr as _tr_e
        _desktop_notify(_tr_e("HomeGrid Backup: помилка", engine.state.get("lang", "en")), str(exc)[:200])
        engine.set_pill("Помилка бекапу", "err")
        if hasattr(engine, "record_op_event"):
            engine.record_op_event("Помилка", str(exc), 0.0, dur_sec=round(time.time() - t_total_start, 1))
        _record_cloud_event(
            engine, operation_id, "error", archive=out_file,
            size_mb=total_mb, duration_sec=time.time() - t_total_start,
            result="error", error_type=type(exc).__name__
        )
        _sync_cloud_reports(engine)
        engine.set_progress(0, f"Помилка: {exc}")
        if not SILENT_MODE:
            engine.ask_modal("alert", "Помилка резервного копіювання", str(exc))
    finally:
        with engine.lock:
            engine.is_running = False
            engine.indeterminate = False