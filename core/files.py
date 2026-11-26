# patch-id: files-packing-tarzst-3.39
# [ФАЙЛ: core/files.py (v2.08 | 22.11.2026 09:10) — ФАЙЛОВЫЕ УТИЛИТЫ WINDOWS (КОРЗИНА, ПАПКИ, ДАТЫ)]
_B=False
_A=True
import os,re,shutil
from datetime import datetime
try:from send2trash import send2trash
except ImportError:send2trash=None
def pretty_phase(ph):
	A='Обробка на сервері';p=str(ph or'').lower()
	if'db'in p or'connect'in p:return'Підключення до бази даних'
	if'history'in p or'device'in p:return'Копіювання історії розумних пристроїв'
	return{'copying':'Копіювання бази та файлів','checking':'Перевірка файлів','packing':'Стиснення архіву TAR.ZST','preparing':'Підготовка на сервері','processing':A,'ready':'Архів готовий'}.get(p,A)
def send_to_recycle_bin(filepath):
	abs_path=os.path.abspath(filepath)
	if send2trash is not None:
		try:send2trash(abs_path);return _A
		except Exception:0
	try:trash_dir=os.path.join(os.path.dirname(abs_path),'.trash_hgm');os.makedirs(trash_dir,exist_ok=_A);shutil.move(abs_path,os.path.join(trash_dir,os.path.basename(abs_path)));return _A
	except Exception:return _B
def remove_backup_file(filepath,delete_mode='trash'):
	abs_path=os.path.abspath(filepath)
	if not os.path.exists(abs_path):return _A
	if delete_mode in('direct','permanent'):
		try:os.remove(abs_path);return _A
		except Exception:return _B
	return send_to_recycle_bin(abs_path)
def _open_path_os(target_path):
	import subprocess,sys
	if os.name=='nt':os.startfile(target_path)
	elif sys.platform=='darwin':subprocess.Popen(['open',target_path])
	else:subprocess.Popen(['xdg-open',target_path])
def open_folder_native(folder_path):
	os.makedirs(folder_path,exist_ok=_A)
	try:_open_path_os(folder_path);return _A
	except Exception:return _B
def open_file_native(file_path):
	parent=os.path.dirname(os.path.abspath(file_path));os.makedirs(parent,exist_ok=_A)
	if not os.path.exists(file_path):
		try:
			with open(file_path,'w',encoding='utf-8')as f:f.write('')
		except Exception:0
	try:_open_path_os(file_path);return _A
	except Exception:return _B
def choose_folder_native(initial_dir,lang='en'):
	B='zenity';A='kdialog';import subprocess,sys;from core.i18n import tr;dlg_t=tr('Оберіть папку',lang)
	if sys.platform.startswith('linux'):
		start_d=initial_dir.rstrip('/')+'/'if initial_dir and os.path.isdir(initial_dir)else os.path.expanduser('~/');de=(os.environ.get('XDG_CURRENT_DESKTOP')or'').upper();tools=[(A,[A,'--getexistingdirectory',start_d,'--title',dlg_t]),(B,[B,'--file-selection','--directory',f"--title={dlg_t}",f"--filename={start_d}"])]
		if not any(k in de for k in('KDE','LXQT')):tools.reverse()
		for(bin_name,cmd)in tools:
			if shutil.which(bin_name):
				try:
					res=subprocess.run(cmd,capture_output=_A,text=_A,timeout=120)
					if res.returncode==0 and res.stdout.strip():return os.path.normpath(res.stdout.strip())
					if res.returncode==1:return''
				except Exception:0
	try:from tkinter import filedialog;chosen=filedialog.askdirectory(initialdir=initial_dir,title=dlg_t);return os.path.normpath(chosen)if chosen else''
	except Exception:return''
_ENG_WEEKDAYS='Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'
_ENG_MONTHS='January','February','March','April','May','June','July','August','September','October','November','December'
def format_backup_dt(dt):wday=_ENG_WEEKDAYS[dt.weekday()];return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}_{wday}_{dt.hour:02d}-{dt.minute:02d}-{dt.second:02d}"
def parse_backup_dt(filename,fallback_ts):
	m_num=re.search('(\\d{4})-(\\d{2})-(\\d{2})_[^_]+_(\\d{2})-(\\d{2})',filename)
	if m_num:
		try:y,mo,d,hh,mm=(int(x)for x in m_num.groups());return datetime(y,mo,d,hh,mm)
		except Exception:0
	m_mon=re.search('(\\d{4})-([A-Za-z]+)-(\\d{2})_[^_]+_(\\d{2})-(\\d{2})',filename)
	if m_mon:
		try:
			y_s,mon_s,d_s,hh_s,mm_s=m_mon.groups();mon_idx=next((i+1 for(i,nm)in enumerate(_ENG_MONTHS)if nm.lower()==mon_s.lower()),0)
			if mon_idx:return datetime(int(y_s),mon_idx,int(d_s),int(hh_s),int(mm_s))
		except Exception:0
	return datetime.fromtimestamp(fallback_ts)
def format_duration(sec,lang='uk'):
	raw=max(.0,float(sec or .0));s=1 if raw<1. else int(round(raw))
	if s<60:return f"{s} с"if lang=='uk'else f"{s} s"
	mins,rem=divmod(s,60);return f"{mins} хв {rem} с ({s} с)"if lang=='uk'else f"{mins}m {rem}s ({s}s)"
def get_app_icon_path():
	A='icon.ico';import sys;module_dir=os.path.dirname(os.path.abspath(__file__));compiled_dir=getattr(globals().get('__compiled__'),'containing_dir','');cands=[]
	if compiled_dir:cands.extend((os.path.join(compiled_dir,A),os.path.join(os.path.dirname(compiled_dir),'Resources',A)))
	cands.extend((os.path.join(module_dir,A),os.path.join(os.path.dirname(module_dir),A),os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),A),os.path.join(os.path.dirname(os.path.abspath(sys.executable)),A),os.path.join(getattr(sys,'_MEIPASS',''),A),os.path.join(os.getcwd(),A)))
	for c in cands:
		if c and os.path.isfile(c):return c
	return''
