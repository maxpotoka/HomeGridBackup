# patch-id: auto-gui-mode-with-display-4.11
# patch-id: smart-bottleneck-4.06
# patch-id: chart-journal-only-4.05
# patch-id: json-inv-id-and-raw-regex-4.04.1
# patch-id: hide-inv-img-in-lite-and-en-hw-4.04b
# patch-id: server-hw-status-ui-4.03b
# patch-id: remove-server-version-probe-4.02
# patch-id: extract-hgm-web-version-4.01
# patch-id: health-endpoint-and-srv-version-4.00
# patch-id: actionable-errors-and-terms-3.99c
# patch-id: backup-logs-uk-consistency-3.98
# patch-id: about-repo-url-3.97
# patch-id: no-pip-auto-install-and-uk-tray-hints-3.96
# patch-id: confirm-modal-inverter-image-sync-3.95
# patch-id: confirm-modal-inverter-image-left-3.94
# patch-id: server-inverter-image-fix-display-3.93
# patch-id: server-inverter-image-auth-3.92
# patch-id: server-inverter-image-preview-3.91
# patch-id: larger-lan-and-confirm-dialogs-3.90
# patch-id: tar-zst-verify-and-i18n-3.89
# patch-id: tar-zst-log-label-3.88
# patch-id: keep-part-on-stream-eof-3.87
# patch-id: http-range-resume-polish-3.86
# patch-id: http-range-resume-download-3.85
# patch-id: independent-1-100-per-stage-3.84
# patch-id: pingpong-and-3stage-1-100-3.83
# patch-id: backup-report-3stage-hbar-3.82
# patch-id: stats-3d-bars-3.81
# patch-id: stats-compact-x-labels-3.80
# patch-id: stats-dynamic-cols-3.79
# patch-id: stats-sort-desc-3.78
# patch-id: fix-first-run-load-state-3.77
# patch-id: direct-cloud-write-setting-3.76
# patch-id: strict-ssl-verify-3.75
# patch-id: py38-win32-no-removesuffix-3.74
# patch-id: main-nuitka-global-ssl-3.73
# patch-id: macos-nuitka-ssl-d1-3.72
# patch-id: cloud-union-d1-keys-3.71
# patch-id: stats-view-exact-filters-3.70
# patch-id: d1-mine-backup-safe-3.68
# patch-id: d1-mine-backup-merge-3.67
# patch-id: d1-post-200-none-fix-3.66
# patch-id: d1-submit-debug-ascii-3.64
# patch-id: d1-upload-refresh-true-3.63
# patch-id: d1-sync-keys-fix-3.61
# patch-id: d1-log-events-3.60
# patch-id: d1-cache-default-state-3.59
# patch-id: d1-cache-toggle-setting-3.58
# patch-id: owner-prefix-anon-3.56
# patch-id: stats-full-parent-width-3.55
# patch-id: canon-srv-lan-wan-label-3.51
# patch-id: auto-owner-canon-srv-3.50
# patch-id: d1-always-send-3.48
# patch-id: disk-gauge-3seg-3.46
_AK='config.json'
_AJ='.backup_hgm'
_AI='HomeGridMonitorBackup'
_AH='WSL_DISTRO_NAME'
_AG='sched_wake'
_AF='sched_missed'
_AE='silent_cleanup'
_AD='silent_sec_digits'
_AC='tray_enabled'
_AB='yearly_count'
_AA='monthly_count'
_A9='weekly_count'
_A8='today_max'
_A7='daily_days'
_A6='keep_last_count'
_A5='cloud_fit_free_space'
_A4='cloud_max_archives'
_A3='cloud_save_logs'
_A2='cloud_save_archives'
_A1='HomeGridBackup'
_A0='editor_pin'
_z='login_pin'
_y='session_token'
_x='client_token'
_w='--hidden'
_v='darwin'
_u='linux'
_t='sched_time'
_s='lite_mode'
_r='value'
_q='BackupHGM'
_p='nt'
_o='storage_backend'
_n='sched_prio'
_m='sched_mode'
_l='progress_style'
_k='hw_checked'
_j='tray_backend'
_i='minimize_to_tray'
_h='ui_scale'
_g='lang'
_f='delete_mode'
_e='cloud_path'
_d='cloud_remote'
_c='cloud_enabled'
_b='journal_sync_target'
_a='net_fit_free_space'
_Z='net_max_size_gb'
_Y='net_max_archives'
_X='net_enabled'
_W='mirror_enabled'
_V='local_enabled'
_U='op_history'
_T='favorite_servers'
_S=None
_R='theme'
_Q='device_id'
_P='cloud_max_size_gb'
_O='net_dir'
_N='mirror_dir'
_M='all_time_mb'
_L='all_time_cnt'
_K='logs_dir'
_J='auto'
_I='dirty'
_H='ui_font'
_G='download_buf_kb'
_F='server_history'
_E='server'
_D='backup_dir'
_C='utf-8'
_B=False
_A=True
import atexit,json,os,platform,re,sys,tempfile,threading,time,uuid
def is_wsl():
	if not sys.platform.startswith(_u):return _B
	if os.environ.get(_AH)or os.environ.get('WSL_INTEROP')or os.path.exists('/proc/sys/fs/binfmt_misc/WSLInterop'):return _A
	try:
		with open('/proc/version','r',encoding=_C)as A:return'microsoft'in A.read().lower()
	except Exception:return _B
IS_WINDOWS=os.name==_p
IS_MAC=sys.platform==_v
IS_WSL=is_wsl()
WSL_DISTRO=os.environ.get(_AH,'')
WIN_VER=(sys.getwindowsversion().major,sys.getwindowsversion().minor)if IS_WINDOWS else(0,0)
if IS_WSL:
	try:
		import subprocess as _sp_mod,time as _t_mod
		if _t_mod.tzname==('UTC','UTC')and not os.environ.get('TZ'):
			_ps_tz=_sp_mod.check_output(['powershell.exe','-NoProfile','-Command','[TimeZoneInfo]::Local.BaseUtcOffset.TotalMinutes'],stderr=_sp_mod.DEVNULL,timeout=1.5).decode(_C,errors='ignore').strip()
			if _ps_tz and _ps_tz.lstrip('-').isdigit():
				_mins=int(_ps_tz);_sign='-'if _mins>=0 else'+';_hh,_mm=divmod(abs(_mins),60);os.environ['TZ']=f"UTC{_sign}{_hh:02d}:{_mm:02d}"
				if hasattr(_t_mod,'tzset'):_t_mod.tzset()
	except Exception:0
try:
	if IS_MAC and not os.environ.get('HGB_MAC_KEYCHAIN'):raise RuntimeError('macOS unsigned binary uses .env 0600')
	import keyring;KEYRING_SERVICE=_AI;keyring.get_keyring();HAS_KEYRING=_A
except Exception:keyring=_S;KEYRING_SERVICE=_AI;HAS_KEYRING=_B
SCRIPT_VER='4.11.2'
BUILD_DATE='28.11.2026 08:30'
DEFAULT_TOK='pK5hquN9wdrSgIr55FR0WyL16qnpC_cEf1Y6jUjyd14'
IS_ANDROID='ANDROID_ARGUMENT'in os.environ or'ANDROID_ROOT'in os.environ or os.path.exists('/system/build.prop')
if IS_ANDROID:_and_dl='/storage/emulated/0/Download';_and_base=_and_dl if os.path.isdir(_and_dl)else os.path.expanduser('~');DEFAULT_BACKUP_DIR=os.path.join(_and_base,_q);SECURE_DIR=os.path.join(os.path.expanduser('~'),_AJ)
else:DEFAULT_BACKUP_DIR=os.path.join(os.path.expanduser('~'),_q);SECURE_DIR=os.path.join(os.path.expanduser('~'),_AJ)
CFG_FILE=os.path.join(SECURE_DIR,_AK)
ENV_FILE=os.path.join(SECURE_DIR,'.env')
ARGS_LOW=[A.lower()for A in sys.argv[1:]]
GUI_MODE=any(A in('--gui','/gui')for A in ARGS_LOW)
HIDDEN_MODE=any(A in(_w,'--background','/hidden','/h')for A in ARGS_LOW)
SILENT_MODE=HIDDEN_MODE or any(A in('--silent','-s','/silent','/s')for A in ARGS_LOW)
CLI_MODE=any(A in('--cli','--console','-c','/console')for A in ARGS_LOW)
IS_LINUX_NATIVE=sys.platform.startswith(_u)and not IS_WSL and not IS_ANDROID
HAS_DISPLAY=IS_WINDOWS or IS_MAC or IS_ANDROID or bool(os.environ.get('DISPLAY')or os.environ.get('WAYLAND_DISPLAY'))
GUI_EXPLICIT=GUI_MODE
if HAS_DISPLAY and not(SILENT_MODE or CLI_MODE or HIDDEN_MODE):GUI_MODE=_A
AUTO_CLI_FALLBACK=_B
if not HAS_DISPLAY and not HIDDEN_MODE:
	if GUI_MODE or not(SILENT_MODE or CLI_MODE):AUTO_CLI_FALLBACK=_A
	GUI_MODE=_B;CLI_MODE=_A
NO_CLEAN=any(A in('--no-clean','/noclean')for A in ARGS_LOW)
NO_TRAY=any(A in('--no-tray','/notray')for A in ARGS_LOW)
SECRET_KEYS=_x,_y,_z,_A0,'server_pins_json'
SCHED_TASK_NAME=_A1
VALID_PBAR_STYLES='v8',
VALID_THEMES='dark','light'
VALID_SCALES=_J,'800x600','1024x600','1024x768','1280x720','1366x768','1600x900','1920x1080','2560x1440'
VALID_TRAY_BACKENDS=_J,'appindicator','sni-bridge','gtk','xorg','none','pystray'
def _get_ram_summary():
	L='/proc/meminfo'
	try:
		if os.name==_p:
			import ctypes as A
			class E(A.Structure):_fields_=[('dwLength',A.c_ulong),('dwMemoryLoad',A.c_ulong),('ullTotalPhys',A.c_ulonglong),('ullAvailPhys',A.c_ulonglong),('ullTotalPageFile',A.c_ulonglong),('ullAvailPageFile',A.c_ulonglong),('ullTotalVirtual',A.c_ulonglong),('ullAvailVirtual',A.c_ulonglong),('ullAvailExtendedVirtual',A.c_ulonglong)]
			B=E();B.dwLength=A.sizeof(E)
			if A.windll.kernel32.GlobalMemoryStatusEx(A.byref(B)):return f" | RAM: {round(B.ullAvailPhys/1073741824.,1)}/{round(B.ullTotalPhys/1073741824.,1)} GB free"
		elif sys.platform==_v:
			import subprocess as F;M=int(F.check_output(['sysctl','-n','hw.memsize'],timeout=.4).decode().strip());G=F.check_output(['vm_stat'],timeout=.4).decode(_C,errors='ignore');H=re.search('page size of (\\d+) bytes',G);N=int(H.group(1))if H else 4096;I=0
			for O in('Pages free','Pages inactive','Pages speculative'):
				J=re.search(rf"{O}:\s+(\d+)",G)
				if J:I+=int(J.group(1))
			return f" | RAM: {round(I*N/1073741824.,1)}/{round(M/1073741824.,1)} GB free"
		elif os.path.exists(L):
			D,K=0,0
			with open(L,'r',encoding=_C)as P:
				for C in P:
					if C.startswith('MemTotal:'):D=int(C.split()[1])
					elif C.startswith('MemAvailable:'):K=int(C.split()[1])
			if D>0:return f" | RAM: {round(K/1048576.,1)}/{round(D/1048576.,1)} GB free"
	except Exception:0
	return''
_SYSINFO_CACHE={_r:'','time':.0}
def get_fast_sysinfo():
	W='/proc/cpuinfo';V='/etc/os-release';U='Windows 10';K='getprop';L=time.monotonic()
	if _SYSINFO_CACHE[_r]and L-_SYSINFO_CACHE['time']<3e1:return _SYSINFO_CACHE[_r]
	import struct as M;X='64-bit'if os.environ.get('PROCESSOR_ARCHITEW6432')or'64'in platform.machine()or M.calcsize('P')==8 else'32-bit';Y=f"{M.calcsize('P')*8}-bit";A='';B=f"{platform.system()} {platform.release()}"
	if os.name==_p:
		try:
			import winreg as C
			with C.OpenKey(C.HKEY_LOCAL_MACHINE,'HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0')as E:A=str(C.QueryValueEx(E,'ProcessorNameString')[0]).strip()
			with C.OpenKey(C.HKEY_LOCAL_MACHINE,'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')as E:
				G=str(C.QueryValueEx(E,'ProductName')[0]).strip();H=str(C.QueryValueEx(E,'CurrentBuild')[0]).strip();I=''
				for Z in('DisplayVersion','ReleaseId','CSDVersion'):
					try:
						N=str(C.QueryValueEx(E,Z)[0]).strip()
						if N:I=N;break
					except Exception:0
				if H.isdigit()and int(H)>=22000 and U in G:G=G.replace(U,'Windows 11')
				a=f" {I}"if I else'';B=f"{G}{a} (Build {H})"
		except Exception:0
	elif IS_ANDROID:
		try:
			import subprocess as F;b=F.check_output([K,'ro.build.version.release'],timeout=.4).decode().strip();c=F.check_output([K,'ro.build.version.sdk'],timeout=.4).decode().strip();O=F.check_output([K,'ro.product.model'],timeout=.4).decode().strip();B=f"Android {b} (API {c})"
			if O:A=f"{O} ({platform.machine()})"
		except Exception:B='Android OS'
	elif sys.platform==_v:
		J=platform.mac_ver()[0]if platform.mac_ver()else'';P={'15':'Sequoia','14':'Sonoma','13':'Ventura','12':'Monterey','11':'Big Sur'};Q=J.split('.')[0]if J else'';d=f" ({P[Q]})"if Q in P else'';B=f"macOS {J}{d}"
		try:
			import subprocess as F;R=F.check_output(['sysctl','-n','machdep.cpu.brand_string'],timeout=.4).decode().strip()
			if R:A=R
		except Exception:0
	elif sys.platform.startswith(_u):
		try:
			if os.path.exists(V):
				with open(V,'r',encoding=_C)as e:
					for D in e:
						if D.startswith('PRETTY_NAME='):B=D.split('=',1)[1].strip().strip('"');break
			if os.path.exists(W):
				with open(W,'r',encoding=_C)as f:
					for D in f:
						if D.lower().startswith('model name')and':'in D:A=D.split(':',1)[1].strip();break
			g=(os.environ.get('XDG_CURRENT_DESKTOP')or os.environ.get('DESKTOP_SESSION')or'').strip();h=(os.environ.get('XDG_SESSION_TYPE')or('x11'if os.environ.get('DISPLAY')else'')).strip().upper();S=[A for A in(g,h,f"Linux {platform.release().split('-')[0]}")if A]
			if S:B=f"{B} ({', '.join(S)})"
		except Exception:0
	if not A:A=(platform.processor()or os.environ.get('PROCESSOR_IDENTIFIER')or platform.machine()or'Unknown CPU').strip()
	A=re.sub('\\s+',' ',A).replace('(R)','').replace('(TM)','').replace('CPU ','').strip()
	if len(A)>42:A=A[:39]+'...'
	T=f"{B} [{X}, app {Y}] | CPU: {A}{_get_ram_summary()}";_SYSINFO_CACHE[_r]=T;_SYSINFO_CACHE['time']=L;return T
def _ensure_secure_dir():os.makedirs(SECURE_DIR,exist_ok=_A)
def _read_env_secrets():
	B={}
	if os.path.exists(ENV_FILE):
		try:
			with open(ENV_FILE,'r',encoding=_C)as D:
				for A in D:
					A=A.strip()
					if not A or A.startswith('#')or'='not in A:continue
					E,F=A.split('=',1);C=E.strip().lower()
					if C in SECRET_KEYS:B[C]=F.strip().strip('"').strip("'")
		except Exception:0
	return B
def _write_env_secrets(state):
	A=state;_ensure_secure_dir();B=ENV_FILE+'.tmp';C=['# HomeGrid Backup — захищені токени та PIN-коди',f"CLIENT_TOKEN={A.get(_x,'')}",f"SESSION_TOKEN={A.get(_y,'')}",f"LOGIN_PIN={A.get(_z,'')}",f"EDITOR_PIN={A.get(_A0,'')}",f"SERVER_PINS_JSON={A.get('server_pins_json','')}"]
	with open(B,'w',encoding=_C)as D:D.write('\n'.join(C)+'\n')
	if os.name!=_p:
		try:os.chmod(B,384)
		except Exception:0
	os.replace(B,ENV_FILE)
_LOG_DIRS_READY=set()
_LOG_WRITE_CNT={}
_LOG_HANDLES={}
_LOG_LOCK=threading.Lock()
def get_logs_dir(state=_S):
	A=state
	if isinstance(A,dict):
		B=(A.get(_K)or'').strip()
		if B:return os.path.normpath(os.path.expanduser(B))
		C=(A.get(_D)or'').strip()
		if C:return os.path.normpath(os.path.expanduser(C))
	return DEFAULT_BACKUP_DIR
def write_file_log(text,target_dir=_S):
	from datetime import datetime as H;C=target_dir or DEFAULT_BACKUP_DIR
	try:
		with _LOG_LOCK:
			if C not in _LOG_DIRS_READY:os.makedirs(C,exist_ok=_A);_LOG_DIRS_READY.add(C)
			A=os.path.join(C,'backup.log');E=_LOG_WRITE_CNT.get(A,0);_LOG_WRITE_CNT[A]=E+1
			if E%50==0 and os.path.exists(A)and os.path.getsize(A)>52748288:
				if A in _LOG_HANDLES:_LOG_HANDLES.pop(A).close()
				try:
					with open(A,'rb')as F:F.seek(-153600,os.SEEK_END);D=F.read().decode(_C,errors='replace')
					G=D.find('\n')
					if G!=-1:D=D[G+1:]
					with open(A,'w',encoding=_C)as I:I.write('[Лог автоматично скорочено при перевищенні 512 МБ]\n'+D)
				except Exception:0
			B=_LOG_HANDLES.get(A)
			if B is _S:B=open(A,'a',encoding=_C,buffering=65536);_LOG_HANDLES[A]=B
			J=H.now().strftime('%Y-%m-%d %H:%M:%S');B.write(f"[{J}] {text}\n")
			if E%16==0:B.flush()
	except Exception:0
def flush_file_logs():
	with _LOG_LOCK:
		for A in _LOG_HANDLES.values():
			try:A.flush()
			except Exception:0
atexit.register(flush_file_logs)
def record_server_history(state,srv_url):
	A=state;B=(srv_url or'').strip().rstrip('/')
	if not B:return
	C=[A for A in A.get(_F)or[]if isinstance(A,str)and A.strip()and A.strip().rstrip('/')!=B];C.insert(0,B);A[_F]=C[:15]
def _norm_srv_key(u):
	return (u or '').strip().rstrip('!').rstrip('/')
def get_server_pins_map(state):
	raw = state.get('server_pins_json') or ''
	if not raw: return {}
	try:
		d = json.loads(raw)
		return d if isinstance(d, dict) else {}
	except Exception:
		return {}
def save_server_auth(state, srv_url):
	k = _norm_srv_key(srv_url)
	if not k: return
	m = get_server_pins_map(state)
	lp, ep, st = str(state.get(_z) or '').strip(), str(state.get(_A0) or '').strip(), str(state.get(_y) or '').strip()
	if lp or ep or st:
		m[k] = {'lp': lp, 'ep': ep, 'st': st}
	elif k in m:
		del m[k]
	state['server_pins_json'] = json.dumps(m, ensure_ascii=_B) if m else ''
	state[_I] = _A
def apply_server_auth(state, srv_url):
	k = _norm_srv_key(srv_url)
	m = get_server_pins_map(state)
	rec = m.get(k) if k else _S
	if isinstance(rec, dict):
		state[_z] = str(rec.get('lp') or '')
		state[_A0] = str(rec.get('ep') or '')
		state[_y] = str(rec.get('st') or '')
	else:
		state[_z] = ''
		state[_A0] = ''
		state[_y] = ''
def remove_server_auth(state, srv_url):
	k = _norm_srv_key(srv_url)
	m = get_server_pins_map(state)
	if k in m:
		del m[k]
		state['server_pins_json'] = json.dumps(m, ensure_ascii=_B) if m else ''
		state[_I] = _A
def load_state():
	A={};O='trash';J='pcloud';B={_E:'',_F:[],_T:[],'server_pins_json':'',_U:[],_L:0,_M:.0,_x:'',_y:'',_z:'',_A0:'',_D:DEFAULT_BACKUP_DIR,_K:'',_V:_A,_G:0,_N:'',_W:_B,_O:'',_X:_B,_Y:0,_Z:.0,_a:_A,_b:_J,_c:_B,_d:J,_A2:_A,_A3:_A,_A4:0,_P:.0,_A5:_A,_e:_A1,_Q:uuid.uuid4().hex,_A6:5,_A7:7,_A8:2,_A9:4,_AA:12,_AB:3,_f:O,_g:'en',_R:'dark',_h:_J,_H:0,_i:_A,_AC:_A,_j:_J,_s:_B,_k:_B,'hw_auto_notice':'','global_speed_optin':_B,'d1_use_cache':_A,'show_bottleneck':_A,'direct_cloud_write':_B,_l:'v8','archive_format':'tar.zst',_AD:_A,_AE:_B,_t:'03:00',_m:_w,_AF:_A,_AG:_B,_n:6,_o:'none',_I:_B};K=os.path.join(DEFAULT_BACKUP_DIR,_AK);E=CFG_FILE if os.path.exists(CFG_FILE)else K if os.path.exists(K)else''
	if E:
		try:
			with open(E,'r',encoding=_C)as P:A=json.load(P)
			if A.get(_E):B[_E]=str(A[_E]).strip()
			if isinstance(A.get(_U),list):B[_U]=A[_U][:25]
			if isinstance(A.get(_L),int)and A[_L]>=0:B[_L]=A[_L]
			if isinstance(A.get(_M),(int,float))and A[_M]>=0:B[_M]=round(float(A[_M]),1)
			if isinstance(A.get(_F),list):B[_F]=[str(A).strip()for A in A[_F]if str(A).strip()][:15]
			if isinstance(A.get(_T),list):B[_T]=[str(A).strip()for A in A[_T]if str(A).strip()][:8]
			if A.get(_D):B[_D]=os.path.expanduser(str(A[_D]).strip())
			if A.get(_K):B[_K]=os.path.expanduser(str(A[_K]).strip())
			if A.get(_N):B[_N]=os.path.expanduser(str(A[_N]).strip())
			if isinstance(A.get(_W),bool):B[_W]=A[_W]and bool(B[_N])
			if A.get(_O):B[_O]=os.path.expanduser(str(A[_O]).strip())
			if _G in A and A[_G]is not _S and int(A[_G])in(0,16,32,64,128,256,512,1024):B[_G]=int(A[_G])
			if isinstance(A.get(_V),bool):B[_V]=A[_V]
			if _Y in A:B[_Y]=max(0,int(A[_Y]or 0))
			if _Z in A:B[_Z]=max(.0,float(A[_Z]or .0))
			if isinstance(A.get(_a),bool):B[_a]=A[_a]
			B[_X]=_B;B[_O]=''
			B[_b]=_J
			if not IS_ANDROID and isinstance(A.get(_c),bool):B[_c]=A[_c]
			if isinstance(A.get(_d),str):B[_d]=A[_d].strip()or J
			if isinstance(A.get(_e),str):B[_e]=A[_e].strip()or _A1
			if isinstance(A.get(_Q),str)and re.fullmatch('[0-9a-f]{32}',A[_Q]):B[_Q]=A[_Q]
			else:B[_I]=_A
			if A.get(_g)in('en','uk'):B[_g]=A[_g]
			if A.get(_R)in VALID_THEMES:B[_R]=A[_R]
			if A.get(_h)in VALID_SCALES:B[_h]=A[_h]
			if isinstance(A.get(_H),int)and(A[_H]==0 or 8<=A[_H]<=28):B[_H]=A[_H]
			if isinstance(A.get(_i),bool):B[_i]=A[_i]
			if A.get(_l)in VALID_PBAR_STYLES:B[_l]=A[_l]
			B['archive_format']='tar.zst'
			if A.get(_f)in(O,'direct','permanent'):B[_f]=A[_f]
			if A.get(_j)in VALID_TRAY_BACKENDS:B[_j]=A[_j]
			for F in(_s,_k,_AD,_AE,_AF,_AG,_AC,_A2,_A3,_A5,'global_speed_optin','d1_use_cache','show_bottleneck','direct_cloud_write'):
				if isinstance(A.get(F),bool):B[F]=A[F]
			L=str(A.get(_t)or'').strip()
			if':'in L:
				G,H=L.split(':',1)
				if G.isdigit()and H.isdigit()and 0<=int(G)<=23 and 0<=int(H)<=59:B[_t]=f"{int(G):02d}:{int(H):02d}"
			if A.get(_m)in(_w,'--silent'):B[_m]=A[_m]
			if A.get(_n)in(2,4,5,6,7,8,9):B[_n]=A[_n]
			if isinstance(A.get(_P),(int,float))and A[_P]>=0:B[_P]=round(float(A[_P]),2)
			for D in(_A6,_A4,_A7,_A8,_A9,_AA,_AB):
				if D in A and isinstance(A[D],int)and A[D]>=0:B[D]=A[D]
			for C in SECRET_KEYS:
				if A.get(C):B[C]=str(A[C]).strip();B[_I]=_A
		except Exception:0
	if B[_E]:record_server_history(B,B[_E])
	if any(A in('--lite','/lite')for A in ARGS_LOW):B[_s]=_A
	if not B[_k]:
		B[_k]=_A
		if not E:B[_R]='dark'
		B[_I]=_A
	M=_B
	if HAS_KEYRING:
		try:
			for C in SECRET_KEYS:
				N=keyring.get_password(KEYRING_SERVICE,C)
				if N:B[C]=N.strip();M=_A
			B[_o]='keyring'
		except Exception:0
	I=_read_env_secrets()
	for C in SECRET_KEYS:
		if not B.get(C) and I.get(C):B[C]=I[C]
	if not M and(I or not HAS_KEYRING):B[_o]='env'
	if not B.get('server_pins_json') and isinstance(A.get('server_pins'),dict) and A['server_pins']:
		B['server_pins_json']=json.dumps(A['server_pins'],ensure_ascii=_B)
	if B[_E]:
		_pm=get_server_pins_map(B)
		if _norm_srv_key(B[_E]) in _pm:apply_server_auth(B,B[_E])
		elif B[_z] or B[_A0] or B[_y]:save_server_auth(B,B[_E])
	if IS_ANDROID:
		try:
			os.makedirs(B[_D],exist_ok=_A)
			with tempfile.TemporaryFile(dir=B[_D]):0
		except OSError:Q=os.environ.get('ANDROID_PRIVATE')or os.path.expanduser('~');B[_D]=os.path.join(Q,_q);os.makedirs(B[_D],exist_ok=_A);B['_android_storage_fallback']=_A;B[_I]=_A
	if B[_I]:commit_state(B)
	return B
def commit_state(state):
	A=state;_ensure_secure_dir()
	try:os.makedirs(A[_D],exist_ok=_A)
	except PermissionError:A[_D]=os.path.join(os.path.expanduser('~'),_q);os.makedirs(A[_D],exist_ok=_A)
	if A.get(_E):record_server_history(A,A[_E])
	F=_E,_F,_T,_U,_L,_M,_D,_V,_G,_K,_N,_W,_O,_X,_Y,_Z,_a,_b,_c,_d,_A2,_A3,_A4,_P,_A5,_e,_Q,_A6,_A7,_A8,_A9,_AA,_AB,_f,_g,_R,_h,_H,_i,_AC,_j,_s,_k,_l,'archive_format',_AD,_AE,_t,_m,_AF,_AG,_n,'global_speed_optin','d1_use_cache','show_bottleneck','direct_cloud_write';G={B:A[B]for B in F};G['server_pins']=get_server_pins_map(A);D=CFG_FILE+'.tmp'
	with open(D,'w',encoding=_C)as H:json.dump(G,H,indent=2,ensure_ascii=_B)
	os.replace(D,CFG_FILE);B=_B
	if HAS_KEYRING:
		try:
			for C in SECRET_KEYS:
				E=A.get(C,'')
				if E:keyring.set_password(KEYRING_SERVICE,C,E)
				else:
					try:keyring.delete_password(KEYRING_SERVICE,C)
					except Exception:0
			B=_A;A[_o]='keyring'
			if os.path.exists(ENV_FILE):os.remove(ENV_FILE)
		except Exception:B=_B
	if not B:_write_env_secrets(A);A[_o]='env'
	A[_I]=_B
