# patch-id: fix-net-drive-status-and-build-retry-2.78
# patch-id: idle-ui-cache-2.19
# patch-id: stage-window-2.21
# patch-id: archive-scan-cache-2.04
# patch-id: android-storage-fallback-2.06
# patch-id: archives-label-and-logs-dir-2.60
# patch-id: dest-stats-bg-worker-2.61
# patch-id: split-last-backup-2.68
# [ФАЙЛ: core/engine.py (v2.09 | 24.11.2026 00:35) — ЯДРО ДВИЖКА BACKUPENGINE]
_b='.sha256'
_a='_dest_stats_started'
_Z='pcloud'
_Y='size_mb'
_X='detail'
_W='%d.%m.%Y %H:%M'
_V='mtime'
_U='path'
_T='size'
_S='network'
_R='mirror'
_Q='Успішно'
_P='.zip'
_O='ts'
_N='warn'
_M='info'
_L='status'
_K='idle'
_J='dur_sec'
_I='op_history'
_H='en'
_G='ok'
_F='backup_dir'
_E='lang'
_D=True
_C=.0
_B=False
_A=None
import atexit,getpass,os,re,shutil,threading,time
from datetime import datetime
from core.config import BUILD_DATE,CLI_MODE,HIDDEN_MODE,IS_WSL,NO_CLEAN,SCRIPT_VER,SILENT_MODE,WSL_DISTRO,get_fast_sysinfo,get_logs_dir,load_state,write_file_log
from core.i18n import tr
_CON_TR_MAP=('Обробка на сервері','Processing on server'),('Систему запущено','System started'),('сховище:','storage:'),('Каталог:','Dir:'),('Перевірку сайту/порту пропущено для','Host/port check skipped for'),('Сервер HGM онлайн','HGM server online'),('Активну сесію підтверджено.','Active session confirmed.'),('Збережена сесія застаріла. Повторний вхід...','Saved session expired. Re-login...'),('Авторизація успішна!','Authorization successful!'),('Авторизацію підтверджено сервером!','Authorization confirmed by server!'),('Збірка архіву на сервері','Building archive on server'),('Етап сервера','Server stage'),('Копіювання бази та файлів','Copying database and files'),('Перевірка файлів','Checking files'),('Стиснення ZIP-архіву','Packing ZIP archive'),('Підготовка на сервері','Preparing on server'),('Архів готовий','Archive ready'),('Завантаження ZIP-архіву з','Downloading ZIP archive from'),('Архів завантажено:','Archive downloaded:'),('Цілісність перевірено','Integrity verified'),('файлів','files'),('файл(ів)','file(s)'),('Збережено','Saved'),('Дзеркальну копію збережено у:','Mirror copy saved to:'),('Попередження: не вдалося скопіювати у дзеркальну папку','Warning: failed to copy to mirror dir'),('Налаштування та ключі захищено збережено.','Settings and keys securely saved.'),('Режим збереження: очищення застарілих архівів пропущено.','Keep mode: old archive cleanup skipped.'),('Переміщено у Кошик:','Moved to Recycle Bin:'),('Видалено з диска назавжди:','Deleted permanently:'),('Очищення застарілих архівів пропущено.','Old archive cleanup skipped.'),('УСПІХ! Резервне копіювання завершено за','SUCCESS! Backup completed in'),('ПОМИЛКА:','ERROR:'),('Адресу не вказано. Запуск автопошуку в LAN...','Address empty. Starting LAN auto-scan...'),('Сканування підмереж:','Scanning subnets:'),('Активні мережеві адаптери LAN не знайдено!','No active LAN network adapters found!'),('Автоматично обрано сервер:','Auto-selected server:'),('Сервер скинув завдання. Повторний запуск збірки...','Server reset job. Restarting build...'),('Збій завантаження','Download failed'),('завантажено лише','downloaded only'),('обрив потоку','stream interrupted'),('Повтор','Retry'),('через','in'),('ICMP Ping до','ICMP Ping to'),("без відповіді, перевірка з'єднання",'no reply, checking connection')
_CON_TR_SORTED=sorted(_CON_TR_MAP,key=lambda x:len(x),reverse=_D)
def _to_con_en(txt):
	A=str(txt)
	for(B,C)in _CON_TR_SORTED:A=A.replace(B,C)
	A=re.sub('\\bМБ/с\\b','MB/s',A);A=re.sub('\\bКБ/с\\b','KB/s',A);A=re.sub('\\bМБ\\b','MB',A);A=re.sub('\\bмс\\b','ms',A);A=re.sub('(\\d+)\\s*хв\\s*([\\d.]+)\\s*с','\\1m \\2s',A);A=re.sub('(?<=\\d)\\s*с(?=\\b|\\)|\\.)',' s',A);A=re.sub('\\bза\\s+(?=\\d)','in ',A);A=re.sub('\\bіз\\s+(?=\\d)','of ',A);return A
class BackupEngine:
	def __init__(A):
		A.state=load_state();A.lock=threading.Lock();A.cloud_sync_worker_lock=threading.Lock();A.is_running=_B;A.show_hw_notice=bool(A.state.get('hw_auto_notice'));A.progress=0;A.indeterminate=_B;A.sys_summary=get_fast_sysinfo();A.stage=tr('Готовий до резервного копіювання',A.state.get(_E,_H));A.pill_text=f"v{SCRIPT_VER} | {BUILD_DATE}";A.pill_type=_K;A.op_history=list(A.state.get(_I)or[]);A.diag_net='Не перевірено';A.diag_ping='— мс';A.logs=[];A._file_log_buf=[];A._file_log_last_flush=time.monotonic();atexit.register(A.flush_logs);A.modal=_A;A.modal_event=threading.Event();A.modal_result=_A;A.exit_code=0;A.tray_icon=_A;A.tray_spin_idx=0;A.app_ref=_A;A._last_cli_print=_C;A._cli_inline_active=_B;A._storage_stats_cache=_A;A._storage_stats_cache_time=_C;A._storage_stats_cache_dir=_A;A._last_backup_cache=_A;A._last_backup_cache_time=_C;A._last_backup_cache_dir=_A;A._archive_snapshot_cache=_A;A._archive_snapshot_cache_time=_C;A._archive_snapshot_cache_dir=_A;A._dest_stats={_R:_A,_S:_A,_Z:_A};A._dest_stats_event=threading.Event();A._dest_stats_started=_B;os.makedirs(A.state[_F],exist_ok=_D);B='HIDDEN'if HIDDEN_MODE else'SILENT'if SILENT_MODE else'CLI'if CLI_MODE else'APP';C='Keyring'if A.state['storage_backend']=='keyring'else'.env';A.log(f"Систему запущено (v{SCRIPT_VER} від {BUILD_DATE}, {B}, сховище: {C}). Каталог: {A.state[_F]}",_M)
		if A.state.pop('_android_storage_fallback',_B):A.log(f"Папка резервних копій недоступна; використовується внутрішнє сховище Android: {A.state[_F]}",_N)
		A.log(f"ОС та залізо: {A.sys_summary}",_M);from core.config import AUTO_CLI_FALLBACK as D
		if D:A.log('Графічний сервер (DISPLAY/WSLg) недоступний — автоматично увімкнено консольний режим (--cli).',_N)
		if IS_WSL:
			E=WSL_DISTRO or'Linux';A.log(f"Робота в WSL (дистрибутив: {E}), режим: {B}",_M)
			if os.path.abspath(A.state[_F]).startswith('/mnt/'):A.log('Папка архівів на диску Windows (/mnt/): права POSIX не застосовуються, швидкість I/O нижча.',_N)
	def flush_logs(A):
		with A.lock:
			if not A._file_log_buf:return
			B=list(A._file_log_buf);A._file_log_buf.clear();A._file_log_last_flush=time.monotonic()
		try:
			C=get_logs_dir(A.state)
			for D in B:write_file_log(D,C)
		except Exception:0
	def log(A,msg,level=_M):
		C=level;B=msg;B=tr(B,A.state.get(_E,_H));E=datetime.now().strftime('%H:%M:%S');G=f"[{C.upper()}] {B}";H=C in('err',_G);D=_A
		with A.lock:
			A._file_log_buf.append(G);F=time.monotonic()
			if H or len(A._file_log_buf)>=20 or F-A._file_log_last_flush>=4.:D=chr(10).join(A._file_log_buf);A._file_log_buf.clear();A._file_log_last_flush=F
		if D:
			try:write_file_log(D,get_logs_dir(A.state))
			except Exception:0
		if CLI_MODE or SILENT_MODE and not HIDDEN_MODE:from console.terminal import _finish_cli_inline as I,_safe_con_write as J;I(A);K=max(0,min(100,int(A.progress)));J(f"[{E}] ({K:3d}%) {_to_con_en(B)}\n")
		with A.lock:
			A.logs.append({_O:E,'msg':B,'level':C})
			if len(A.logs)>400:A.logs=A.logs[-400:]
	def set_progress(A,pct,stage_text=_A):
		C=stage_text
		with A.lock:
			B=_B
			if pct is _A:
				if not A.indeterminate:A.indeterminate=_D;B=_D
			else:
				D=max(0,min(100,int(pct)))
				if A.indeterminate or D!=A.progress:B=_D
				A.indeterminate=_B;A.progress=D
			if C is not _A:
				E=tr(C,A.state.get(_E,_H))
				if E!=A.stage:B=_D;A.stage=E
		if B and not HIDDEN_MODE and(CLI_MODE or SILENT_MODE):from console.terminal import _print_cli_line as F;F(A)
	def set_pill(A,text,state_type=_K):
		B=state_type
		with A.lock:
			C=tr(text,A.state.get(_E,_H))
			if C!=A.pill_text or B!=A.pill_type:A.pill_text=C;A.pill_type=B
	def ask_modal(A,mtype,title,text,default_val=''):
		F='confirm';D=text;C=mtype;B=title;E=A.state.get(_E,_H);B,D=tr(B,E),tr(D,E)
		if SILENT_MODE:return not NO_CLEAN if C==F else''
		if CLI_MODE:
			from console.terminal import _finish_cli_inline as G;G(A)
			if C=='pin':return getpass.getpass(f"[{B}] Enter PIN: ").strip()
			elif C==F:H=input(f"[{B}] Confirm? [y/N]: ").strip().lower();return H in('y','yes','так','д')
			return''
		A.modal_event.clear();A.modal_result=_A
		with A.lock:A.modal={'id':int(time.time()*1000),'type':C,'title':B,'text':D,'default':default_val}
		A.modal_event.wait();return A.modal_result
	def submit_modal(A,val):
		with A.lock:A.modal=_A
		A.modal_result=val;A.modal_event.set()
	def start_dest_stats_worker(A):
		if getattr(A,_a,_B):A._dest_stats_event.set();return
		A._dest_stats_started=_D;threading.Thread(target=A._dest_stats_loop,name='dest-stats-worker',daemon=_D).start()
	def request_dest_stats_refresh(A):
		if not getattr(A,_a,_B):A.start_dest_stats_worker()
		else:A._dest_stats_event.set()
	def _scan_dir_brief(K,raw_path,prev_res=_A):
		E='free_gb';A=prev_res;B=os.path.expanduser((raw_path or'').strip())
		if not B:return{_G:_B}
		try:
			if not os.path.isdir(B):
				if isinstance(A,dict)and A.get(_G):return dict(A,stale=_D)
				return{_G:_B}
			F,G=0,0
			with os.scandir(B)as H:
				for C in H:
					if not C.name.startswith('.')and C.name.lower().endswith(_P)and C.is_file(follow_symlinks=_B):F+=1;G+=C.stat(follow_symlinks=_B).st_size
			D=-1.
			try:I,I,J=shutil.disk_usage(B);D=round(J/1073741824.,1)
			except Exception:
				if isinstance(A,dict)and A.get(E,-1)>=0:D=A[E]
		except Exception:
			if isinstance(A,dict)and A.get(_G):return dict(A,stale=_D)
			return{_G:_B}
		return{_G:_D,'count':F,'mb':round(G/1048576.,1),E:D}
	def _dest_stats_loop(A):
		F='net_dir';E='mirror_dir'
		while _D:
			A._dest_stats_event.clear();B=A.state
			with A.lock:D=dict(getattr(A,'_dest_stats',{})or{})
			G=A._scan_dir_brief(B.get(E),D.get(_R))if B.get('mirror_enabled')and(B.get(E)or'').strip()else _A;H=A._scan_dir_brief(B.get(F),D.get(_S))if B.get('net_enabled')and(B.get(F)or'').strip()else _A;C=_A
			if B.get('cloud_enabled'):
				try:from core.cloud import get_cloud_dest_stats as I;C=I(B)
				except Exception:C={_G:_B}
			with A.lock:A._dest_stats={_R:G,_S:H,_Z:C}
			A._dest_stats_event.wait(15e1)
	def get_storage_stats(A,force=_B):
		B=A.state[_F];C=time.time();G=not force and A._storage_stats_cache is not _A and A._storage_stats_cache_dir==B and C-A._storage_stats_cache_time<12.
		if G:return A._storage_stats_cache
		D=A.get_archive_snapshot(force=_D);H=round(sum(A[_T]for A in D)/1048576.,1)
		try:I,I,J=shutil.disk_usage(B);E=round(J/1073741824.,1)
		except Exception:E=-1.
		F=len(D),H,E;A._storage_stats_cache=F;A._storage_stats_cache_time=C;A._storage_stats_cache_dir=B;return F
	def get_archive_snapshot(A,force=_B):
		C=A.state[_F];E=time.time();G=not force and A._archive_snapshot_cache is not _A and A._archive_snapshot_cache_dir==C and E-A._archive_snapshot_cache_time<12.
		if G:return A._archive_snapshot_cache
		os.makedirs(C,exist_ok=_D);D=[]
		try:
			with os.scandir(C)as H:
				for B in H:
					if B.name.startswith('.')or not B.name.lower().endswith(_P):continue
					if B.is_file(follow_symlinks=_B):F=B.stat(follow_symlinks=_B);D.append({_U:B.path,'name':B.name,_T:F.st_size,_V:F.st_mtime})
		except Exception:0
		D.sort(key=lambda item:item[_V],reverse=_D);A._archive_snapshot_cache=D;A._archive_snapshot_cache_time=E;A._archive_snapshot_cache_dir=C;return D
	def _seed_op_history_from_disk(A):
		B=A.state.get(_F,'')
		if not B or not os.path.isdir(B):return
		try:
			C=[os.path.join(B,A)for A in os.listdir(B)if not A.startswith('.')and A.lower().endswith(_P)and os.path.isfile(os.path.join(B,A))];C.sort(key=os.path.getmtime,reverse=_D)
			for D in C[:25]:E=os.stat(D);F=datetime.fromtimestamp(E.st_mtime).strftime(_W);G=round(E.st_size/1048576.,1);A.op_history.append({_O:F,_L:_Q,_X:os.path.basename(D),_Y:G,_J:_A})
			if A.op_history:A.state[_I]=A.op_history
		except Exception:0
	def record_op_event(A,status_lbl,detail_txt,size_mb=_C,dur_sec=_A,started_at=_A,finished_at=_A):
		B=dur_sec;from datetime import datetime as C;from core.config import commit_state as F;D={_O:C.now().strftime(_W),_L:status_lbl,_X:detail_txt,_Y:round(float(size_mb),1),_J:round(float(B),1)if B is not _A else _A}
		for(G,E)in(('started_at',started_at),('finished_at',finished_at)):
			if E is not _A:D[G]=C.fromtimestamp(float(E)).astimezone().isoformat(timespec='seconds')
		if not hasattr(A,_I):A.op_history=list(A.state.get(_I)or[])
		A.op_history.insert(0,D);A.op_history=A.op_history[:25];A.state[_I]=A.op_history;A._storage_stats_cache_time=_C;A._last_backup_cache_time=_C;A._archive_snapshot_cache_time=_C;A.request_dest_stats_refresh()
		try:F(A.state)
		except Exception:0
	def get_last_backup_info(A,force=_B):
		N='Ще немає створених копій';F=force;from datetime import datetime as O;C=A.state.get(_F,'');G=time.time();P=not F and getattr(A,'_last_backup_cache',_A)is not _A and getattr(A,'_last_backup_cache_dir',_A)==C and getattr(A,'_last_backup_cache_lang',_A)==A.state.get(_E,_H)and G-getattr(A,'_last_backup_cache_time',_C)<12.
		if P:return A._last_backup_cache
		if not C or not os.path.isdir(C):B=N,_K
		else:
			try:
				H=A.get_archive_snapshot(force=F)
				if not H:B=N,_K
				else:
					D=H[0];I=O.fromtimestamp(D[_V]).strftime('%H:%M  (%d.%m.%Y)');J=round(D[_T]/1048576.,1);Q=os.path.exists(D[_U]+_b);R=os.path.basename(D[_U]);K=next((A.get(_J)for A in A.state.get(_I,[])if isinstance(A,dict)and A.get(_L)==_Q and A.get(_X)==R and A.get(_J)is not _A),_A);E=''
					if K is not _A:
						try:
							S=max(0,int(round(float(K))));L,M=divmod(S,60)
							if A.state.get(_E)=='uk':E=f"  •  Час створення: {L} хв {M:02d} с"
							else:E=f"  •  Creation time: {L} min {M:02d} sec"
						except(TypeError,ValueError,OverflowError):0
					if Q:B=f"{I}\n{J} МБ{E}  •  SHA-256 ✔",_G
					else:B=f"{I}\n{J} МБ{E}  •  Без .sha256",_N
			except Exception:B='Невідомо',_K
		A._last_backup_cache=B;A._last_backup_cache_time=G;A._last_backup_cache_dir=C;A._last_backup_cache_lang=A.state.get(_E,_H);return B
	def get_detailed_stats(B):
		y='%Y-%m';x='months';w='dur_cnt';v='total_dur_sec';u='avg_dur_sec';t='success_rate';s='avg_mb';r='sha_cnt';q='gfs_monthly';p='gfs_weekly';o='gfs_daily';e='span_days';X='all_time_mb';W='all_time_cnt';V='month_cnt';U='week_cnt';T='today_cnt';N='month_mb';M='week_mb';L='today_mb';D='total_cnt';C='total_mb';import time;from datetime import datetime as Y;O=B.state.get(_F,'');f=time.time();Z=Y.now();g=Z.replace(hour=0,minute=0,second=0,microsecond=0).timestamp();h=f-604800;i=f-2592000;A={T:0,L:_C,U:0,M:_C,V:0,N:_C,D:0,C:_C,o:0,p:0,q:0,r:0,s:_C,e:0,t:100,u:_C,v:_C,w:0,x:[]};P=[];a,Q=Z.year,Z.month
		for _ in range(6):
			P.append(f"{a:04d}-{Q:02d}");Q-=1
			if Q==0:Q,a=12,a-1
		P.reverse();G={A:0 for A in P};E=[]
		if O and os.path.isdir(O):
			try:
				for H in os.listdir(O):
					if H.startswith('.')or not H.lower().endswith(_P):continue
					b=os.path.join(O,H)
					if not os.path.isfile(b):continue
					j=os.stat(b);R,I=j.st_size/1048576.,j.st_mtime;E.append(I);A[D]+=1;A[C]+=R
					if I>=g:A[T]+=1;A[L]+=R
					if I>=h:A[U]+=1;A[M]+=R
					if I>=i:A[V]+=1;A[N]+=R
					if'_MONTHLY_'in H:A[q]+=1
					elif'_WEEKLY_'in H:A[p]+=1
					else:A[o]+=1
					if os.path.exists(b+_b):A[r]+=1
					k=Y.fromtimestamp(I).strftime(y)
					if k in G:G[k]+=1
			except Exception:0
		J=A[D];A['disk_cnt']=J;F=getattr(B,_I,[])or[]
		if J==0 and F:
			for c in F:
				if c.get(_L)!=_Q:continue
				d=float(c.get(_Y)or _C)
				try:
					l=Y.strptime(c.get(_O,''),_W);S=l.timestamp();E.append(S)
					if S>=g:A[T]+=1;A[L]+=d
					if S>=h:A[U]+=1;A[M]+=d
					if S>=i:A[V]+=1;A[N]+=d
					m=l.strftime(y)
					if m in G:G[m]+=1
				except Exception:0
		for n in(L,M,N,C):A[n]=round(A[n],1)
		z=int(B.state.get(W,0)or 0);A0=round(float(B.state.get(X,_C)or _C),1)
		if J>z:B.state[W]=J;B.state[X]=max(A0,A[C])
		A[D]=max(J,A[V],A[U],A[T],int(B.state.get(W,0)));A[C]=round(max(A[C],A[N],A[M],A[L],float(B.state.get(X,_C))),1);B.state[W]=A[D];B.state[X]=A[C]
		if A[D]>0:A[s]=round(A[C]/A[D],1)
		if len(E)>=2:A[e]=max(1,int((max(E)-min(E))//86400))
		elif len(E)==1:A[e]=1
		if F:
			A1=sum(1 for A in F if A.get(_L)==_Q);A[t]=int(round(A1/len(F)*100));K=[float(A[_J])for A in F if A.get(_J)is not _A and float(A[_J])>0]
			if K:A[w]=len(K);A[v]=round(sum(K),1);A[u]=round(sum(K)/len(K),1)
		A2={'01':'Січень','02':'Лютий','03':'Березень','04':'Квітень','05':'Травень','06':'Червень','07':'Липень','08':'Серпень','09':'Вересень','10':'Жовтень','11':'Листопад','12':'Грудень'};A3=B.state.get(_E,_H);A[x]=[(tr(A2.get(A[5:],A[5:]),A3),G[A])for A in P];return A
