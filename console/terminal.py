# patch-id: regex-stage-tr-4.09
# patch-id: stage-window-2.21
# [ФАЙЛ: console/terminal.py (v2.03 | 22.11.2026 09:10) — ВЫВОД В КОНСОЛЬ WINDOWS 7/10/11]
_C=False
_B='replace'
_A='\r'
import ctypes,os,re,sys,time
from datetime import datetime
from core.config import BUILD_DATE,CLI_MODE,HIDDEN_MODE,SCRIPT_VER,SILENT_MODE
_STAGE_TR_MAP=('Обробка на сервері','Processing on server'),('Перевірка сайту та сервера HGM...','Checking HGM host and server...'),('Перевірка сесії та авторизація...','Checking session and auth...'),('Запит на підготовку бекапу...','Requesting backup preparation...'),('Підготовка на сервері','Preparing on server'),('Копіювання бази та файлів','Copying DB & files'),('Перевірка файлів','Checking files'),('Стиснення ZIP-архіву','Packing ZIP'),('Архів готовий (75%). Завантаження...','Archive ready (75%). Downloading...'),('Архів готовий','Archive ready'),('Обробка','Processing'),('Збірка архіву на сервері','Building archive on server'),('Етап сервера','Server stage'),('Сервер HGM онлайн','HGM server online'),('Сервер http','Server http'),('Сервер ','Server '),('Завантаження','Downloading'),('Швидкість:','Speed:'),('МБ/с','MB/s'),('КБ/с','KB/s'),('МБ','MB'),('Перевірка CRC32','Verifying CRC32'),('Розрахунок SHA-256:','Calculating SHA-256:'),('Старі копії збережено (авторежим без видалення)...','Old backups kept (no-clean mode)...'),('Ротація бекапів за обраною стратегією...','Running GFS backup rotation...'),('Готово! Архів збережено','Done! Archive saved'),('Помилка:','Error:')
_STAGE_TR_DICT=dict(_STAGE_TR_MAP)
_STAGE_TR_RE=re.compile('|'.join(re.escape(k)for k in sorted(_STAGE_TR_DICT,key=len,reverse=True)))
def _stage_to_en(txt):
	A=re.sub('^\\[[^\\]]+\\]\\s*','',(txt or'').strip())
	return _STAGE_TR_RE.sub(lambda m:_STAGE_TR_DICT[m.group(0)],A)
def _safe_con_write(text):
	A=text
	if not A:return
	if os.name=='nt':
		try:
			C=ctypes.windll.kernel32;B=C.GetStdHandle(-11)
			if B and B!=-1 and B!=0:
				E=ctypes.c_ulong(0)
				if C.WriteConsoleW(B,ctypes.c_wchar_p(A),len(A),ctypes.byref(E),None):return
		except Exception:0
	try:sys.stdout.write(A);sys.stdout.flush()
	except Exception:
		try:D=getattr(sys.stdout,'encoding',None)or'cp866';sys.stdout.write(A.encode(D,errors=_B).decode(D,errors=_B));sys.stdout.flush()
		except Exception:0
def _print_cli_banner():
	F='net_dir';E='OFF';D='+\n';C='|\n';B='|';from core.config import get_fast_sysinfo as G;H=G();I=f"  HomeGrid Backup v{SCRIPT_VER} ({BUILD_DATE}) - Inverter Data Backup";J=f"  {H}"[:76];_safe_con_write('+'+'-'*76+D);_safe_con_write(B+I.ljust(76)+C);_safe_con_write(B+J.ljust(76)+C)
	try:from core.config import load_state as K;A=K();L=A.get('backup_dir','')if A.get('local_enabled',True)else E;M=A.get(F,'')if A.get('net_enabled')and A.get(F)else E;N=f"  Storage | Local: {L} | Network: {M}"[:76];_safe_con_write(B+N.ljust(76)+C)
	except Exception:0
	_safe_con_write('+'+'-'*76+D)
def _init_console_for_cli():
	C='CONOUT$';B='utf-8'
	if os.name!='nt':
		try:
			if sys.stdout.isatty():_safe_con_write(f"]0;HomeGrid Backup v{SCRIPT_VER}\a")
		except Exception:0
		_print_cli_banner();return
	try:
		A=ctypes.windll.kernel32
		if A.GetConsoleWindow()==0:
			if not A.AttachConsole(-1):A.AllocConsole()
		try:A.SetConsoleOutputCP(65001);A.SetConsoleCP(65001);A.SetConsoleTitleW(f"HomeGrid Backup v{SCRIPT_VER} ({BUILD_DATE}) - Inverter Data Backup")
		except Exception:0
		try:sys.stdout=open(C,'w',encoding=B,errors=_B,buffering=1);sys.stderr=open(C,'w',encoding=B,errors=_B,buffering=1);sys.stdin=open('CONIN$','r',encoding=B,errors=_B)
		except Exception:0
		_print_cli_banner()
	except Exception:0
def _print_cli_line(engine,force=_C):
	A=engine
	if HIDDEN_MODE or not(CLI_MODE or SILENT_MODE):return
	C=time.time()
	if not force and C-A._last_cli_print<1.:return
	A._last_cli_print=C;B=_stage_to_en(A.stage)
	if A.indeterminate:D='[  working...  ]';E=' ...'
	else:F=max(0,min(100,int(A.progress)));G=int(round(F/1e2*16));D='['+'#'*G+'.'*(16-G)+']';E=f"{F:3d}%"
	H=54
	if len(B)>H:B=B[:H-3]+'...'
	I=f"{D} {E} | {B}"
	if SILENT_MODE and not CLI_MODE:_safe_con_write(_A+I[:78].ljust(78));A._cli_inline_active=True
	else:J=datetime.now().strftime('%H:%M:%S');_safe_con_write(f"[{J}] {I}\n")
def _finish_cli_inline(engine):
	A=engine
	if getattr(A,'_cli_inline_active',_C):_safe_con_write(_A+' '*78+_A);A._cli_inline_active=_C
def run_silent_exit_countdown(engine,total_sec=8):
	if HIDDEN_MODE or not SILENT_MODE:return
	_finish_cli_inline(engine);_safe_con_write('-'*78+'\n')
	for A in range(total_sec,0,-1):B=f"[OK] Done! Window will close automatically in {A}s...";_safe_con_write(_A+B.ljust(78));time.sleep(1.)
	_safe_con_write(_A+' '*78+_A)
