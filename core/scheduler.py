# [ФАЙЛ: core/scheduler.py (v2.01 | 22.11.2026 11:20) — ПЛАНИРОВЩИК ЗАДАЧ WINDOWS (SCHTASKS)]
_T='/Create'
_S='/Delete'
_R='# HomeGridBackup'
_Q='cp866'
_P='schtasks'
_O='utf-8'
_N='.exe'
_M='/F'
_L='00'
_K='03'
_J='delete'
_I='03:00'
_H='crontab'
_G='main.py'
_F='replace'
_E='/TN'
_D='--hidden'
_C='--silent'
_B=False
_A=True
import os,re,subprocess,sys,tempfile
from datetime import datetime
from core.config import SCHED_TASK_NAME
def is_compiled_app():
	if getattr(sys,'frozen',_B)or'__compiled__'in globals():return _A
	exe_name=os.path.basename(sys.executable or'').lower();return bool(exe_name.endswith(_N)and not exe_name.startswith('python'))
def _resolve_exe_path():
	A='HomeGridBackup.exe'
	if is_compiled_app():
		argv0=os.path.abspath(sys.argv[0]if sys.argv else'')
		if argv0.lower().endswith(_N)and os.path.exists(argv0):return argv0
	exe_p=os.path.abspath(sys.executable or'')
	if exe_p.lower().endswith(_N)and os.path.basename(exe_p).lower()not in('python.exe','pythonw.exe'):return exe_p
	root_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	for cand_name in(A,'main.exe','homegrid_backup1.exe'):
		cand_exe=os.path.join(root_dir,cand_name)
		if os.path.exists(cand_exe):return cand_exe
	return os.path.join(root_dir,A)
def _build_run_cmd(flag):
	if os.name=='nt':return f'"{_resolve_exe_path()}" {flag}'
	if is_compiled_app():bp=os.path.abspath(sys.argv if sys.argv else sys.executable);return f'"{bp}" {flag}'
	mp=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),_G);return f'"{sys.executable}" "{mp}" {flag}'
def _sync_scheduler_from_windows(st):
	B='sched_time';A='sched_mode'
	if os.name!='nt':
		if sys.platform=='darwin':
			pp=os.path.expanduser('~/Library/LaunchAgents/com.homegrid.backup.plist')
			if os.path.exists(pp):
				try:
					txt=open(pp,'r',encoding=_O).read();mh=re.search('<key>Hour</key>\\s*<integer>(\\d+)</integer>',txt);mm=re.search('<key>Minute</key>\\s*<integer>(\\d+)</integer>',txt)
					if mh and mm:st[B]=f"{int(mh.group(1)):02d}:{int(mm.group(1)):02d}"
					st[A]=_C if _C in txt else _D
				except Exception:0
			return
		try:
			out=subprocess.run([_H,'-l'],capture_output=_A,text=_A,timeout=4).stdout or''
			for ln in out.splitlines():
				if _R in ln:
					pt=ln.split()
					if len(pt)>=2 and pt[0].isdigit()and pt[1].isdigit():
						mm=int(pt[0]);hh=int(pt[1])
						if 0<=mm<=59 and 0<=hh<=23:st[B]=f"{hh:02d}:{mm:02d}"
					st[A]=_C if _C in ln else _D;break
		except Exception:0
		return
	try:
		res=subprocess.run([_P,'/Query',_E,SCHED_TASK_NAME,'/XML'],stdin=subprocess.DEVNULL,capture_output=_A,encoding=_Q,errors=_F,timeout=6,creationflags=134217728)
		if res.returncode!=0 or not res.stdout:return
		xml_txt=res.stdout;m_t=re.search('<StartBoundary>\\d{4}-\\d{2}-\\d{2}T(\\d{2}:\\d{2})',xml_txt)
		if m_t:st[B]=m_t.group(1)
		m_a=re.search('<Arguments>(.*?)</Arguments>',xml_txt)
		if m_a:
			args=m_a.group(1).strip()
			if _C in args:st[A]=_C
			elif _D in args:st[A]=_D
		m_p=re.search('<Priority>(\\d+)</Priority>',xml_txt)
		if m_p:st['sched_prio']=int(m_p.group(1))
		st['sched_missed']='<StartWhenAvailable>true</StartWhenAvailable>'in xml_txt;st['sched_wake']='<WakeToRun>true</WakeToRun>'in xml_txt
	except Exception:0
def _manage_macos_launchagent(action,time_str=_I,mode_flag=_D):
	B='unload';A='launchctl';plist_dir=os.path.expanduser('~/Library/LaunchAgents');plist_path=os.path.join(plist_dir,'com.homegrid.backup.plist')
	if action==_J:
		try:subprocess.run([A,B,plist_path],capture_output=_A,timeout=6)
		except Exception:0
		if os.path.exists(plist_path):
			try:os.remove(plist_path);return _A,'Завдання автозапуску macOS (LaunchAgent) видалено.'
			except Exception as e:return _B,f"Помилка видалення LaunchAgent: {e}"
		return _B,'Завдання автозапуску macOS не знайдено.'
	os.makedirs(plist_dir,exist_ok=_A);hh,mm=(time_str.split(':')+[_K,_L])[:2]
	if is_compiled_app():exe_p=os.path.abspath(sys.executable);prog_args=f"    <string>{exe_p}</string>\n    <string>{mode_flag}</string>"
	else:main_py=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),_G);prog_args=f"    <string>{sys.executable}</string>\n    <string>{main_py}</string>\n    <string>{mode_flag}</string>"
	plist_xml='<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://apple.com">\n<plist version="1.0">\n<dict>\n  <key>Label</key><string>com.homegrid.backup</string>\n  <key>ProgramArguments</key>\n  <array>\n'+prog_args+f"""
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>{int(hh)}</integer>
    <key>Minute</key><integer>{int(mm)}</integer>
  </dict>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
"""
	try:
		try:subprocess.run([A,B,plist_path],capture_output=_A,timeout=5)
		except Exception:0
		with open(plist_path,'w',encoding=_O)as pf:pf.write(plist_xml)
		subprocess.run([A,'load',plist_path],capture_output=_A,timeout=6);return _A,f"Завдання macOS LaunchAgent створено на {int(hh):02d}:{int(mm):02d} ({mode_flag})."
	except Exception as e:return _B,f"Помилка створення LaunchAgent: {e}"
def _manage_linux_scheduler(action,time_str=_I,mode_flag=_D):
	A='\n';autostart_dir=os.path.expanduser('~/.config/autostart');desktop_path=os.path.join(autostart_dir,'homegrid-backup.desktop');tag_mark=_R
	try:cur_cron=subprocess.run([_H,'-l'],capture_output=_A,text=_A,timeout=5).stdout or''
	except Exception:cur_cron=''
	kept_lines=[ln for ln in cur_cron.splitlines()if tag_mark not in ln and ln.strip()]
	if action==_J:
		removed_any=_B
		if os.path.exists(desktop_path):
			try:os.remove(desktop_path);removed_any=_A
			except Exception:0
		if len(kept_lines)!=len([ln for ln in cur_cron.splitlines()if ln.strip()]):
			try:new_c=A.join(kept_lines)+A if kept_lines else'';subprocess.run([_H,'-'],input=new_c,text=_A,capture_output=_A,timeout=5);removed_any=_A
			except Exception:0
		if removed_any:return _A,'Завдання Linux (crontab та автозапуск DE) видалено.'
		return _B,'Завдання Linux не знайдено або вже видалено.'
	hh,mm=(time_str.split(':')+[_K,_L])[:2]
	if is_compiled_app():bin_p=os.path.abspath(sys.argv[0]if sys.argv else sys.executable);cmd_str=f'"{bin_p}" {mode_flag}'
	else:main_py=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),_G);cmd_str=f'"{sys.executable}" "{main_py}" {mode_flag}'
	disp=os.environ.get('DISPLAY',':0');dbus_addr=os.environ.get('DBUS_SESSION_BUS_ADDRESS','');env_pref=f"DISPLAY={disp} "+(f'DBUS_SESSION_BUS_ADDRESS="{dbus_addr}" 'if dbus_addr else'');cron_line=f"{int(mm)} {int(hh)} * * * {env_pref}{cmd_str} >/dev/null 2>&1 {tag_mark}";kept_lines.append(cron_line)
	try:subprocess.run([_H,'-'],input=A.join(kept_lines)+A,text=_A,check=_A,capture_output=_A,timeout=6)
	except Exception as e:return _B,f"Помилка запису crontab: {e}"
	try:
		os.makedirs(autostart_dir,exist_ok=_A)
		with open(desktop_path,'w',encoding=_O)as df:df.write(f"""[Desktop Entry]
Type=Application
Name=HomeGrid Backup
Exec={cmd_str}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
""")
	except Exception:0
	return _A,f"Завдання Linux (crontab + autostart) створено на {int(hh):02d}:{int(mm):02d} ({mode_flag})."
def _manage_wsl_scheduler(action,time_str=_I,mode_flag=_C):
	A='/mnt/c/Windows/System32/schtasks.exe';from core.config import WSL_DISTRO;sch_bin=A if os.path.exists(A)else'schtasks.exe'
	if action==_J:res=subprocess.run([sch_bin,_S,_E,SCHED_TASK_NAME,_M],capture_output=_A,text=_A,errors=_F,timeout=8);return(_A,f"Завдання Windows '{SCHED_TASK_NAME}' (WSL) видалено.")if res.returncode==0 else(_B,'Завдання не знайдено або вже видалено.')
	hh,mm=(time_str.split(':')+[_K,_L])[:2];main_py=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),_G);eff_flag=_C if mode_flag==_D else mode_flag;d_arg=f"-d {WSL_DISTRO} "if WSL_DISTRO else'';tr_cmd=f'wsl.exe {d_arg}-- python3 "{main_py}" {eff_flag}';res=subprocess.run([sch_bin,_T,_E,SCHED_TASK_NAME,'/TR',tr_cmd,'/SC','DAILY','/ST',f"{int(hh):02d}:{int(mm):02d}",_M],capture_output=_A,text=_A,errors=_F,timeout=10);return(_A,f"Завдання Windows '{SCHED_TASK_NAME}' створено на {int(hh):02d}:{int(mm):02d} (WSL {eff_flag}).")if res.returncode==0 else(_B,f"Помилка schtasks.exe: {(res.stderr or res.stdout or"").strip()}")
def _manage_windows_scheduler(action,time_str=_I,mode_flag=_D,start_missed=_A,wake_pc=_B,prio=6):
	B='false';A='true';from core.config import IS_MAC,IS_WINDOWS,IS_WSL
	if IS_WSL:return _manage_wsl_scheduler(action,time_str,mode_flag)
	if IS_MAC:return _manage_macos_launchagent(action,time_str,mode_flag)
	if not IS_WINDOWS:return _manage_linux_scheduler(action,time_str,mode_flag)
	if action==_J:
		try:
			res=subprocess.run([_P,_S,_E,SCHED_TASK_NAME,_M],stdin=subprocess.DEVNULL,capture_output=_A,encoding=_Q,errors=_F,timeout=8,creationflags=134217728)
			if res.returncode==0:return _A,f"Завдання '{SCHED_TASK_NAME}' видалено з Планувальника."
			err_msg=(res.stderr or res.stdout or'').strip();return _B,f"Завдання не знайдено або вже видалено ({err_msg})."
		except Exception as e:return _B,f"Помилка видалення завдання: {e}"
	exe_path=_resolve_exe_path();work_dir=os.path.dirname(exe_path);hh,mm=(time_str.split(':')+[_K,_L])[:2];start_dt=f"{datetime.now().strftime("%Y-%m-%d")}T{int(hh):02d}:{int(mm):02d}:00";missed_xml=A if start_missed else B;wake_xml=A if wake_pc else B;prio_val=max(2,min(9,int(prio)));sl=chr(47);task_ns=f"http:{sl}{sl}schemas"+f".microsoft.com{sl}windows{sl}2004{sl}02{sl}mit{sl}task";xml_body=f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="{task_ns}">
  <RegistrationInfo><Description>HomeGrid Backup Scheduled Task</Description></RegistrationInfo>
  <Triggers><CalendarTrigger><StartBoundary>{start_dt}</StartBoundary><Enabled>true</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowHardTerminate>true</AllowHardTerminate><StartWhenAvailable>{missed_xml}</StartWhenAvailable><RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable><AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled><Hidden>false</Hidden><RunOnlyIfIdle>false</RunOnlyIfIdle><WakeToRun>{wake_xml}</WakeToRun><ExecutionTimeLimit>PT2H</ExecutionTimeLimit><Priority>{prio_val}</Priority></Settings>
  <Actions Context="Author"><Exec><Command>{exe_path}</Command><Arguments>{mode_flag}</Arguments><WorkingDirectory>{work_dir}</WorkingDirectory></Exec></Actions>
</Task>''';tmp_xml=os.path.join(tempfile.gettempdir(),'hgb_sched_task.xml')
	try:
		with open(tmp_xml,'w',encoding='utf-16')as xf:xf.write(xml_body)
		res=subprocess.run([_P,_T,_E,SCHED_TASK_NAME,'/XML',tmp_xml,_M],stdin=subprocess.DEVNULL,capture_output=_A,encoding=_Q,errors=_F,timeout=10,creationflags=134217728)
		if res.returncode==0:return _A,f"Завдання '{SCHED_TASK_NAME}' створено на {int(hh):02d}:{int(mm):02d} ({os.path.basename(exe_path)} {mode_flag})."
		err_msg=(res.stderr or res.stdout or'').strip();return _B,f"Помилка Планувальника: {err_msg}"
	except Exception as e:return _B,f"Збій створення завдання: {e}"
	finally:
		try:
			if os.path.exists(tmp_xml):os.remove(tmp_xml)
		except Exception:0
