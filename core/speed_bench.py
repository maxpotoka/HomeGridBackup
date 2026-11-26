# patch-id: owner-prefix-anon-3.56
# patch-id: auto-owner-canon-srv-3.50
# patch-id: d1-always-send-3.48
# patch-id: client-os-binding-3.58
import hashlib, json, os, platform, struct, tempfile, threading, time, urllib.request, zlib
import tkinter as tk
from core.config import SCRIPT_VER, SECURE_DIR

_LAST_D1_ERR = ''
# patch-id: live-d1-sync-3.47
D1_API_BASE = 'https://workers.dev'
_SYNCED_IDS_FILE = os.path.join(SECURE_DIR, 'd1_synced_ids.json')
_CACHE_FILE = os.path.join(SECURE_DIR, 'd1_speed_cache.json')
_LOCAL_BENCH_FILE = os.path.join(SECURE_DIR, 'local_bench_history.jsonl')

def _hw_tag():
    c = (platform.processor() or platform.machine() or '').replace('(R)', '').replace('(TM)', '').replace('CPU ', '').strip()
    return c[:44]

def _os_tag():
    s = platform.system()
    r = str(platform.release() or '').partition('-')[0].strip()
    if s == 'Darwin':
        mv = platform.mac_ver()[0] if platform.mac_ver() else r
        return f"macOS {mv[0].partition('.')[0][0]}" if mv else 'macOS'
    b_str = f'{struct.calcsize("P")*8}-bit'
    if s == 'Linux':
        dist = ''
        try:
            if os.path.exists('/etc/os-release'):
                for ln in open('/etc/os-release', encoding='utf-8', errors='ignore'):
                    if ln.startswith('PRETTY_NAME='):
                        dist = ln.split('=', 1)[1].strip().strip('"'); break
        except Exception: pass
        if dist: return f"{dist} ({b_str})"
        if '.' in r:
            p = r.split('.')
            return f"Linux {p[0]}.{p[1]} ({b_str})"
    return f"{s} {r} ({b_str})".strip()

def _owner_prefix(st):
    d = st or {}
    pin = str(d.get('login_pin') or '').strip()
    if pin:
        return hashlib.sha256(f'hgm-pin:{pin}'.encode('utf-8')).hexdigest()[:16]
    tok = str(d.get('client_token') or '').strip()
    if tok and tok != 'default':
        return hashlib.sha256(f'hgm-tok:{tok}'.encode('utf-8')).hexdigest()[:16]
    return ''

def _anon_id(st):
    d = st or {}
    raw = str(d.get('device_id') or '').strip() or f"{platform.node()}:{platform.machine()}:{platform.system()}"
    dev = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:15]
    own = _owner_prefix(d)
    return f"{own}:{dev}" if own else hashlib.sha256(raw.encode('utf-8')).hexdigest()[:32]

def _owner_id(st):
    d = st or {}
    pin = str(d.get('login_pin') or '').strip()
    if pin:
        return hashlib.sha256(f'hgm-pin:{pin}'.encode('utf-8')).hexdigest()[:32]
    tok = str(d.get('client_token') or '').strip()
    if tok and tok != 'default':
        return hashlib.sha256(f'hgm-owner:{tok}'.encode('utf-8')).hexdigest()[:32]
    return _anon_id(d)

def _cf_http(path, method='GET', payload=None, timeout=8.0):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    hdrs = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    if body is not None:
        hdrs['Content-Type'] = 'application/json'
    req = urllib.request.Request(f"{D1_API_BASE}{path}", data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        txt = resp.read().decode('utf-8', errors='replace').strip()
        return resp.status, (json.loads(txt) if txt.startswith('{') else None)

def run_local_benchmark(target_dir=''):
    blk = os.urandom(1048576)
    tot = 32 * 1048576
    t0 = time.perf_counter()
    crc = 0
    t_s = time.perf_counter(); h = hashlib.sha256()
    for _ in range(32):
        crc = zlib.crc32(blk, crc)
        h.update(blk)
    sha_mbs = round((tot / 1048576.0) / max(0.001, time.perf_counter() - t_s), 1); cpu_mbs = round((tot / 1048576.0) / max(0.001, time.perf_counter() - t0), 1)
    bdir = target_dir if (target_dir and os.path.isdir(target_dir)) else tempfile.gettempdir()
    tmp_p = os.path.join(bdir, f".hgb_bench_{os.getpid()}.tmp")
    w_mbs, r_mbs = 0.0, 0.0
    try:
        t1 = time.perf_counter()
        with open(tmp_p, 'wb', buffering=1048576) as wf:
            for _ in range(32):
                wf.write(blk)
            wf.flush()
            os.fsync(wf.fileno())
        w_mbs = round((tot / 1048576.0) / max(0.001, time.perf_counter() - t1), 1)
        t2 = time.perf_counter()
        with open(tmp_p, 'rb', buffering=1048576) as rf:
            while rf.read(1048576):
                pass
        r_mbs = round((tot / 1048576.0) / max(0.001, time.perf_counter() - t2), 1)
    finally:
        if os.path.exists(tmp_p):
            try:
                os.remove(tmp_p)
            except OSError:
                pass
    res = {'cpu_mbs': cpu_mbs, 'sha_mbs': sha_mbs, 'disk_w_mbs': w_mbs, 'disk_r_mbs': r_mbs, 'ts': time.time(), 'pc': f"{platform.node()} [{_os_tag()}] ({_hw_tag()})"[:64], 'os_label': _os_tag()}
    try:
        os.makedirs(SECURE_DIR, exist_ok=True)
        with open(_LOCAL_BENCH_FILE, 'a', encoding='utf-8') as af:
            af.write(json.dumps(res, ensure_ascii=False) + '\n')
    except Exception:
        pass
    return res

def load_local_benchmarks():
    out = []
    if os.path.isfile(_LOCAL_BENCH_FILE):
        try:
            with open(_LOCAL_BENCH_FILE, 'r', encoding='utf-8') as f:
                for ln in f:
                    ln = ln.strip()
                    if ln.startswith('{'):
                        out.append(json.loads(ln))
        except Exception:
            pass
    return out[-100:]

def _unused_ret():
    return {'cpu_mbs': cpu_mbs, 'sha_mbs': sha_mbs, 'disk_w_mbs': w_mbs, 'disk_r_mbs': r_mbs}

def push_backup_speed(state, os_label, adapter, scope, size_mb, dur_sec, spd_mbs, app_ver=SCRIPT_VER, srv_mbs=0.0, link_mbps=0, srv_host='', buf_kb=64):
    p = {'anon_id': _anon_id(state), 'owner_id': _owner_id(state), 'os_label': str(os_label or _os_tag()).strip()[:64], 'hw_tag': _hw_tag(), 'adapter': str(adapter or 'Backup').strip()[:48], 'kind': 'backup', 'srv_host': str(srv_host or '').strip()[:64], 'buf_kb': int(buf_kb or 64), 'link_mbps': int(link_mbps or 0), 'size_mb': round(float(size_mb or 0), 2), 'scope': 'Internet' if str(scope).lower() == 'internet' else 'LAN', 'spd_mbs': round(float(spd_mbs or 0), 2), 'srv_mbs': round(float(srv_mbs or 0), 2), 'cpu_mbs': 0.0, 'disk_w_mbs': 0.0, 'disk_r_mbs': 0.0, 'app_ver': str(app_ver)[:16]}
    try:
        code, data = _cf_http('/submit', method='POST', payload=p)
        return bool(200 <= code < 300 and isinstance(data, dict) and data.get('ok'))
    except Exception:
        return False

def fetch_global_stats(scope='ALL'):
    global _LAST_D1_ERR
    _LAST_D1_ERR = ''
    sc = scope if scope in ('LAN', 'Internet') else 'ALL'
    try:
        code, raw = _cf_http(f"/stats?scope={sc}", method='GET')
        if 200 <= code < 300 and isinstance(raw, dict):
            items = raw.get('samples') or raw.get('summary') or raw.get('rows') or []
            if isinstance(items, list) and items:
                items = [_norm_d1_row(x) for x in items if isinstance(x, dict)]
                os.makedirs(SECURE_DIR, exist_ok=True)
                try:
                    with open(_CACHE_FILE, 'w', encoding='utf-8') as wf:
                        json.dump(items, wf, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                return items
    except Exception as _e:
        _LAST_D1_ERR = str(_e)[:80]
    if os.path.isfile(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
                raw_c = json.load(f) or []
                return [_norm_d1_row(x) for x in raw_c if isinstance(x, dict)]
        except Exception:
            pass
    return []

def _norm_d1_row(r):
    d = dict(r)
    ad = str(d.get('adapter') or '').strip()
    if not d.get('kind'):
        d['kind'] = 'bench' if ad.lower() == 'bench' else 'backup'
    if not d.get('spd_mbs') and d.get('avg_spd') is not None:
        d['spd_mbs'] = float(d.get('avg_spd') or 0)
    if not d.get('srv_mbs') and d.get('avg_srv') is not None:
        d['srv_mbs'] = float(d.get('avg_srv') or 0)
    if not d.get('cpu_mbs') and d.get('avg_cpu') is not None:
        d['cpu_mbs'] = float(d.get('avg_cpu') or 0)
    if not d.get('disk_w_mbs') and d.get('avg_disk_w') is not None:
        d['disk_w_mbs'] = float(d.get('avg_disk_w') or 0)
    if not d.get('disk_r_mbs') and d.get('avg_disk_r') is not None:
        d['disk_r_mbs'] = float(d.get('avg_disk_r') or 0)
    return d

_D1_SYNC_LOCK = threading.Lock()
def sync_local_history_to_d1(state, ops=None):
    def _job():
        if not _D1_SYNC_LOCK.acquire(blocking=False):
            return
        try:
            os.makedirs(SECURE_DIR, exist_ok=True)
            seen = set()
            if os.path.isfile(_SYNCED_IDS_FILE):
                try:
                    seen = set(json.load(open(_SYNCED_IDS_FILE, encoding='utf-8')) or [])
                except Exception:
                    seen = set()
            aid = _anon_id(state)
            changed = False
            for b in load_local_benchmarks()[-15:]:
                bid = f"b_{round(float(b.get('ts') or 0), 2)}"
                if bid in seen or float(b.get('disk_w_mbs') or 0) <= 0:
                    continue
                pl = {'anon_id': aid, 'owner_id': _owner_id(state), 'os_label': str(b.get('os_label') or _os_tag())[:64],
                      'hw_tag': _hw_tag(), 'kind': 'bench', 'adapter': 'Bench',
                      'sha_mbs': float(b.get('sha_mbs') or 0), 'scope': 'LAN',
                      'spd_mbs': float(b.get('disk_w_mbs') or 0),
                      'cpu_mbs': float(b.get('cpu_mbs') or 0),
                      'disk_w_mbs': float(b.get('disk_w_mbs') or 0),
                      'disk_r_mbs': float(b.get('disk_r_mbs') or 0), 'app_ver': SCRIPT_VER}
                try:
                    c, d = _cf_http('/submit', method='POST', payload=pl)
                    if 200 <= c < 300 and isinstance(d, dict) and d.get('ok'):
                        seen.add(bid); changed = True
                except Exception:
                    break
            for o in (ops or [])[:25]:
                oid = str(o.get('operation_id') or o.get('timestamp') or '')
                sp = float(o.get('spd_f') or o.get('download_speed_mbps') or 0)
                if not oid or f"o_{oid}" in seen or sp <= 0 or o.get('spd_approx'):
                    continue
                os_v = (str(o.get('platform') or '') + ' ' + str(o.get('platform_version') or '').partition('-')[0]).strip() or _os_tag()
                ad_v = o.get('net_adapter_label') or o.get('net_adapter_type') or 'Backup'
                ok = push_backup_speed(
                    state, os_v, ad_v, o.get('scope_norm') or o.get('net_scope') or 'LAN',
                    o.get('mb_f') or o.get('size_mb') or 0, o.get('dur_f') or o.get('duration_sec') or 0,
                    sp, str(o.get('app_version') or SCRIPT_VER),
                    float(o.get('srv_speed_mbps') or 0), int(o.get('net_link_mbps') or 0),
                    str(o.get('srv_host') or o.get('srv_norm') or ''), int(o.get('buf_kb') or 64))
                if ok:
                    seen.add(f"o_{oid}"); changed = True
            if changed:
                with open(_SYNCED_IDS_FILE, 'w', encoding='utf-8') as wf:
                    json.dump(sorted(seen)[-300:], wf)
        finally:
            _D1_SYNC_LOCK.release()
    threading.Thread(target=_job, daemon=True).start()

def open_compact_bench_popup(parent, state, palette, fs, fam, get_dir_cb, on_done=None):
    lang = (state or {}).get('lang', 'en')
    win = tk.Toplevel(parent)
    win.title('Тест ПК і диска' if lang == 'uk' else 'PC & Disk Benchmark')
    win.configure(bg=palette['panel'])
    win.geometry('430x220')
    win.transient(parent)
    win.grab_set()
    lbl = tk.Label(win, text='⏳ Тестування CPU та диска (32 МБ)...' if lang == 'uk' else '⏳ Testing CPU & disk (32 MB)...', bg=palette['panel'], fg=palette['cyan'], font=(fam, fs, 'bold'), wraplength=390)
    lbl.pack(pady=(24, 12), padx=16)
    res_lbl = tk.Label(win, text='', bg=palette['panel'], fg=palette['text'], font=(fam, fs))
    res_lbl.pack(pady=6, padx=16)
    btn_ok = tk.Button(win, text='OK', state='disabled', command=lambda: (win.destroy(), on_done() if callable(on_done) else None), bg=palette['green'], fg=palette['green_txt'], font=(fam, fs, 'bold'), padx=18, pady=4)
    btn_ok.pack(side='bottom', pady=14)
    def _work():
        r = run_local_benchmark(get_dir_cb() if callable(get_dir_cb) else '')
        p = {'anon_id': _anon_id(state), 'owner_id': _owner_id(state), 'os_label': _os_tag(), 'hw_tag': _hw_tag(), 'kind': 'bench', 'adapter': 'Bench', 'sha_mbs': r.get('sha_mbs', 0.0), 'scope': 'LAN', 'spd_mbs': r['disk_w_mbs'], 'cpu_mbs': r['cpu_mbs'], 'disk_w_mbs': r['disk_w_mbs'], 'disk_r_mbs': r['disk_r_mbs'], 'app_ver': SCRIPT_VER}
        sent = False
        if True:
            try:
                c, d = _cf_http('/submit', method='POST', payload=p)
                sent = bool(200 <= c < 300 and isinstance(d, dict) and d.get('ok'))
            except Exception:
                pass
        def _fin():
            if not win.winfo_exists():
                return
            sfx = (' • D1 ✔' if sent else ' • D1 opt-in вимк.' if lang == 'uk' else ' • D1 opt-in off')
            lbl.configure(text=('✔ Тест завершено!' if lang == 'uk' else '✔ Benchmark complete!') + sfx, fg=palette['green'])
            res_lbl.configure(text=f"CPU: {r['cpu_mbs']} MB/s  |  Write: {r['disk_w_mbs']} MB/s  |  Read: {r['disk_r_mbs']} MB/s")
            btn_ok.configure(state='normal')
        win.after(0, _fin)
    threading.Thread(target=_work, daemon=True).start()


def open_buffer_ab_popup(parent, state, palette, fs, fam):
    lang = (state or {}).get('lang', 'en')
    srv = str((state or {}).get('server') or '').strip().rstrip('/')
    win = tk.Toplevel(parent)
    win.title('Тест буфера 16 vs 256 КБ' if lang == 'uk' else 'Buffer 16 vs 256 KB Test')
    win.configure(bg=palette['panel'])
    win.geometry('490x230')
    win.transient(parent)
    win.grab_set()
    lbl = tk.Label(win, text='⏳ Порівняння буферів 16 КБ та 256 КБ (проксі вимкнено)...' if lang == 'uk' else '⏳ Comparing 16 KB vs 256 KB buffers (proxy disabled)...', bg=palette['panel'], fg=palette['cyan'], font=(fam, fs, 'bold'), wraplength=450)
    lbl.pack(pady=(22, 12), padx=16)
    res_lbl = tk.Label(win, text='', bg=palette['panel'], fg=palette['text'], font=(fam, fs))
    res_lbl.pack(pady=6, padx=16)
    btn_ok = tk.Button(win, text='OK', state='disabled', command=win.destroy, bg=palette['green'], fg=palette['green_txt'], font=(fam, fs, 'bold'), padx=18, pady=4)
    btn_ok.pack(side='bottom', pady=14)
    def _run_ab():
        if not srv:
            win.after(0, lambda: (lbl.configure(text='Server URL is empty', fg=palette['red']), btn_ok.configure(state='normal')))
            return
        try:
            import http.cookiejar as _cj
            from core.config import DEFAULT_TOK
            from core.network import invoke_http, _seed_cookie, BROWSER_UA
            pin = (state or {}).get('login_pin') or ''
            if pin:
                _, _, _, ses_new, _, _ = invoke_http(f"{srv}/api/auth/login", state, 'POST', json.dumps({'pin': pin}), srv, f"{srv}/login", 8.0, send_ses=False)
                if ses_new and isinstance(state, dict):
                    state['session_token'] = ses_new
            jar = (state or {}).get('_jar') if isinstance(state, dict) and state.get('_jar') else _cj.CookieJar()
            tok = (state or {}).get('client_token') or DEFAULT_TOK
            ses = (state or {}).get('session_token') or ''
            _seed_cookie(jar, srv, 'hg_client', tok)
            if ses:
                _seed_cookie(jar, srv, 'homegrid_dash_session', ses)
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), urllib.request.ProxyHandler({}))
            hdrs = {'User-Agent': BROWSER_UA, 'Referer': f"{srv}/", 'Origin': srv, 'Accept-Encoding': 'identity'}
            out = {}
            for kb in (16, 256):
                chunk = kb * 1024
                tot, net_dt = 0, 0.0
                t_start = time.perf_counter()
                while time.perf_counter() - t_start < 3.5:
                    req = urllib.request.Request(f"{srv}/api/auth/status?_t={int(time.time()*1000)}", headers=hdrs)
                    with opener.open(req, timeout=8) as r:
                        while True:
                            rt0 = time.perf_counter()
                            b = r.read(chunk)
                            net_dt += time.perf_counter() - rt0
                            if not b:
                                break
                            tot += len(b)
                out[kb] = round((tot / 1048576.0) / max(0.001, net_dt), 2)
            v16, v256 = out.get(16, 0), out.get(256, 0)
            msg = f"16 KB: {v16} MB/s   |   256 KB: {v256} MB/s   ({_os_tag()})"
            win.after(0, lambda m=msg: (lbl.configure(text='✔ A/B тест завершено (no-proxy)' if lang == 'uk' else '✔ A/B test complete (no-proxy)', fg=palette['green']), res_lbl.configure(text=m), btn_ok.configure(state='normal')))
        except Exception as exc:
            err_s = str(exc)[:90]
            win.after(0, lambda e=err_s: (lbl.configure(text=e, fg=palette['red']), btn_ok.configure(state='normal')))
    threading.Thread(target=_run_ab, daemon=True).start()
