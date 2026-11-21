import os
import sys
# ==============================================================================
# [ФАЙЛ: core/network.py (v2.01 | 21.11.2026 05:25) — HTTP, PING, TCP, ВЕРИФИКАЦИЯ HGM И СКАНЕР LAN]
# ==============================================================================
import re
import json
import time
import socket
_ORIG_CREATE_CONN = socket.create_connection
def _fast_conn(addr, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, **kw):
    s = _ORIG_CREATE_CONN(addr, timeout=timeout, source_address=source_address, **kw)
    try:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2097152)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2097152)
    except Exception: pass
    return s
socket.create_connection = _fast_conn
import ipaddress
import subprocess
import urllib.request
import urllib.error
import http.cookiejar
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from core.config import DEFAULT_TOK, SILENT_MODE, commit_state

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
                        if "homegrid_dash_session=" in h_val:
                            m = re.search(r"homegrid_dash_session=([^;]+)", h_val)
                            if m and m.group(1).strip():
                                new_ses = m.group(1).strip()
                                _seed_cookie(jar, url, "homegrid_dash_session", new_ses)
                        if "hg_client=" in h_val:
                            m2 = re.search(r"hg_client=([^;]+)", h_val)
                            if m2 and m2.group(1).strip():
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
        if os.name == "nt":
            cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
            res = subprocess.run(
                cmd, stdin=subprocess.DEVNULL, capture_output=True, encoding="cp866", errors="replace", timeout=4, creationflags=0x08000000
            )
        else:
            sec = max(1, int(round(timeout_ms / 1000.0)))
            w_flag = "-t" if sys.platform == "darwin" else "-W"
            cmd = ["ping", "-c", "1", w_flag, str(sec), host]
            res = subprocess.run(
                cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, errors="replace", timeout=4
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

def _linux_proc_net_hints():
    """Шлюзы (из /proc/net/route) и IP соседей (из /proc/net/arp) — только строки IP-адресов."""
    gw_ips, arp_ips = [], []
    if os.name == "nt":
        return gw_ips, arp_ips
    # /proc/net/route: Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT
    try:
        with open("/proc/net/route", "r", encoding="utf-8", errors="ignore") as f:
            next(f, None)
            for ln in f:
                pt = ln.split()
                if len(pt) >= 3 and pt[1] == "00000000" and pt[2] != "00000000":
                    gw = socket.inet_ntoa(int(pt[2], 16).to_bytes(4, "little"))
                    if gw not in gw_ips:
                        gw_ips.append(gw)
    except Exception:
        pass
    # /proc/net/arp: IP address  HW type  Flags  HW address  Mask  Device
    try:
        with open("/proc/net/arp", "r", encoding="utf-8", errors="ignore") as f:
            next(f, None)
            for ln in f:
                pt = ln.split()
                if len(pt) >= 4 and pt[2] != "0x0":
                    arp_ips.append(pt[0])
    except Exception:
        pass
    return gw_ips, arp_ips

def _local_ipv4_with_prefix():
    """Локальные IPv4 с длиной префикса для Linux/macOS."""
    res = []
    if os.name == "nt":
        return res
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show"], stdin=subprocess.DEVNULL, capture_output=True,
                             text=True, errors="replace", timeout=3).stdout or ""
        for line in out.splitlines():
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", line)
            if m:
                res.append((m.group(1), int(m.group(2))))
    except Exception:
        pass
    if not res:
        try:
            out = subprocess.run(["ifconfig"], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                 errors="replace", timeout=3).stdout or ""
            for m in re.finditer(r"inet (?:addr:)?(\d+\.\d+\.\d+\.\d+)\s+(?:netmask|Mask:)\s*(0x[0-9a-fA-F]+|\d+\.\d+\.\d+\.\d+)", out):
                mask = m.group(2)
                if mask.startswith("0x"):
                    mask = str(ipaddress.IPv4Address(int(mask, 16)))
                res.append((m.group(1), ipaddress.IPv4Network("0.0.0.0/" + mask).prefixlen))
        except Exception:
            pass
    gw_ips, arp_ips = _linux_proc_net_hints()
    for ip_h in gw_ips + arp_ips:
        res.append((ip_h, 24))
    return res

def get_main_subnets(state=None):
    networks = set()
    has_wsl_nat = False

    def _add_net(ip_str, plen=24):
        nonlocal has_wsl_nat
        try:
            ip_obj = ipaddress.IPv4Address(ip_str)
            if not ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                return
            if ip_str.startswith("172."):
                has_wsl_nat = True
            if 22 <= plen < 24:
                for sub in ipaddress.IPv4Network(f"{ip_str}/{plen}", strict=False).subnets(new_prefix=24):
                    networks.add(str(sub.network_address).rsplit(".", 1)[0])
            else:
                net = ipaddress.IPv4Network(f"{ip_str}/24", strict=False)
                networks.add(str(net.network_address).rsplit(".", 1)[0])
        except ValueError:
            pass

    for ip_str, plen in _local_ipv4_with_prefix():
        _add_net(ip_str, plen)

    candidate_ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            _, _, _, _, sockaddr = info
            candidate_ips.append(sockaddr[0])
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        candidate_ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    for ip_str in candidate_ips:
        _add_net(ip_str, 24)

    if isinstance(state, dict):
        urls = [state.get("server", "")] + list(state.get("server_history") or [])
        for u in urls:
            try:
                u = (u or "").strip().rstrip("!")
                if not u:
                    continue
                host = urlparse(u if "://" in u else "http://" + u).hostname
                if host:
                    _add_net(host, 24)
            except Exception:
                continue

    primary_prefs = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        p_ip = s.getsockname()[0]
        s.close()
        if not p_ip.startswith("172."):
            primary_prefs.append(p_ip.rsplit(".", 1)[0])
    except Exception:
        pass

    from core.config import IS_WSL
    if IS_WSL:
        try:
            ps_out = subprocess.check_output(
                ["powershell.exe", "-NoProfile", "-Command",
                 "(Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null}).IPv4Address.IPAddress"],
                stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.5
            ).decode("utf-8", errors="ignore")
            for m_ip in re.findall(r"\b(\d+\.\d+\.\d+)\.\d+\b", ps_out):
                if not m_ip.startswith("172."):
                    networks.add(m_ip)
                    if m_ip not in primary_prefs:
                        primary_prefs.append(m_ip)
        except Exception:
            pass
        if not any(n.startswith("192.168.") for n in networks):
            networks.update(("192.168.0", "192.168.1"))

    def _net_rank(pref):
        if pref in primary_prefs:
            return (0, primary_prefs.index(pref), pref)
        if pref.startswith("192.168."):
            return (1, 0, pref)
        if pref.startswith("10."):
            return (2, 0, pref)
        return (3, 0, pref)

    return sorted(networks, key=_net_rank)

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
    subs = get_main_subnets(engine.state)
    if not subs:
        engine.log("Активні мережеві адаптери LAN не знайдено!", "err")
        return []
    engine.log("Сканування підмереж: " + ", ".join(f"{s}.0/24" for s in subs), "info")
    found = []
    with engine.lock:
        base_state = dict(engine.state)
    _, arp_h = _linux_proc_net_hints()
    prio = set(arp_h)
    for u in [base_state.get("server", "")] + list(base_state.get("server_history") or []):
        hp = urlparse((u or "").strip().rstrip("!")).hostname
        if hp:
            prio.add(hp)
    for pref in subs:
        engine.set_progress(None, f"Сканування {pref}.1-254...")
        raw = [f"{pref}.{i}" for i in range(1, 255)]
        ips = [x for x in raw if x in prio] + [x for x in raw if x not in prio]
        try:
            us = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            us.setblocking(False)
            for t in ips:
                try: us.sendto(b"\x00", (t, 9))
                except Exception: pass
            us.close()
            time.sleep(0.12)
        except Exception:
            pass
        def check_ip(ip_addr):
            try:
                ok_tcp, tcp_ms = test_tcp_port(ip_addr, 18899, timeout=0.85)
                if not ok_tcp:
                    time.sleep(0.15)
                    ok_tcp, tcp_ms = test_tcp_port(ip_addr, 18899, timeout=1.85)
                if ok_tcp:
                    temp_state = dict(base_state)
                    temp_state["_jar"] = None
                    ok_api, api_ms = test_hgm_stage2(f"http://{ip_addr}:18899", temp_state, timeout=5.0)
                    if ok_api:
                        return ip_addr, temp_state.get("client_token", ""), tcp_ms, api_ms
            except Exception:
                return None
            return None
        with ThreadPoolExecutor(max_workers=32) as ex:
            for res in ex.map(check_ip, ips):
                if res:
                    f_ip, f_tok, t_ms, a_ms = res
                    if not any(ip_item == f_ip for ip_item, _, _ in found):
                        found.append((f_ip, t_ms, a_ms))
                        f_url = f"http://{f_ip}:18899"
                        engine.discovered_servers = [(f"http://{x}:18899", tm, am) for x, tm, am in found]
                        engine.log(f"Знайдено сервер: {f_url} (TCP: {t_ms} мс, API: {a_ms} мс)", "ok")
                        engine.set_pill(f"Знайдено: {len(found)}", "work")
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
    found_list = []
    try:
        servers = scan_lan_servers(engine)
        if not servers:
            engine.log("Сервери HomeGrid Monitor у мережі не знайдено.", "err")
            engine.set_pill("Не знайдено", "err")
            engine.set_progress(0, "Сервер не знайдено")
        else:
            found_list = [(f"http://{ip}:18899", t_ms, a_ms) for ip, t_ms, a_ms in servers]
            engine.discovered_servers = found_list
            first_ip, first_t, first_a = servers[0]
            first_url = f"http://{first_ip}:18899"
            engine.state["server"] = first_url
            engine.diag_net = f"{first_ip}:18899 (ОНЛАЙН)"
            engine.diag_ping = f"TCP {first_t} мс | API {first_a} мс"
            if len(servers) == 1:
                engine.set_pill(f"ОНЛАЙН | {first_a} мс", "ok")
                engine.set_progress(100, f"Знайдено сервер: {first_url}")
            else:
                engine.log(f"Сканування завершено. Всього знайдено серверів: {len(servers)} шт.", "info")
                engine.set_pill(f"Знайдено: {len(servers)}", "ok")
                engine.set_progress(100, f"Знайдено {len(servers)} серверів у мережі")
    finally:
        with engine.lock:
            engine.is_running = False
            engine.indeterminate = False

    if found_list and not SILENT_MODE:
        choice = engine.ask_modal("lan_found", "Виявлені сервери в мережі", "", default_val=found_list)
        if isinstance(choice, dict):
            sel_url = choice.get("url", "")
            act = choice.get("action", "")
            if sel_url:
                engine.state["server"] = sel_url
                if act in ("save", "backup"):
                    commit_state(engine.state)
                    engine.log(f"Сервер {sel_url} збережено у «Історія».", "ok")
                if act == "backup":
                    run_backup_task(engine, sel_url, False)