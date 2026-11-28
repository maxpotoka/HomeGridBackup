# patch-id: safe-tkinter-fallback-and-apt-hint-4.09
# patch-id: linux-single-instance-exit-4.09
# patch-id: no-pip-auto-install-and-uk-tray-hints-3.96
# patch-id: strict-ssl-verify-3.75
# patch-id: main-nuitka-global-ssl-3.73
# patch-id: main-zstd-dep-3.37
#!/usr/bin/env python3
# [ФАЙЛ: main.py (v2.10 | 28.11.2026 07:05) — ТОЧКА ВХОДА, MUTEX, CRASH-ЛОГ И ЛЕНИВЫЙ ЗАПУСК РЕЖИМОВ]
#!/usr/bin/env python3
_E='pystray'
_D='keyring'
_C='send2trash'
_B=False
_A=True
import ctypes,os,ssl,subprocess,sys
try:
	_ca_p=''
	try:
		import certifi as _cert;_ca_p=_cert.where()
	except Exception:0
	if not(_ca_p and os.path.isfile(_ca_p)):
		for _cand_ca in('/etc/ssl/cert.pem','/usr/local/etc/openssl@3/cert.pem','/opt/homebrew/etc/openssl@3/cert.pem','/etc/ssl/certs/ca-certificates.crt'):
			if os.path.isfile(_cand_ca):_ca_p=_cand_ca;break
	if _ca_p and os.path.isfile(_ca_p):
		os.environ.setdefault('SSL_CERT_FILE',_ca_p);os.environ.setdefault('REQUESTS_CA_BUNDLE',_ca_p)
		ssl._create_default_https_context=lambda *_a,**_kw:ssl.create_default_context(cafile=_ca_p)
	else:
		sys.stderr.write('[HomeGridBackup] WARNING: CA bundle not found, strict SSL verification kept\n')
except Exception:0
try:import faulthandler;_crash_dir=os.path.join(os.path.expanduser('~'),'.backup_hgm');os.makedirs(_crash_dir,exist_ok=_A);_crash_fp=open(os.path.join(_crash_dir,'crash.log'),'a',encoding='utf-8');faulthandler.enable(_crash_fp)
except Exception:0
from core.config import IS_ANDROID
from core.scheduler import is_compiled_app
_APP_MUTEX=None
_SHOW_EVENT_NAME='Global\\HomeGridBackup_ShowWindow_v1'
_IS_PY_CONSOLE_LAUNCHER=not is_compiled_app()and sys.executable.lower().endswith('python.exe')and not any(A.lower()in('--cli','--console','-c','/console','--silent','-s','/silent','/s')for A in sys.argv[1:])
if not _IS_PY_CONSOLE_LAUNCHER:
	try:
		_k32=ctypes.windll.kernel32;_APP_MUTEX=_k32.CreateMutexW(None,_A,'Global\\HomeGridBackup_SingleInstance_v1')
		if _k32.GetLastError()==183:
			_h_ev=_k32.OpenEventW(2,_B,_SHOW_EVENT_NAME)
			if _h_ev:_k32.SetEvent(_h_ev);_k32.CloseHandle(_h_ev)
			os._exit(0)
	except Exception:0
	if os.name!='nt':
		try:
			import fcntl,hashlib,socket,tempfile;_inst_id=hashlib.md5(os.path.realpath(sys.argv[0]).encode('utf-8',errors='ignore')).hexdigest()[:10];_lock_p=os.path.join(tempfile.gettempdir(),f"hgb_inst_{_inst_id}.lock");_port_p=os.path.join(tempfile.gettempdir(),f"hgb_inst_{_inst_id}.port");_APP_MUTEX=open(_lock_p,'w')
			try:fcntl.flock(_APP_MUTEX.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
			except OSError:
				try:
					if os.path.exists(_port_p):
						with open(_port_p,'r')as pf:p_num=int(pf.read().strip()or'0')
						if p_num>0:
							with socket.create_connection(('127.0.0.1',p_num),timeout=.6)as sk:sk.sendall(b'SHOW')
				except Exception:0
				os._exit(0)
		except Exception:0
if not is_compiled_app()and not IS_ANDROID:
	_missing_pkgs=[]
	_chk_list=[(_C,_C),(_D,_D),(_E,_E),('PIL','pillow'),('zstandard','zstandard')]+([('tkinter','tkinter')]if not any(a.lower()in('--cli','--console','-c','/console','--silent','-s','/silent','/s','--hidden','--background','/hidden','/h')for a in sys.argv[1:])else[])
	for(_mod,_pkg)in _chk_list:
		try:__import__(_mod)
		except ImportError:_missing_pkgs.append(_pkg)
	if _missing_pkgs:
		_apt_map={'tkinter':'python3-tk','pillow':'python3-pil','zstandard':'python3-zstandard','keyring':'python3-keyring','send2trash':'python3-send2trash'}
		_apt_pkgs=[_apt_map[p]for p in _missing_pkgs if p in _apt_map]
		_hint_cmd=(f"sudo apt install {' '.join(_apt_pkgs)}"if _apt_pkgs else f"pip install --break-system-packages {' '.join(_missing_pkgs)}")if sys.platform.startswith('linux')else "pip install -r requirements.txt"
		print(f"[HomeGrid Backup] \u0412\u0456\u0434\u0441\u0443\u0442\u043d\u0456 \u043f\u0430\u043a\u0435\u0442\u0438: {', '.join(_missing_pkgs)}. \u0412\u0441\u0442\u0430\u043d\u043e\u0432\u0456\u0442\u044c \u043a\u043e\u043c\u0430\u043d\u0434\u043e\u044e: {_hint_cmd}",flush=_A)
from core.backup import run_backup_task
from core.config import CLI_MODE,GUI_MODE,HIDDEN_MODE,NO_CLEAN,SILENT_MODE
from core.engine import BackupEngine
def main():
	D='server'
	if(SILENT_MODE or CLI_MODE)and not HIDDEN_MODE:from console.terminal import _init_console_for_cli as G;G()
	A=BackupEngine();B=A.state;E=bool(NO_CLEAN or not B.get('silent_cleanup',_B))
	if CLI_MODE and not GUI_MODE:from console.terminal import _finish_cli_inline as H;run_backup_task(A,B.get(D,''),_B,NO_CLEAN,_B);H(A);sys.exit(A.exit_code)
	if(SILENT_MODE or HIDDEN_MODE)and not GUI_MODE:
		if HIDDEN_MODE:from gui.tray import _force_quit_app as I,_start_tray_thread as C;C(A);run_backup_task(A,B.get(D,''),_A,E,_A);I(A)
		else:from console.terminal import run_silent_exit_countdown as J;run_backup_task(A,B.get(D,''),_A,E,_B);J(A,8);os._exit(A.exit_code)
		return
	if IS_ANDROID:from mobile.android_app import run_android_ui as K;K(A);return
	try:import tkinter as L
	except ImportError:
		_tk_hint='sudo apt install python3-tk'if sys.platform.startswith('linux')else'Install Python with Tcl/Tk support'
		A.log(f"\u041c\u043e\u0434\u0443\u043b\u044c tkinter \u0432\u0456\u0434\u0441\u0443\u0442\u043d\u0456\u0439 ({_tk_hint}). \u041f\u0435\u0440\u0435\u0445\u0456\u0434 \u0443 \u043a\u043e\u043d\u0441\u043e\u043b\u044c\u043d\u0438\u0439 \u0440\u0435\u0436\u0438\u043c CLI...",'warn')
		if GUI_MODE:sys.exit(1)
		from console.terminal import _init_console_for_cli as G,_finish_cli_inline as H;G();run_backup_task(A,B.get(D,''),_B,NO_CLEAN,_B);H(A);sys.exit(A.exit_code)
	from gui.tray import _start_show_window_listener as M,_start_tray_thread as C;from gui.window import HomeGridApp as N
	try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
	except Exception:
		try:ctypes.windll.user32.SetProcessDPIAware()
		except Exception:0
	F=L.Tk(className='HomeGridBackup');O=N(F,A);A.app_ref=O;M(A,_SHOW_EVENT_NAME);C(A);F.mainloop()
if __name__=='__main__':main()
