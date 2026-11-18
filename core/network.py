# ==============================================================================
# [ФАЙЛ: core/network.py (v1.1) — HTTP, PING, TCP, ВЕРИФИКАЦИЯ HGM И СКАНЕР LAN]
# ==============================================================================
import re
import json
import time
import socket
import ipaddress
import subprocess
import urllib.request
import urllib.error
import http.cookiejar
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from core.config import DEFAULT_TOK, SILENT_MODE, commit_state, record_server_history

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

def _seed_cookie(jar, url, name, value):
    if not value:
        return
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not host:
        return
    for ck in list(jar):
        if ck.name == name and ck.domain == host:
            ck.value = value
            return
    ck = http.cookiejar.Cookie(
        version=0, name=name, value=value, port=None, port_specified=False,
        domain=host, domain_specified=False, domain_initial_dot=False,
        path="/", path_specified=True, secure=(parsed.scheme == "https"),
        expires=None, discard=True, comment=None, comment_url=None, rest={}, rfc2109=False
    )
    jar.set_cookie(ck)

def invoke_http(url, state, method="GET", body=None, origin="", ref="", timeout=10.0, send_cli=True, send_ses=True):
    cli_tok = state["client_token"] or DEFAULT_TOK
    ses_tok = state["session_token"] if send_ses else ""
    jar = state.get("_jar")
    if jar is None:
        jar = http.cookiejar.CookieJar()
        state["_jar"] = jar

    if send_cli and cli_tok:
        _seed_cookie(jar, url, "hg_client", cli_tok)
    if ses_tok:
        _seed_cookie(jar, url, "homegrid_dash_session", ses_tok)
    else:
        for ck in list(jar):
            if ck.name == "homegrid_dash_session":
                jar.clear(ck.domain, ck.path, ck.name)

    for no_proxy in (True, False):
        t0 = time.time()
        try:
            handlers = [urllib.request.HTTPCookieProcessor(jar)]
            if no_proxy:
                handlers.append(urllib.request.ProxyHandler({}))
            opener = urllib.request.build_opener(*handlers)

            headers = {
                "User-Agent": BROWSER_UA,
                "Accept": "application/json, text/html, */*",
                "Accept-Encoding": "identity",
                "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
            }
            if origin:
                headers["Origin"] = origin
            if ref:
                headers["Referer"] = ref
            data = body.encode("utf-8") if body is not None else None
            if data is not None:
                headers["Content-Type"] = "application/json"

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with opener.open(req, timeout=timeout) as resp:
                txt = resp.read().decode("utf-8", errors="replace")
                lat_ms = round((time.time() - t0) * 1000, 1)
                new_ses = new_cli = ""
                for ck in jar:
                    if ck.name == "homegrid_dash_session" and ck.value:
                        new_ses = ck.value
                    elif ck.name == "hg_client" and ck.value:
                        new_cli = ck.value

                for h_name, h_val in resp.headers.items():
                    if h_name.lower() == "set-cookie":
                        if not new_ses and "homegrid_dash_session=" in h_val:
                            m = re.search(r"homegrid_dash_session=([^;]+)", h_val)
                            if m:
                                new_ses = m.group(1).strip()
                                _seed_cookie(jar, url, "homegrid_dash_session", new_ses)
                        if not new_cli and "hg_client=" in h_val:
                            m2 = re.search(r"hg_client=([^;]+)", h_val)
                            if m2:
                                new_cli = m2.group(1).strip()
                                _seed_cookie(jar, url, "hg_client", new_cli)

                if new_cli and new_cli != state["client_token"]:
                    state["client_token"] = new_cli
                    state["dirty"] = True
                if new_ses and new_ses != state["session_token"]:
                    state["session_token"] = new_ses
                    state["dirty"] = True
                return True, resp.status, txt, new_ses, "", lat_ms
        except urllib.error.HTTPError as e:
            lat_ms = round((time.time() - t0) * 1000, 1)
            txt = e.read().decode("utf-8", errors="replace") if e.fp else ""
            if e.headers:
                for h_name, h_val in e.headers.items():
                    if h_name.lower() == "set-cookie":
                        m2 = re.search(r"hg_client=([^;]+)", h_val)
                        if m2 and m2.group(1).strip() != state["client_token"]:
                            state["client_token"] = m2.group(1).strip()
                            state["dirty"] = True
            return False, e.code, txt, "", str(e), lat_ms
        except Exception as e:
            if not no_proxy:
                return False, 0, "", "", str(e), 0.0
    return False, 0, "", "", "Помилка мережі", 0.0

def ping_host(host, timeout_ms=2000):
    t0 = time.time()
    try:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
        res = subprocess.run(
            cmd, stdin=subprocess.DEVNULL, capture_output=True, encoding="cp866", errors="replace", timeout=4, creationflags=0x08000000
        )
        if res.returncode == 0:
            m = re.search(r"time[=<]\s*([\d.,]+)\s*ms", res.stdout or "", re.I)
            if m:
                return True, round(float(m.group(1).replace(",", ".")), 1)
            return True, round((time.time() - t0) * 1000, 1)
    except Exception:
        pass
    return False, 0.0

def test_tcp_port(host, port, timeout=2.5):
    t0 = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, round((time.time() - t0) * 1000, 1)
    except Exception:
        return False, 0.0

def test_hgm_stage2(base_url, state, timeout=6.0):
    ts = int(time.time() * 1000)
    ok, code, body, _, _, lat = invoke_http(
        f"{base_url}/api/auth/status?_t={ts}", state, timeout=timeout, send_cli=True, send_ses=False
    )
    if ok and code == 200 and body:
        try:
            data = json.loads(body)
            if isinstance(data, dict) and isinstance(data.get("authenticated"), bool):
                return True, lat
        except Exception:
            pass

    _, code_l, html_l, _, _, lat_l = invoke_http(
        f"{base_url}/login", state, timeout=timeout, send_cli=True, send_ses=False
    )
    if code_l == 200 and html_l:
        has_title = bool(re.search(r"HomeGrid\s+Monitor", html_l, re.I))
        has_signature = bool(re.search(r"PV\s+аналітики|PIN-захист|hg_client|DashboardPanelHeader", html_l, re.I))
        if has_title and has_signature:
            return True, (lat_l or lat)

    return False, 0.0

def get_main_subnets():
    networks = set()
    candidate_ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            _, _, _, _, sockaddr = info
            ip_val, _ = sockaddr
            candidate_ips.append(ip_val)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_val, _ = s.getsockname()
        candidate_ips.append(ip_val)
        s.close()
    except Exception:
        pass

    for ip_str in candidate_ips:
        try:
            ip_obj = ipaddress.IPv4Address(ip_str)
            if ip_obj.is_private and not ip_obj.is_loopback and not ip_obj.is_link_local:
                net = ipaddress.IPv4Network(f"{ip_str}/24", strict=False)
                prefix, _ = str(net.network_address).rsplit(".", 1)
                networks.add(prefix)
        except ValueError:
            continue
    return sorted(networks)

def normalize_server_url(raw):
    s = (raw or "").strip()
    skip = "!" in s
    s = s.replace("!", "").strip().rstrip("/")
    if not s:
        return "", skip

    if "://" not in s and "." not in s and ":" not in s and s.lower() != "localhost":
        return f"https://{s}.homegridmonitor.com", skip

    if not re.match(r"^https?://", s, re.I):
        host_only, _, _ = s.partition(":")
        is_ip = bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host_only))
        s = f"http://{s}" if (is_ip or "." not in host_only) else f"https://{s}"
    parsed = urlparse(s)
    host = parsed.hostname or ""
    if not host:
        return "", skip
    if parsed.port:
        return f"{parsed.scheme.lower()}://{host}:{parsed.port}", skip
    if parsed.scheme.lower() == "https":
        return f"https://{host}", skip
    is_ip = bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host))
    if is_ip or "." not in host:
        return f"http://{host}:18899", skip
    return f"http://{host}", skip

def verify_host_and_hgm(engine, srv_url):
    parsed = urlparse(srv_url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        socket.getaddrinfo(host, port)
    except socket.gaierror:
        return False, "DNS_FAIL", f"Сайт/домен '{host}' не знайдено (помилка DNS).", 0.0, 0.0

    ping_ok, ping_ms = ping_host(host, 2000)
    if ping_ok:
        engine.log(f"ICMP Ping до {host}: {ping_ms} мс", "info")
    else:
        engine.log(f"ICMP Ping до {host} без відповіді, перевірка з'єднання ({port})...", "warn")

    ok_tcp, tcp_ms = test_tcp_port(host, port, 3.5)
    if not ok_tcp:
        return False, "TCP_FAIL", f"Хост '{host}' існує, але порт {port} закритий або недоступний.", 0.0, 0.0

    ok_api, api_ms = test_hgm_stage2(srv_url, engine.state, 7.0)
    if not ok_api:
        return False, "NOT_HGM", f"Сайт '{host}' доступний, але це НЕ сервер HomeGrid Monitor!", tcp_ms, 0.0

    return True, "OK", f"{host}:{port}", (ping_ms if ping_ok else tcp_ms), api_ms

def scan_lan_servers(engine):
    subs = get_main_subnets()
    if not subs:
        engine.log("Активні мережеві адаптери LAN не знайдено!", "err")
        return []
    engine.log("Сканування підмереж: " + ", ".join(f"{s}.0/24" for s in subs), "info")
    found = []
    for pref in subs:
        engine.set_progress(None, f"Сканування {pref}.1-254...")
        ips = [f"{pref}.{i}" for i in range(1, 255)]
        def check_ip(ip_addr):
            ok_tcp, tcp_ms = test_tcp_port(ip_addr, 18899, timeout=0.65)
            if ok_tcp:
                temp_state = dict(engine.state)
                ok_api, api_ms = test_hgm_stage2(f"http://{ip_addr}:18899", temp_state, timeout=3.5)
                if ok_api:
                    return ip_addr, temp_state.get("client_token", ""), tcp_ms, api_ms
            return None
        with ThreadPoolExecutor(max_workers=64) as ex:
            for res in ex.map(check_ip, ips):
                if res:
                    f_ip, f_tok, t_ms, a_ms = res
                    if not any(ip_item == f_ip for ip_item, _, _ in found):
                        found.append((f_ip, t_ms, a_ms))
                        if f_tok and f_tok != engine.state["client_token"]:
                            engine.state["client_token"] = f_tok
                            engine.state["dirty"] = True
    return found

def run_connect_task(engine, raw_url, force_skip=False):
    from core.backup import run_backup_task
    if engine.is_running:
        return
    engine.is_running = True
    engine.set_pill("Підключення...", "work")
    connected_ok = False
    try:
        srv, has_bang = normalize_server_url(raw_url)
        skip_check = force_skip or has_bang
        if not srv:
            engine.log("Введіть IP-адресу або домен сайту перед підключенням!", "warn")
            engine.set_pill("Не вказано адресу", "err")
            return
        parsed = urlparse(srv)
        p_host = parsed.hostname or srv
        c_port = parsed.port or (443 if parsed.scheme == "https" else 18899)
        if skip_check:
            engine.state["server"] = srv
            commit_state(engine.state)
            engine.diag_net = f"{p_host}:{c_port} (БЕЗ ПЕРЕВІРКИ)"
            engine.diag_ping = "Пропущено"
            engine.set_pill("Збережено (!)", "ok")
            engine.log(f"Адресу збережено без перевірки: {srv}", "warn")
            engine.set_progress(100, "Сервер збережено")
            connected_ok = True
        else:
            engine.set_progress(None, f"Перевірка сайту та HGM ({p_host}:{c_port})...")
            ok, code, msg, tcp_ms, api_ms = verify_host_and_hgm(engine, srv)
            if not ok:
                engine.log(msg, "err")
                engine.diag_net = f"{p_host}:{c_port} ({code})"
                engine.diag_ping = "Помилка перевірки"
                engine.set_pill("Не є сервером HGM" if code == "NOT_HGM" else "Сайт недоступний", "err")
                engine.set_progress(0, msg)
                return
            engine.state["server"] = srv
            commit_state(engine.state)
            engine.diag_net = f"{p_host}:{c_port} (ОНЛАЙН)"
            engine.diag_ping = f"TCP {tcp_ms} мс | API {api_ms} мс"
            engine.set_pill(f"ОНЛАЙН | {api_ms} мс", "ok")
            engine.log(f"Підключено до HomeGrid Monitor: {srv} (TCP: {tcp_ms} мс, API: {api_ms} мс)", "ok")
            engine.set_progress(100, "Підключення успішне")
            connected_ok = True
    finally:
        with engine.lock:
            engine.is_running = False
            engine.indeterminate = False
    if connected_ok and not SILENT_MODE:
        if engine.ask_modal("confirm", "Сервер підключено", f"Успішно підключено до {engine.state['server']}. Виконати резервне копіювання зараз?"):
            run_backup_task(engine, engine.state["server"], skip_check)

def run_scan_task(engine):
    from core.backup import run_backup_task
    if engine.is_running:
        return
    engine.is_running = True
    engine.set_pill("Пошук в LAN...", "work")
    found_single = False
    try:
        servers = scan_lan_servers(engine)
        if not servers:
            engine.log("Сервери HomeGrid Monitor у мережі не знайдено.", "err")
            engine.set_pill("Не знайдено", "err")
            engine.set_progress(0, "Сервер не знайдено")
        elif len(servers) == 1:
            (ip, t_ms, a_ms), = servers
            url = f"http://{ip}:18899"
            engine.state["server"] = url
            commit_state(engine.state)
            engine.diag_net = f"{ip}:18899 (ОНЛАЙН)"
            engine.diag_ping = f"TCP {t_ms} мс | API {a_ms} мс"
            engine.set_pill(f"ОНЛАЙН | {a_ms} мс", "ok")
            engine.log(f"Знайдено сервер: {url} (TCP: {t_ms} мс, API: {a_ms} мс)", "ok")
            engine.set_progress(100, "Сервер знайдено та збережено")
            found_single = True
        else:
            engine.log(f"Знайдено кілька серверів ({len(servers)} шт.):", "warn")
            lan_urls = []
            for ip, t_ms, a_ms in reversed(servers):
                u_ip = f"http://{ip}:18899"
                record_server_history(engine.state, u_ip)
            for ip, t_ms, a_ms in servers:
                u_ip = f"http://{ip}:18899"
                lan_urls.append(u_ip)
                engine.log(f"  • {u_ip} (TCP: {t_ms} мс, API: {a_ms} мс)", "info")
            engine.lan_found_urls = set(lan_urls)
            first_ip, _, _ = next(iter(servers))
            engine.state["server"] = f"http://{first_ip}:18899"
            commit_state(engine.state)
            engine.log("Усі знайдені адреси збережено у «🕘 Історія» для швидкого вибору.", "ok")
            engine.set_pill(f"Знайдено: {len(servers)}", "ok")
            engine.set_progress(100, f"Знайдено {len(servers)} серверів — оберіть потрібний у «🕘 Історія»")
    finally:
        with engine.lock:
            engine.is_running = False
            engine.indeterminate = False
    if found_single and not SILENT_MODE:
        if engine.ask_modal("confirm", "Сервер знайдено", f"Знайдено та підключено сервер {engine.state['server']}. Виконати резервне копіювання зараз?"):
            run_backup_task(engine, engine.state["server"], False)
