# patch-id: main-zstd-dep-3.37
#!/usr/bin/env python3
# [ФАЙЛ: main.py (v2.04 | 23.11.2026 16:35) — ТОЧКА ВХОДА, MUTEX, CRASH-ЛОГ И ЛЕНИВЫЙ ЗАПУСК РЕЖИМОВ]
#!/usr/bin/env python3
_E='pystray'
_D='keyring'
_C='send2trash'
_B=False
_A=True
import ctypes,os,subprocess,sys
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
				if os.path.exists(_port_p):
					with open(_port_p,'r')as pf:p_num=int(pf.read().strip()or'0')
					if p_num>0:
						with socket.create_connection(('127.0.0.1',p_num),timeout=.6)as sk:sk.sendall(b'SHOW')
				os._exit(0)
		except Exception:0
if not is_compiled_app()and not IS_ANDROID:
	_missing_pkgs=[]
	for(_mod,_pkg)in((_C,_C),(_D,_D),(_E,_E),('PIL','pillow'),('zstandard','zstandard')):
		try:__import__(_mod)
		except ImportError:_missing_pkgs.append(_pkg)
	if _missing_pkgs:
		print(f"[HomeGrid Backup] Устанавливаю недостающие пакеты: {', '.join(_missing_pkgs)} ...",flush=_A)
		try:
			_res=subprocess.run([sys.executable,'-m','pip','install','--user']+_missing_pkgs,timeout=300)
			if _res.returncode!=0:print(f"[HomeGrid Backup] Ошибка установки (код {_res.returncode}). Установите вручную: pip install {' '.join(_missing_pkgs)}",flush=_A)
		except Exception as _e:print(f"[HomeGrid Backup] Не удалось установить пакеты: {_e}",flush=_A)
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
	import tkinter as L;from gui.tray import _start_show_window_listener as M,_start_tray_thread as C;from gui.window import HomeGridApp as N
	try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
	except Exception:
		try:ctypes.windll.user32.SetProcessDPIAware()
		except Exception:0
	F=L.Tk(className='HomeGridBackup');O=N(F,A);A.app_ref=O;M(A,_SHOW_EVENT_NAME);C(A);F.mainloop()
if __name__=='__main__':main()
