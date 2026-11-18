# ==============================================================================
# [ФАЙЛ: core/backup.py (v1.018 | 18.11.2026 20:19) — АВТОРИЗАЦИЯ, СКАЧИВАНИЕ ZIP, CRC32/SHA-256 И ЗЕРКАЛО]
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
from core.config import DEFAULT_TOK, SILENT_MODE, NO_CLEAN, commit_state
from core.files import pretty_phase
from core.network import BROWSER_UA, _seed_cookie, invoke_http, normalize_server_url, verify_host_and_hgm, scan_lan_servers

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

def verify_single_archive(zip_path, progress_callback=None, overall_start=0, overall_total=0):
    name = os.path.basename(zip_path)
    if not os.path.isfile(zip_path):
        return {"name": name, "status": "err", "detail": "Файл не знайдено"}
    processed = 0

    def report(stage):
        if progress_callback:
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
                        chunk = member.read(1024 * 1024)
                        if not chunk:
                            break
                        crc = zlib.crc32(chunk, crc)
                        processed += len(chunk)
                        report(f"CRC32 {processed / 1048576.0:.1f} МБ")
                if (crc & 0xFFFFFFFF) != info.CRC:
                    return {"name": name, "status": "err", "detail": f"Пошкоджений CRC32 у файлі: {info.filename}"}
                if info.file_size == 0:
                    report("CRC32")
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
                blk = f_in.read(1024 * 1024)
                if not blk:
                    break
                h.update(blk)
                processed += len(blk)
                report(f"SHA-256 {processed / 1048576.0:.1f} МБ")
        actual_hash = h.hexdigest().lower()
        if expected_hash and actual_hash == expected_hash:
            return {"name": name, "status": "ok", "detail": f"Цілісність 100% підтверджена ({cnt} файлів, SHA-256 збігається)"}
        return {"name": name, "status": "err", "detail": "УВАГА! Контрольна сума SHA-256 не збігається (файл змінено або пошкоджено)"}
    except Exception as e:
        return {"name": name, "status": "err", "detail": f"Помилка перевірки SHA-256: {e}"}

def verify_all_archives(state, progress_callback=None):
    bdir = state["backup_dir"]
    os.makedirs(bdir, exist_ok=True)
    zips = sorted(
        [os.path.join(bdir, f) for f in os.listdir(bdir) if f.lower().endswith(".zip")],
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )
    work_sizes = []
    for path in zips:
        try:
            with zipfile.ZipFile(path, "r") as zf:
                crc_size = sum(i.file_size for i in zf.infolist())
        except Exception:
            crc_size = 0
        try:
            sha_size = os.path.getsize(path) if os.path.exists(path + ".sha256") else 0
        except OSError:
            sha_size = 0
        work_sizes.append(crc_size + sha_size)
    total_work = sum(work_sizes)
    completed_work = 0
    results = []
    for index, path in enumerate(zips, 1):
        if progress_callback:
            progress_callback(int(completed_work * 100 / total_work) if total_work else int((index - 1) * 100 / max(1, len(zips))),
                              f"Архив {index}/{len(zips)}: {os.path.basename(path)}")
        results.append(verify_single_archive(path, progress_callback, completed_work, total_work))
        completed_work += work_sizes[index - 1]
    if progress_callback:
        progress_callback(100, f"Перевірку завершено: {len(zips)} архівів")
    ok_cnt = sum(1 for r in results if r["status"] == "ok")
    warn_cnt = sum(1 for r in results if r["status"] == "warn")
    err_cnt = sum(1 for r in results if r["status"] == "err")
    return {"total": len(results), "ok_cnt": ok_cnt, "warn_cnt": warn_cnt, "err_cnt": err_cnt, "items": results}

def _copy_to_mirror(engine, out_file, sha_file):
    if not engine.state.get("mirror_enabled", True):
        return
    mirror_dir = (engine.state.get("mirror_dir") or "").strip()
    if not mirror_dir:
        return
    try:
        if os.path.normcase(os.path.abspath(mirror_dir)) == os.path.normcase(os.path.abspath(os.path.dirname(out_file))):
            return
        os.makedirs(mirror_dir, exist_ok=True)
        dst_zip = os.path.join(mirror_dir, os.path.basename(out_file))
        dst_sha = os.path.join(mirror_dir, os.path.basename(sha_file))
        shutil.copy2(out_file, dst_zip)
        if os.path.exists(sha_file):
            shutil.copy2(sha_file, dst_sha)
        engine.log(f"Дзеркальну копію збережено у: {mirror_dir}", "ok")
    except Exception as e:
        engine.log(f"Попередження: не вдалося скопіювати у дзеркальну папку ({mirror_dir}): {e}", "warn")

def _download_backup_zip(engine, srv, srv_label, job_id, bdir):
    engine.log(f"Збірка архіву на сервері {srv_label}...", "info")
    last_phase = ""
    phase_start_t = time.time()
    tot_b = 0
    job_retries = 0
    bad_json_cnt = 0
    while True:
        time.sleep(0.35)
        _, sr_code, sr_body, _, sr_err, _ = invoke_http(f"{srv}/api/migration/export/status?job_id={job_id}", engine.state, timeout=12.0)
        if not sr_body or not sr_body.strip():
            bad_json_cnt += 1
            if bad_json_cnt >= 15:
                raise RuntimeError(f"Сервер {srv_label} перестав відповідати під час збірки (HTTP {sr_code}): {sr_err}")
            time.sleep(0.8)
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
            if err_code == "backup_job_not_found" and job_retries < 1:
                job_retries += 1
                engine.log("Сервер скинув завдання. Повторний запуск збірки...", "warn")
                _, _, pr_body2, _, pr_err2, _ = invoke_http(f"{srv}/api/migration/export/prepare", engine.state, "POST", "{}", timeout=15.0)
                if not pr_body2 or not pr_body2.strip():
                    raise RuntimeError(f"Помилка повторної підготовки: {pr_err2}")
                try:
                    job_id = json.loads(pr_body2).get("job_id")
                except Exception:
                    raise RuntimeError("Сервер повернув некоректну відповідь під час повторного запуску.")
                last_phase = ""
                continue
            raise RuntimeError(f"Сервер {srv_label} перервав збірку архіву: {err_code}")

        pct = int(st.get("progress", 0))
        ph = st.get("phase") or "working"
        tot_b = st.get("total_bytes", 0) or 0
        proc_b = st.get("processed_bytes", 0) or 0
        if ph != last_phase:
            last_phase = ph
            phase_start_t = time.time()
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
            phase_ranges = {"preparing": (25, 30), "copying": (30, 55), "packing": (55, 75), "ready": (75, 75)}
            p_start, p_end = phase_ranges.get(ph, (25, 75))
            overall_pct = p_start + int((pct / 100.0) * (p_end - p_start))
            engine.set_progress(overall_pct, f"[{srv_label}] {pretty_phase(ph)}: {pct}%{sz_txt}")

        if ph == "ready" or st.get("ready") is True:
            engine.set_progress(75, f"[{srv_label}] Архів готовий (75%). Завантаження...")
            break
        if st.get("status") == "error" or ph == "error":
            raise RuntimeError(f"Сервер {srv_label} повідомив про помилку під час створення архіву!")

    date_eng = datetime.now().strftime("%Y-%m-%d_%A_%H-%M")
    out_file = os.path.join(bdir, f"homegrid_backup_DAILY_{date_eng}.zip")
    cli_tok = engine.state["client_token"] or DEFAULT_TOK
    ses_tok = engine.state["session_token"]
    dt_tok = st.get("download_token") or cli_tok
    du = f"{srv}{st['download_url']}" if st.get("download_url") else f"{srv}/api/migration/export?_t={int(time.time()*1000)}&job_id={job_id}&_download_token={dt_tok}"

    engine.log(f"Завантаження ZIP-архіву з {srv_label}...", "info")
    eb = float(tot_b) if tot_b > 0 else 0.0
    max_attempts = 7
    retry_delays = (10, 15, 20, 25, 25, 25)
    for attempt in range(1, max_attempts + 1):
        if os.path.exists(out_file):
            os.remove(out_file)
        d0 = time.time()
        dl_ok = False
        dl_err = ""
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
                with opener.open(req, timeout=300) as resp, open(out_file, "wb") as out_f:
                    cb = 0
                    last_ui = time.time()
                    last_speed_t = d0
                    last_speed_bytes = 0
                    smooth_speed = None
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        out_f.write(chunk)
                        cb += len(chunk)
                        now = time.time()
                        if now - last_ui >= 0.2:
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
                if os.path.exists(out_file):
                    os.remove(out_file)
        actual_sz = os.path.getsize(out_file) if os.path.exists(out_file) else 0
        size_valid = (actual_sz >= int(tot_b * 0.99)) if tot_b > 0 else (actual_sz >= 1024)
        if dl_ok and size_valid:
            engine.log(f"Архів завантажено: {actual_sz / 1048576.0:.2f} МБ за {round(time.time() - d0, 1)} с", "ok")
            return out_file
        if dl_ok and not size_valid:
            dl_err = f"завантажено лише {actual_sz/1048576.0:.1f} із {tot_b/1048576.0:.1f} МБ (обрив потоку)"
            if os.path.exists(out_file):
                os.remove(out_file)
        if attempt < max_attempts:
            wait_s = retry_delays[min(attempt - 1, len(retry_delays) - 1)]
            engine.log(f"Збій завантаження ({dl_err}). Повтор {attempt + 1}/{max_attempts} через {wait_s} с...", "warn")
            for left_s in range(wait_s, 0, -1):
                engine.set_progress(75, f"Очікування мережі: повтор {attempt + 1}/{max_attempts} через {left_s} с...")
                time.sleep(1.0)
        else:
            raise RuntimeError(f"Помилка завантаження після {max_attempts} спроб: {dl_err}")

def run_backup_task(engine, raw_url=None, force_skip=False, skip_cleanup=False, auto_quiet=False):
    if engine.is_running:
        return
    engine.is_running = True
    engine.set_pill("Резервне копіювання...", "work")
    t_total_start = time.time()
    try:
        bdir = engine.state["backup_dir"]
        srv, srv_label, job_id = _backup_stage1_prepare(engine, raw_url, force_skip)
        out_file = _download_backup_zip(engine, srv, srv_label, job_id, bdir)

        total_bytes = os.path.getsize(out_file)
        total_mb = total_bytes / 1048576.0
        engine.set_progress(None, f"Перевірка CRC32 ({total_mb:.1f} МБ)...")
        with zipfile.ZipFile(out_file, "r") as zf:
            bad_file = zf.testzip()
            if bad_file is not None:
                os.remove(out_file)
                raise RuntimeError(f"Пошкоджений файл в архіві: {bad_file}")
            cnt = len(zf.namelist())
        if cnt < 1:
            os.remove(out_file)
            raise RuntimeError("ZIP-архів порожній!")

        h = hashlib.sha256()
        processed = 0
        last_ui = time.time()
        with open(out_file, "rb") as f_in:
            for blk in iter(lambda: f_in.read(65536), b""):
                h.update(blk)
                processed += len(blk)
                if time.time() - last_ui >= 0.15:
                    last_ui = time.time()
                    pct = 92 + int((processed / max(1, total_bytes)) * 5)
                    engine.set_progress(pct, f"Розрахунок SHA-256: {processed / 1048576.0:.1f} / {total_mb:.1f} МБ")

        zip_hash = h.hexdigest().upper()
        sha_file = out_file + ".sha256"
        with open(sha_file, "w", encoding="utf-8") as f_sha:
            f_sha.write(f"{zip_hash.lower()}  {os.path.basename(out_file)}\n")
        engine.log(f"Цілісність перевірено ({cnt} файлів). Збережено {os.path.basename(sha_file)}", "ok")

        _copy_to_mirror(engine, out_file, sha_file)

        if engine.state["dirty"]:
            commit_state(engine.state)
            engine.log("Налаштування та ключі захищено збережено.", "ok")

        if skip_cleanup or NO_CLEAN:
            engine.set_progress(98, "Старі копії збережено (авторежим без видалення)...")
            engine.log("Режим збереження: очищення застарілих архівів пропущено.", "info")
        else:
            from core.gfs import apply_gfs_cleanup
            engine.set_progress(98, "Ротація бекапів за обраною стратегією...")
            apply_gfs_cleanup(engine, skip_prompt=auto_quiet)

        total_sec = round(time.time() - t_total_start, 1)
        engine.set_progress(100, f"Готово! Архів збережено ({total_mb:.2f} МБ)")
        engine.set_pill(f"ГОТОВО | {total_mb:.1f} МБ", "ok")
        engine.log(f"УСПІХ! Резервне копіювання завершено за {total_sec} с.", "ok")
        if hasattr(engine, "record_op_event"):
            engine.record_op_event("Успішно", f"{os.path.basename(out_file)} ({total_sec} с)", round(total_mb, 1))
    except Exception as exc:
        engine.exit_code = 1
        engine.log(f"ПОМИЛКА: {exc}", "err")
        engine.set_pill("Помилка бекапу", "err")
        if hasattr(engine, "record_op_event"):
            engine.record_op_event("Помилка", str(exc)[:65], 0.0)
        engine.set_progress(0, f"Помилка: {exc}")
        if not SILENT_MODE:
            engine.ask_modal("alert", "Помилка резервного копіювання", str(exc))
    finally:
        with engine.lock:
            engine.is_running = False
            engine.indeterminate = False
