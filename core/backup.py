# patch-id: bak-tarzst-file-count-3.42
# patch-id: bak-disable-net-copy-3.40
# patch-id: bak-force-tarzst-3.38
# patch-id: history-indeterminate-time-3.34
# patch-id: backup-32bit-pause5ms-and-log-fix-3.25
# patch-id: main-win-adapter-badge-3.02
# patch-id: net-scope-adapter-3.01-p2
# patch-id: backup-timeout-retry-3.00
# patch-id: fix-net-drive-status-and-build-retry-2.78
# patch-id: io-pause-buf128-2.18
# patch-id: stage-window-2.21
# patch-id: adaptive-status-poll-2.11
# patch-id: card-conn-copies-2.59
# patch-id: speed-journal-auto-target-2.62
# patch-id: tall-pbar-server-marquee-2.70
# patch-id: single-pass-verify-speed-2.75
# [ФАЙЛ: core/backup.py (v2.21 | 25.11.2026 18:05) — АВТОРИЗАЦИЯ, СКАЧИВАНИЕ ZIP, CRC32/SHA-256 В 1 ПРОХОД И ЗЕРКАЛО]
# patch-id: pcloud-speed-progress-gradient-2.33
_z='_last_srv_timings'
_y='HomeGridBackup_stage'
_x='copying'
_w='_KEEP_'
_v='net_fit_free_space'
_u='net_max_size_gb'
_t='net_max_archives'
_s='mirror_dir'
_r='mirror_enabled'
_q='job_id'
_p='<[^>]+>'
_o='editor_pin_required'
_n='HomeGrid Backup'
_m='network'
_l='download_buf_kb'
_k='cloud_save_archives'
_j='dl_t0'
_i='packing'
_h='preparing'
_g=('.zip','.tar.zst')
_f='stop'
_e='backup_dir'
_d='pcloud'
_c='checking'
_b='processing'
_a='{}'
_Z='dirty'
_Y='\\'
_X='error'
_W='.sha256'
_V='editor_pin'
_U='pin'
_T='net_enabled'
_S='en'
_R='lang'
_Q='login_pin'
_P='session_token'
_O='local_enabled'
_N='cloud_enabled'
_M='stage_started'
_L='POST'
_K='net_dir'
_J='stage_completed'
_I='err'
_H='info'
_G='status'
_F='ok'
_E='warn'
_D=None
_C=.0
_B=False
_A=True
import hashlib,http.cookiejar,json,os,re,shutil,sys,time,urllib.request,zipfile,zlib
_IS_32BIT=(sys.maxsize<=2**32)
from datetime import datetime
from urllib.parse import urlparse
from core.config import DEFAULT_TOK,NO_CLEAN,SCRIPT_VER,SILENT_MODE,commit_state,get_fast_sysinfo
from core.files import format_backup_dt,format_duration,pretty_phase
from core.network import BROWSER_UA,_seed_cookie,detect_network_adapter,invoke_http,normalize_server_url,scan_lan_servers,verify_host_and_hgm
def _record_cloud_event(engine,operation_id,event,**B):
	A=engine
	try:from core.cloud import record_operation_event as C;C(A,operation_id,event,**B)
	except Exception as D:A.log(f"Попередження: не вдалося записати локальний звіт: {D}",_E)
def _cloud_sync_warning(engine,prefix,exc):
	B=exc;A=engine;from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW as C;from core.cloud import CloudRateLimitError as D,cloud_sync_error_text as E
	if C and isinstance(B,D):A.log(E(B,A.state.get(_R,_S)),_E)
	else:A.log(f"{prefix}{B}",_E)
def _sync_cloud_reports(engine):
	J='auto';A=engine;E=A.state;F=E.get('journal_sync_target')or J;B=bool(E.get(_N));I=os.path.expanduser((E.get(_K)or'').strip());G=bool(I and os.path.isdir(I))
	if F==J:C=B;D=not B and G
	elif F==_d:C,D=B,_B
	elif F==_m:C,D=_B,G
	else:C,D=B,G
	if C:
		try:from core.cloud import sync_cloud_reports as K;K(A)
		except Exception as H:
			_cloud_sync_warning(A,'Попередження: не вдалося передати хмарний звіт: ',H);from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW as L
			if L:from core.cloud import start_cloud_sync_worker as M;M(A)
	if D:
		try:from core.cloud import sync_network_shared_journal as N;N(A)
		except Exception as H:A.log(f"Попередження: не вдалося оновити мережевий журнал швидкості: {H}",_E)
def _sync_cloud_backups(engine,prune=_B,progress_cb=_D):
	A=engine
	if not A.state.get(_N):return _B
	try:from core.cloud import sync_cloud_backups as B;return B(A,prune=prune,progress_cb=progress_cb)is not _B
	except Exception as C:
		_cloud_sync_warning(A,'Попередження: не вдалося синхронізувати хмарні архіви: ',C);from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW as D
		if D:from core.cloud import start_cloud_sync_worker as E;E(A)
		return _B
def _desktop_notify(title,text):
	F='\\"';E='\\\\';D='notify-send';C=text;B=title;import subprocess as A,sys
	try:
		if sys.platform.startswith('linux'):
			if(os.environ.get('DISPLAY')or os.environ.get('WAYLAND_DISPLAY'))and shutil.which(D):A.Popen([D,'-a',_n,B,C],stdin=A.DEVNULL,stdout=A.DEVNULL,stderr=A.DEVNULL)
		elif sys.platform=='darwin':G=str(B).replace(_Y,E).replace('"',F);H=str(C).replace(_Y,E).replace('"',F);A.Popen(['osascript','-e',f'display notification "{H}" with title "{G}"'],stdin=A.DEVNULL,stdout=A.DEVNULL,stderr=A.DEVNULL)
		elif os.name=='nt':I=str(B).replace("'","''");J=str(C).replace("'","''");K=f"Add-Type -AssemblyName System.Windows.Forms;$n=New-Object System.Windows.Forms.NotifyIcon;$n.Icon=[System.Drawing.SystemIcons]::Information;$n.Visible=$true;$n.ShowBalloonTip(5000,'{I}','{J}',[System.Windows.Forms.ToolTipIcon]::Info);Start-Sleep -Seconds 6;$n.Dispose()";A.Popen(['powershell','-NoProfile','-WindowStyle','Hidden','-Command',K],stdin=A.DEVNULL,stdout=A.DEVNULL,stderr=A.DEVNULL,creationflags=134217728)
	except Exception:0
def _is_slow_or_cloud_path(path_str):
	C=path_str
	if not C:return _B
	B=os.path.normpath(os.path.expanduser(str(C)));D=B.lower().replace(chr(92),'/')
	if B.startswith(chr(92)*2)or D.startswith('//'):return _A
	I='/library/cloudstorage/','/library/mobile documents/','googledrive','google-drive','/run/user/','google drive','onedrive','dropbox','icloud',_d,'nextcloud','owncloud','yandexdisk','/gvfs/','/volumes/','/mnt/','/media/'
	if any(A in D for A in I):return _A
	if os.name=='nt':
		try:
			import ctypes as A;E=os.path.splitdrive(B)
			if E:
				F=E+chr(92)
				if A.windll.kernel32.GetDriveTypeW(F)==4:return _A
				G=A.create_unicode_buffer(64);H=A.create_unicode_buffer(256)
				if A.windll.kernel32.GetVolumeInformationW(F,H,256,_D,_D,_D,G,64):
					J=G.value.lower();K=H.value.lower()
					if any(A in J or A in K for A in('dokan','winfsp','fuse',_d,'google','mega','raidrive','webdav')):return _A
		except Exception:0
	return _B
def _backup_stage1_prepare(engine,raw_url,force_skip):
	Z='"ok"\\s*:\\s*false';O=raw_url;N='server';A=engine;P=bool(A.state.get(_O,_A));Q=os.path.expanduser((A.state.get(_K)or'').strip());a=bool(A.state.get(_T,_B))and bool(Q)
	if not P and not a:raise RuntimeError('Увімкніть хоча б одне сховище (Локально або Мережа).')
	b=A.state[_e]if P else Q;os.makedirs(b,exist_ok=_A);C,c=normalize_server_url(O if O is not _D else A.state[N]);d=force_skip or c
	if not C:
		A.log('Адресу не вказано. Запуск автопошуку в LAN...',_H);R=scan_lan_servers(A)
		if not R:raise RuntimeError('Сервери HomeGrid Monitor у мережі не знайдено.')
		e,B,B=next(iter(R));C=f"http://{e}:18899";A.log(f"Автоматично обрано сервер: {C}",_F)
	H=urlparse(C);E=H.hostname or C;F=H.port or(443 if H.scheme=='https'else 80)
	if d:A.log(f"Перевірку сайту/порту пропущено для {E}:{F}.",_E)
	else:
		A.set_progress(5,'Перевірка сайту та сервера HGM...');f,B,g,S,T=verify_host_and_hgm(A,C)
		if not f:A.diag_net=f"{E}:{F} (ОФЛАЙН)";raise RuntimeError(g)
		A.diag_net=f"{E}:{F} (ОНЛАЙН)";A.diag_ping=f"TCP {S} мс | API {T} мс";A.diag_adapter=detect_network_adapter(A.state.get('server','')).get('label','');A.log(f"Сервер HGM онлайн (TCP: {S} мс, API: {T} мс)",_F)
	if C!=A.state[N]:A.state[N]=C;A.state[_Z]=_A
	A.set_progress(12,'Перевірка сесії та авторизація...');I=A.state[_P]==''
	if not I:
		h=int(time.time()*1000);B,B,i,B,B,B=invoke_http(f"{C}/api/auth/status?_t={h}",A.state)
		if not re.search('"authenticated"\\s*:\\s*true',i):I=_A;A.state[_P]='';A.log('Збережена сесія застаріла. Повторний вхід...',_E)
	if I:
		while _A:
			J=A.state[_Q]or A.ask_modal(_U,'Авторизація HomeGrid','Введіть LOGIN PIN:')
			if not J:raise RuntimeError('Вхід скасовано (не введено LOGIN PIN).')
			B,B,K,U,j,B=invoke_http(f"{C}/api/auth/login",A.state,_L,json.dumps({_U:J}),C,f"{C}/login",1e1,send_ses=_B)
			if not K:raise RuntimeError(f"Мережева помилка під час входу: {j}")
			if re.search(Z,K):
				A.log('Невірний LOGIN PIN!',_I);A.state[_Q]=''
				if SILENT_MODE:raise RuntimeError('Збережений LOGIN PIN відхилено сервером.')
				continue
			A.state[_Q]=J;A.state[_Z]=_A
			if U:A.state[_P]=U;A.log('Авторизація успішна!',_F);break
			if re.search('"ok"\\s*:\\s*true',K):A.log('Авторизацію підтверджено сервером!',_F);break
			raise RuntimeError('Сервер не повернув cookie сесії.')
	else:A.log('Активну сесію підтверджено.',_F)
	A.set_progress(20,'Запит на підготовку бекапу...');fmt_q='tar.zst';B,L,D,B,V,B=invoke_http(f"{C}/api/migration/export/prepare?format={fmt_q}",A.state,_L,json.dumps({'format':fmt_q}),timeout=15.);M=_B
	while D and _o in D:
		if A.state[_V]:G=A.state[_V]
		elif not M and A.state[_Q]:G=A.state[_Q];M=_A
		else:
			G=A.ask_modal(_U,'Права редактора','Для експорту потрібен EDITOR PIN:')
			if not G:raise RuntimeError('Експорт скасовано (не введено EDITOR PIN).')
		B,B,W,X,k,B=invoke_http(f"{C}/api/auth/editor/unlock",A.state,_L,json.dumps({_U:G}),C,f"{C}/service.html",1e1)
		if not W:raise RuntimeError(f"Помилка розблокування редактора: {k}")
		if re.search(Z,W):
			A.state[_V]=''
			if SILENT_MODE and not M:raise RuntimeError('Збережений EDITOR PIN відхилено.')
			continue
		A.state[_V]=G;A.state[_Z]=_A
		if X:A.state[_P]=X
		fmt_q='tar.zst';B,L,D,B,V,B=invoke_http(f"{C}/api/migration/export/prepare?format={fmt_q}",A.state,_L,json.dumps({'format':fmt_q}),timeout=15.)
	if not D or not D.strip():raise RuntimeError(f"Помилка підготовки (порожня відповідь сервера, HTTP {L}): {V}")
	try:l=json.loads(D)
	except Exception:m=re.sub('\\s+',' ',re.sub(_p,' ',D)).strip()[:120];raise RuntimeError(f"Сервер повернув некоректну відповідь замість JSON (HTTP {L}): {m or'порожньо'}")
	Y=l.get(_q)
	if not Y:raise RuntimeError(f"Сервер не створив завдання експорту: {D[:160]}")
	n=f"{E}:{F}"if F not in(80,443)else E;return C,n,Y
VERIFY_PAUSE_LITE=.005
class _HashingReader:
	def __init__(A,raw_file):A._f=raw_file;A.hasher=hashlib.sha256();A.hashed_pos=0
	def read(A,size=-1):
		C=A._f.tell();B=A._f.read(size)
		if not B:return B
		D=C+len(B)
		if C==A.hashed_pos:A.hasher.update(B);A.hashed_pos=D
		elif C<A.hashed_pos<D:A.hasher.update(B[A.hashed_pos-C:]);A.hashed_pos=D
		return B
	def seek(A,offset,whence=0):return A._f.seek(offset,whence)
	def tell(A):return A._f.tell()
	def seekable(A):return A._f.seekable()
	def readable(A):return _A
	@property
	def closed(self):return getattr(self._f,'closed',_B)
	def finalize_tail(A,buf_size=1048576):
		A._f.seek(A.hashed_pos)
		while _A:
			B=A._f.read(buf_size)
			if not B:break
			A.hasher.update(B);A.hashed_pos+=len(B)
def verify_single_archive(zip_path,progress_callback=_D,overall_start=0,overall_total=0,buf_size=1048576,cancel_flag=_D,io_pause=_C):
	T=io_pause;S=cancel_flag;R=overall_total;Q=progress_callback;D=zip_path;C='detail';B='name';A=os.path.basename(D)
	if not os.path.isfile(D):return{B:A,_G:_I,C:'Файл не знайдено'}
	U=D+_W;E=os.path.exists(U);G=''
	if E:
		try:
			with open(U,'r',encoding='utf-8')as X:G=next(iter(X.read().split()),'').strip().lower()
		except Exception as H:return{B:A,_G:_I,C:f"Помилка читання .sha256: {H}"}
	I=0;J=0;K=_C;L=max(4096,int(buf_size));Y='CRC32 + SHA-256'if E else'CRC32'
	def Z():
		nonlocal K
		if not Q:return
		B=time.time()
		if B-K<.15:return
		K=B;C=int(min(99,(overall_start+I)*1e2/R))if R else 0;Q(C,f"{Y} {I/1048576.:.1f} МБ: {A}")
	try:
		with open(D,'rb',buffering=max(1048576,L))as a:
			M=_HashingReader(a)
			with zipfile.ZipFile(M,'r')as V:
				W=V.infolist();N=len(W)
				if N<1:return{B:A,_G:_I,C:'Порожній ZIP-архів'}
				for O in W:
					P=0
					with V.open(O,'r')as b:
						while _A:
							if S and S.get(_f):return{B:A,_G:_E,C:'Перевірку перервано'}
							F=b.read(L)
							if not F:break
							P=zlib.crc32(F,P);I+=len(F);J+=len(F)
							if T and J>=4194304:J=0;time.sleep(T)
							Z()
					if P&4294967295!=O.CRC:return{B:A,_G:_I,C:f"Пошкоджений CRC32 у файлі: {O.filename}"}
			if E:M.finalize_tail(max(1048576,L))
	except Exception as H:return{B:A,_G:_I,C:f"Помилка перевірки архіву: {H}"}
	if not E:return{B:A,_G:_E,C:f"ZIP OK ({N} файлів), але файл .sha256 відсутній"}
	if M.hasher.hexdigest().lower()==G and G:return{B:A,_G:_F,C:f"Цілісність 100% підтверджена ({N} файлів)"}
	return{B:A,_G:_I,C:'УВАГА! Контрольна сума SHA-256 не збігається'}
def verify_all_archives(state,progress_callback=_D,buf_size=1048576,cancel_flag=_D):
	G=state;D=progress_callback;B=cancel_flag;S=time.time();T=VERIFY_PAUSE_LITE if(G.get('lite_mode')or _IS_32BIT)else _C;buf_size=min(int(buf_size),262144)if _IS_32BIT else buf_size;E=G[_e];os.makedirs(E,exist_ok=_A);C=[]
	for H in os.listdir(E):
		if H.lower().endswith(_g):
			I=os.path.join(E,H)
			try:J=os.stat(I);C.append((I,J.st_size,J.st_mtime))
			except OSError:0
	C.sort(key=lambda x:x[2],reverse=_A);K=[A[0]for A in C];L=[A[1]for A in C];M=[A*2 for A in L];N,F,A=sum(M),0,[]
	for(O,P)in enumerate(K,1):
		if B and B.get(_f):break
		if D:D(int(F*100/max(1,N)),f"Архів {O}/{len(K)}: {os.path.basename(P)}")
		A.append(verify_single_archive(P,D,F,N,buf_size=buf_size,cancel_flag=B,io_pause=T));F+=M[O-1]
	Q=max(.001,time.time()-S);R=sum(L)/1048576.;U=R/Q;return{'total':len(A),'ok_cnt':sum(1 for A in A if A[_G]==_F),'warn_cnt':sum(1 for A in A if A[_G]==_E),'err_cnt':sum(1 for A in A if A[_G]==_I),'elapsed':round(Q,2),'speed_mbs':round(U,1),'total_mb':round(R,1),'cancelled':bool(B and B.get(_f)),'items':A}
def _copy_to_mirror(engine,out_file,sha_file):
	F=sha_file;D=out_file;B=engine
	if not bool(B.state.get(_r,_B)):return
	E=(B.state.get(_s)or'').strip()
	if not E or E in('.','./','.\\','/',_Y):return
	try:
		P=os.path.normcase(os.path.realpath(os.path.dirname(D)));A=os.path.normcase(os.path.realpath(os.path.expanduser(E)))
		if P==A:return
		os.makedirs(A,exist_ok=_A);G=B.state;Q=os.path.getsize(D)+67108864;J=max(0,int(G.get(_t,0)or 0));K=int(max(_C,float(G.get(_u,_C)or _C))*1024**3);R=bool(G.get(_v,_A));C=[]
		for H in os.listdir(A):
			if H.lower().endswith(_g)and _w not in H.upper():
				L=os.path.join(A,H)
				try:M=os.stat(L);C.append([L,M.st_size,M.st_mtime])
				except OSError:0
		C.sort(key=lambda x:x);I=0
		while C:
			S=shutil.disk_usage(A).free;T=sum(A for A in C)+os.path.getsize(D);U=R and S<Q or J>0 and len(C)+1>J or K>0 and T>K
			if not U:break
			N,V,V=C.pop(0)
			for O in(N,N+_W):
				try:
					if os.path.exists(O):os.remove(O)
				except OSError:0
			I+=1
		if I:B.log(f"Network rotation: removed {I} oldest archive(s).",_H)
		shutil.copy2(D,os.path.join(A,os.path.basename(D)))
		if os.path.exists(F):shutil.copy2(F,os.path.join(A,os.path.basename(F)))
		B.log(f"Дзеркальну копію збережено у: {A}",_F)
	except Exception as W:B.log(f"Попередження: не вдалося скопіювати у дзеркальну папку ({E}): {W}",_E)
def _copy_to_network(engine,out_file,sha_file):
	F=sha_file;C=out_file;B=engine
	if not bool(B.state.get(_T,_B)):return
	E=(B.state.get(_K)or'').strip()
	if not E or E in('.','./','.\\','/',_Y):return
	try:
		from operator import itemgetter as O;P=os.path.normcase(os.path.realpath(os.path.dirname(C)));A=os.path.normcase(os.path.realpath(os.path.expanduser(E)))
		if P==A:return
		os.makedirs(A,exist_ok=_A);Q=os.path.basename(C);I=os.path.getsize(C)/1048576.;B.set_progress(96,f"Копіювання у мережу ({I:.1f} МБ)...");B.log(f"Копіювання архіву у мережеву папку: {A}...",_H);G=B.state;R=os.path.getsize(C)+67108864;J=max(0,int(G.get(_t,0)or 0));K=int(max(_C,float(G.get(_u,_C)or _C))*1024**3);S=bool(G.get(_v,_A));D=[(os.path.join(A,B),os.path.getsize(os.path.join(A,B)),os.path.getmtime(os.path.join(A,B)))for B in os.listdir(A)if B.lower().endswith(_g)and _w not in B.upper()];D.sort(key=O(2));H=0
		while D and(S and shutil.disk_usage(A).free<R or J>0 and len(D)+1>J or K>0 and sum(B for(A,B,A)in D)+os.path.getsize(C)>K):
			L,T,T=D.pop(0)
			for M in(L,L+_W):
				if os.path.exists(M):os.remove(M)
			H+=1
		if H:B.log(f"Ротація мережі: видалено {H} старих архівів.",_H)
		U=time.time();shutil.copy2(C,os.path.join(A,Q))
		if os.path.exists(F):shutil.copy2(F,os.path.join(A,os.path.basename(F)))
		N=round(max(.1,time.time()-U),1);V=round(I/N,1);B.log(f"Мережеву копію збережено у: {A} ({N} с, {V} МБ/с)",_F)
	except Exception as W:B.log(f"Попередження: не вдалося скопіювати у мережеву папку ({E}): {W}",_E)
def _download_backup_zip(engine,srv,srv_label,job_id,bdir,operation_id):
	AQ='archive_download';AP='download_url';u='timeout';a=bdir;Z=job_id;S=operation_id;R='ready';I=srv;C=srv_label;A=engine;A.log(f"Збірка архіву на сервері {C}...",_H);E='';b=time.time();T={'db':_C,_h:_C,_x:_C,'history':_C,_b:_C,_i:_C,_c:_C};H=0;U=0;J=0;v=1.5
	_pk=0
	while _A:
		time.sleep(v);B,h,c,B,w,B=invoke_http(f"{I}/api/migration/export/status?job_id={Z}",A.state,timeout=45.)
		if not c or not c.strip():
			J+=1
			if J in(1,5,15,30):A.log(f"Втрачено зв'язок із {C} під час збірки (HTTP {h}: {w}). Повтор {J}/45...",_E)
			A.set_progress(_D,f"[{C}] Очікування мережі ({J}/45)...")
			if J>=45:raise RuntimeError(f"Сервер {C} перестав відповідати під час збірки (HTTP {h}): {w}")
			time.sleep(2.5);continue
		try:D=json.loads(c);J=0
		except Exception:
			J+=1
			if J>=15:AR=re.sub('\\s+',' ',re.sub(_p,' ',c)).strip()[:100];raise RuntimeError(f"Сайт {C} повернув HTML замість статусу JSON (HTTP {h}): {AR}")
			time.sleep(.8);continue
		if D.get(_F)is _B:
			d=D.get(_X)or'невідома помилка сервера'
			if d in('backup_job_not_found',u)and U<4:
				U+=1;x=(15 if d==u else 4)*U;AS='Час збірки на сервері вичерпано'if d==u else'Сервер скинув завдання';A.log(f"{AS} ({C}). Повтор {U}/4 через {x} с...",_E)
				for i in range(x,0,-1):A.set_progress(22,f"[{C}] Перезапуск збірки ({U}/4) через {i} с...");time.sleep(1.)
				fmt_q='tar.zst';B,B,K,B,y,B=invoke_http(f"{I}/api/migration/export/prepare?format={fmt_q}",A.state,_L,json.dumps({'format':fmt_q}),timeout=2e1)
				if K and _o in K:
					z=A.state.get(_V)or A.state.get(_Q)or''
					if z:
						B,B,B,A0,B,B=invoke_http(f"{I}/api/auth/editor/unlock",A.state,_L,json.dumps({_U:z}),I,f"{I}/service.html",1e1)
						if A0:A.state[_P]=A0
						fmt_q='tar.zst';B,B,K,B,y,B=invoke_http(f"{I}/api/migration/export/prepare?format={fmt_q}",A.state,_L,json.dumps({'format':fmt_q}),timeout=2e1)
				if not K or not K.strip():raise RuntimeError(f"Помилка повторної підготовки: {y}")
				try:Z=json.loads(K).get(_q)
				except Exception:raise RuntimeError('Сервер повернув некоректну відповідь під час повторного запуску.')
				if not Z:raise RuntimeError(f"Сервер не створив нове завдання експорту: {K[:140]}")
				E='';continue
			raise RuntimeError(f"Сервер {C} перервав збірку архіву: {d}")
		A1=int(D.get('progress',0));F=D.get('phase')or'working';v=1.5 if F in(_h,R)else 4. if F in(_c,_i)else 2.5;H=D.get('total_bytes',0)or 0;j=D.get('processed_bytes',0)or 0;_pk=max(_pk,H,j)
		if F!=E:
			if E:V=max(_C,time.time()-b);T['db'if('db'in str(E).lower()or'connect'in str(E).lower())else'history'if('history'in str(E).lower()or'device'in str(E).lower())else(E if E in T else _b)]+=V;_record_cloud_event(A,S,_J,stage=f"server_{E}",duration_sec=V)
			E=F;b=time.time();_record_cloud_event(A,S,_M,stage=f"server_{F}");A.log(f"Етап сервера ({C}): {pretty_phase(F)}",_H)
		W=max(.05,time.time()-b)
		if H>0:A2=j/1048576./W if j>0 and W>.25 else _C;AT=f", {A2:.1f} МБ/с"if A2>.05 else'';A3=f" ({j/1048576:.1f}/{H/1048576:.1f} МБ{AT})"
		else:A3=''
		A4=A.state.get(_R,_S);A5=f"{W:.1f} {'с'if A4=='uk'else's'}"if W<60 else format_duration(W,A4).partition(' (').__getitem__(0)
		if F==_c or'history'in str(F).lower()or'device'in str(F).lower():A.set_progress(_D,f"[{C}] {pretty_phase(F)} ({A5})...")
		elif F!=R and D.get(R)is not _A:AU=f": {A1}%"if A1>0 else f" ({A5})";A.set_progress(_D,f"[{C}] {pretty_phase(F)}{AU}{A3}")
		if F==R or D.get(R)is _A:
			if E and E!=R:V=max(_C,time.time()-b);T['db'if('db'in str(E).lower()or'connect'in str(E).lower())else'history'if('history'in str(E).lower()or'device'in str(E).lower())else(E if E in T else _b)]+=V;_record_cloud_event(A,S,_J,stage=f"server_{E}",duration_sec=V)
			A._last_srv_timings={A:round(B,1)for(A,B)in T.items()};A._last_srv_timings[_j]=time.time();A._last_srv_timings['raw_mb']=round(_pk/1048576.,2)if _pk>0 else _C;A6=45 if A.state.get(_N)and A.state.get(_k,_A)else 75;A.set_progress(A6,f"[{C}] Архів готовий ({A6}%). Завантаження...");break
		if D.get(_G)==_X or F==_X:raise RuntimeError(f"Сервер {C} повідомив про помилку під час створення архіву!")
	A7=format_backup_dt(datetime.now());_ext='.tar.zst';M=os.path.join(a,f"homegrid_backup_DAILY_{A7}{_ext}");A8=1
	while os.path.exists(M):M=os.path.join(a,f"homegrid_backup_DAILY_{A7}_{A8}{_ext}");A8+=1
	import tempfile as AV;A9=_B;k=a;AA=not bool(A.state.get(_O,_A))and bool(A.state.get(_T))and bool((A.state.get(_K)or'').strip())
	if _is_slow_or_cloud_path(a)or AA:
		l=AV.gettempdir()
		try:AB=shutil.disk_usage(l).free
		except OSError:AB=0
		AW=int(H*1.25)+104857600 if H>0 else 536870912
		if not _is_slow_or_cloud_path(l)and AB>=AW:k=os.path.join(l,_y);os.makedirs(k,exist_ok=_A);A9=_A;A.log('Спершу завантажу та перевірю у тимчасову локальну папку, а потім перенесу у папку призначення.',_E);AX='увімкнено тільки мережеву папку'if AA else'папка знаходиться у хмарному або мережевому сховищі';A.log(f"Режим ({AX}): спершу завантажу та перевірю у тимчасовій папці на SSD, а потім перенесу в папку призначення.",_E)
	m=os.path.join(k,os.path.basename(M))if A9 else M;G=m+'.part';AC=A.state['client_token']or DEFAULT_TOK;AY=A.state[_P];AZ=D.get('download_token')or AC;n=f"{I}{D[AP]}"if D.get(AP)else f"{I}/api/migration/export?_t={int(time.time()*1000)}&job_id={Z}&_download_token={AZ}";from core.network import set_socket_buffer_kb as Aa;Aa(A.state.get(_l,0));A.log(f"Завантаження ZIP-архіву з {C}...",_H);Al=time.time();_record_cloud_event(A,S,_M,stage=AQ);o=float(H)if H>0 else _C;N=7;AD=10,15,20,25,25,25
	for O in range(1,N+1):
		if os.path.exists(G):os.remove(G)
		p=time.time();P=_B;X='';e=_D
		for Ab in(_A,_B):
			try:
				q=A.state.get('_jar')or http.cookiejar.CookieJar();_seed_cookie(q,n,'hg_client',AC);_seed_cookie(q,n,'homegrid_dash_session',AY);AE=[urllib.request.HTTPCookieProcessor(q)]
				if Ab:AE.append(urllib.request.ProxyHandler({}))
				Ac=urllib.request.build_opener(*AE);Ad=urllib.request.Request(n,headers={'User-Agent':BROWSER_UA,'Accept-Encoding':'identity'})
				with Ac.open(Ad,timeout=300)as AF,open(G,'wb',buffering=1048576)as Ae:
					r=(AF.headers.get('X-Checksum-Sha256')or D.get('sha256')or'').strip().lower();e=hashlib.sha256();Y=0;AG=time.time();AH=p;AI=0;Q=_D;Af=max(16384,int(A.state.get(_l,64)or 64)*1024)
					while _A:
						f=AF.read(Af)
						if not f:break
						Ae.write(f);e.update(f);Y+=len(f);g=time.time()
						if g-AG>=1.:
							AG=g;AJ=Y/1048576.;Ag=max(.001,g-AH);AK=(Y-AI)/1048576./Ag;Q=AK if Q is _D else .35*AK+.65*Q;AH=g;AI=Y;AL=f"{Q:.2f} МБ/с"if Q>=1. else f"{Q*1024:.0f} КБ/с";AM=f" [спроба {O}/{N}]"if O>1 else''
							if o>0:Ah=min(99,int(Y/o*100));Ai,Aj=(45,20)if A.state.get(_N)and A.state.get(_k,_A)else(75,17);A.set_progress(Ai+int(Ah*(Aj/1e2)),f"Завантаження{AM}: {AJ:.1f}/{o/1048576.:.1f} МБ | Швидкість: {AL}")
							else:A.set_progress(83,f"Завантаження{AM}: {AJ:.1f} МБ | Швидкість: {AL}")
				P=_A;break
			except Exception as Ak:
				X=str(Ak)
				if os.path.exists(G):os.remove(G)
		L=os.path.getsize(G)if os.path.exists(G)else 0;s=L>=int(H*.99)if H>0 else L>=1024;AN=e.hexdigest().lower()if P and e is not _D else''
		if P and s and r and len(r)==64 and AN!=r:
			P=_B;X='SHA-256 не збігається з контрольним хешем сервера'
			if os.path.exists(G):os.remove(G)
		if P and s:
			os.replace(G,m);t=max(.05,time.time()-p)
			if hasattr(A,_z):A._last_srv_timings[_j]=p
			A.log(f"Архів завантажено: {L/1048576.:.2f} МБ за {round(t,1)} с",_F);_record_cloud_event(A,S,_J,stage=AQ,archive=M,size_mb=L/1048576.,size_bytes=L,duration_sec=t,speed_mbps=L/1048576./max(t,.001));return m,M,AN
		if P and not s:
			X=f"завантажено лише {L/1048576.:.1f} із {H/1048576.:.1f} МБ (обрив потоку)"
			if os.path.exists(G):os.remove(G)
		if O<N:
			AO=AD[min(O-1,len(AD)-1)];A.log(f"Збій завантаження ({X}). Повтор {O+1}/{N} через {AO} с...",_E)
			for i in range(AO,0,-1):A.set_progress(75,f"Очікування мережі: повтор {O+1}/{N} через {i} с...");time.sleep(1.)
		else:raise RuntimeError(f"Помилка завантаження після {N} спроб: {X}")
def run_backup_task(engine,raw_url=_D,force_skip=_B,skip_cleanup=_B,auto_quiet=_B):
	AI='record_op_event';AH='all_time_mb';AG='gfs_rotation';AF='local_mirror';AE='archive_sha256_verification';AD='archive_crc32_verification';AC='server_connection_and_preparation';AB='%H:%M:%S';h=auto_quiet;g='success';f='all_time_cnt';A=engine
	with A.lock:
		if A.is_running:return
		A.is_running=_A
	A.set_pill('Резервне копіювання...','work');F=time.time();i=datetime.now().strftime(AB);from core.cloud import new_operation_id as AJ;C=AJ();B='';D=_C;_record_cloud_event(A,C,'started',stage='server_connection',archive_sequence=max(0,int(A.state.get(f,0)))+1)
	try:
		L=_A;R=_B;A.state[_O]=_A;A.state[_T]=_B
		if not L and not R:raise RuntimeError('No storage enabled (Local and Network are both OFF).')
		AK=bool(A.state.get(_O,_A));j=A.state[_e]if AK else os.path.expanduser((A.state.get(_K)or'').strip())if L else __import__('tempfile').gettempdir();AL=([f"Local: {j}"]if L else[])+([f"Network: {A.state.get(_K)}"]if R else[]);A.log('Targets: '+' | '.join(AL),_H)
		if L and R:A.log('Режим 2 сховищ: 1) завантаження локально → 2) копіювання у мережу.',_H)
		AM=time.time();_record_cloud_event(A,C,_M,stage=AC);k,AN,AO=_backup_stage1_prepare(A,raw_url,force_skip);_record_cloud_event(A,C,_J,stage=AC,duration_sec=time.time()-AM,result=g);AP=time.time();_record_cloud_event(A,C,'milestone',stage='server_job_ready');AQ,H,l=_download_backup_zip(A,k,AN,AO,j,C);B=AQ;S=time.time();M=os.path.getsize(B);D=M/1048576.;_record_cloud_event(A,C,_M,stage=AD,archive=B);_record_cloud_event(A,C,_M,stage=AE,archive=B);m,AR=(66,5)if A.state.get(_N)and A.state.get(_k,_A)else(92,5);A.set_progress(m,f"Перевірка CRC32 + SHA-256: 0.0 / {D:.1f} МБ");AS=0;n=time.time()
		_vbuf=262144 if _IS_32BIT else 1048576
		with open(B,'rb',buffering=_vbuf)as AT:
			K=_HashingReader(AT)
			if B.lower().endswith('.tar.zst'):
				G=1
				try:
					import zstandard as _zst,tarfile as _tf
					_fc=0
					with _zst.ZstdDecompressor().stream_reader(K)as _zr,_tf.open(fileobj=_zr,mode='r|')as _tar:
						for _m in _tar:
							if _m.isfile():
								_fc+=1;_fo=_tar.extractfile(_m)
								if _fo:
									while _fo.read(_vbuf):0
					G=max(1,_fc)
				except ImportError:
					while K.read(_vbuf):0
				s=time.time();K.finalize_tail(_vbuf)
			else:
				with zipfile.ZipFile(K,'r')as o:
					p=o.infolist();G=len(p)
					if G<1:os.remove(B);raise RuntimeError('ZIP-архів порожній!')
					for T in p:
						U=0
						with o.open(T,'r')as AU:
							for q in iter(lambda:AU.read(_vbuf),b''):
								U=zlib.crc32(q,U);AS+=len(q);r=time.time()
								if r-n>=.5:n=r;AV=m+int(min(1.,K.hashed_pos/max(1,M))*AR);A.set_progress(AV,f"Перевірка CRC32 + SHA-256: {K.hashed_pos/1048576.:.1f} / {D:.1f} МБ")
						if U&4294967295!=T.CRC:os.remove(B);raise RuntimeError(f"Пошкоджений файл в архіві: {T.filename}")
				s=time.time();K.finalize_tail(_vbuf)
		t=time.time();u=max(.001,s-S);v=max(.001,t-s);w=round(max(.1,u),1);x=round(max(.1,v),1);AW=round(max(.1,t-S),1);_record_cloud_event(A,C,_J,stage=AD,archive=B,duration_sec=u,files_count=G);y=K.hasher.hexdigest().lower()
		if l and y!=l:os.remove(B);raise RuntimeError('Помилка запису на диск: SHA-256 файлу на носії не збігається зі завантаженим потоком!')
		AX=y.upper();E=B+_W
		with open(E,'w',encoding='utf-8')as AY:AY.write(f"{AX.lower()}  {os.path.basename(H)}\n")
		if os.path.normcase(os.path.realpath(B))!=os.path.normcase(os.path.realpath(H)):
			A.set_progress(97,'Перенесення перевіреного архіву у папку призначення...');os.makedirs(os.path.dirname(H),exist_ok=_A);z=H+_W;shutil.move(B,H)
			if os.path.exists(E):shutil.move(E,z)
			B=H;E=z;A.log(f"Архів та .sha256 перенесено у папку призначення: {os.path.dirname(B)}",_F)
		A.log(f"Цілісність перевірено в 1 прохід ({G} файлів) за {AW} с. Збережено {os.path.basename(E)}",_F);_record_cloud_event(A,C,_J,stage=AE,archive=B,size_mb=D,duration_sec=v,files_count=G,size_bytes=M);V=bool(A.state.get(_r,_B))and bool((A.state.get(_s)or'').strip());W=_C
		if V:AZ=time.time();_record_cloud_event(A,C,_M,stage=AF,archive=B);_copy_to_mirror(A,B,E);A0=max(.001,time.time()-AZ);W=round(max(.1,A0),1);_record_cloud_event(A,C,_J,stage=AF,archive=B,duration_sec=A0)
		A1=_B;Aa=time.time()
		Ab=round(max(.1,time.time()-Aa),1)if A1 else _C
		with A.lock:
			if hasattr(A,'_dest_stats'):A._dest_stats[_m]=_D
		if hasattr(A,'request_dest_stats_refresh'):A.request_dest_stats_refresh()
		if not bool(A.state.get(_O,_A)):
			for X in(B,E):
				try:
					if X and os.path.exists(X):os.remove(X)
				except OSError:0
			A.log('Temp local archive removed (Local storage is OFF).',_H)
		if A.state[_Z]:commit_state(A.state);A.log('Налаштування та ключі захищено збережено.',_F)
		from core.gfs import apply_gfs_cleanup as Ac,compute_gfs_plan as Ad;A.set_progress(98,'Ротація бекапів за обраною стратегією...');Ae=time.time();_record_cloud_event(A,C,_M,stage=AG,archive=B);Y,Y,A2=Ad(A.state);A3=len(A2);A4=_B
		if not skip_cleanup and not NO_CLEAN and(h or bool(A.state.get('silent_cleanup',_B))):Af,Y,Y=Ac(A,skip_prompt=_A,sync_cloud=_B);A4=Af==len(A2)
		_record_cloud_event(A,C,_J,stage=AG,archive=B,duration_sec=time.time()-Ae);Ag=time.time()
		def Ah(cpct,cinfo):B=73+int((cpct or 0)/1e2*26);A.set_progress(min(99,B),f"pCloud: {cinfo}")
		Ai=_sync_cloud_backups(A,prune=A4,progress_cb=Ah);_record_cloud_event(A,C,_J,stage='cloud_archive_sync',archive=B,duration_sec=time.time()-Ag,result=g if Ai else'disabled'if not A.state.get(_N)else'failed');N=time.time();A5=datetime.now().strftime(AB);I=getattr(A,_z,{});Aj=I.get(_j,AP);O=round(max(.1,S-Aj),1);Z=round(I.get(_h,_C),1);adb=round(I.get('db',_C),1);a=round(I.get(_x,_C),1);ah=round(I.get('history',_C),1);b=round(I.get(_i,_C),1);c=round(I.get(_b,_C),1);d=round(I.get(_c,_C),1);P=round(max(.1,N-F),1);A6=round(adb+Z+a+ah+c+b+d,1);e=round(D/max(.1,O),1);_rmb=float(I.get('raw_mb')or 0)or D;_sspd=round(_rmb/max(.1,A6),1)if A6>0 else _C;Q=os.path.basename(B);A.set_progress(100,f"Готово! Архів збережено ({D:.2f} МБ)");A.set_pill(f"ГОТОВО | {D:.1f} МБ",_F);Ak=format_duration(P,A.state.get(_R,_S)).partition(' (').__getitem__(0);A.log(f"УСПІХ! Резервне копіювання завершено за {Ak} ({i} → {A5}).",_F);A7=get_fast_sysinfo();ni=detect_network_adapter(k);ni_s=f" | {ni['scope']} {ni['label']} ({ni['desc'] or ni['name']})"if ni.get('label')else'';A8=f"v{SCRIPT_VER} | {A7}{ni_s} | download {e} MB/s ({O} s) | server {A6} s | total {P} s | files {G}";A.log(f"[SUMMARY] {A8}",_H);from core.i18n import tr as Al;Am=A.state.get(_R,_S);_desktop_notify(_n,Al(f"Резервну копію створено: {Q} ({D:.1f} МБ)",Am));A.state[f]=max(int(A.state.get(f,0)),0)+1;A.state[AH]=round(max(float(A.state.get(AH,_C)),_C)+D,1);commit_state(A.state)
		if hasattr(A,AI):A.record_op_event('Успішно',Q,round(D,1),dur_sec=P,started_at=F,finished_at=N)
		_record_cloud_event(A,C,g,archive=Q,size_mb=D,size_bytes=M,files_count=G,duration_sec=N-F,speed_mbps=D/max(N-F,.001),download_speed_mbps=e,download_duration_sec=O,server_duration_sec=A6,srv_speed_mbps=_sspd,srv_raw_mb=_rmb,server_preparing_sec=Z,server_copying_sec=a,server_processing_sec=c,server_packing_sec=b,server_checking_sec=d,crc_duration_sec=w,sha256_duration_sec=x,mirror_enabled=V,mirror_duration_sec=W,gfs_removed_count=A3,system_info=A7,net_scope=ni.get('scope',''),srv_host=ni.get('srv_host',''),srv_conn_est=ni.get('srv_conn_est',''),net_adapter_name=ni.get('desc')or ni.get('name',''),net_adapter_type=ni.get('type',''),net_link_mbps=ni.get('link_mbps',0),net_adapter_label=ni.get('label',''),summary=A8);_sync_cloud_reports(A)
		if not SILENT_MODE and not h:An,Ao,Ap=A.get_storage_stats();Aq={'file':Q,'srv':k,'size_mb':round(D,2),'files_cnt':G,'ts_start':i,'ts_end':A5,'total_sec':P,'srv_db_sec':adb,'srv_prep_sec':Z,'srv_copy_sec':a,'srv_hist_sec':ah,'srv_proc_sec':c,'srv_pack_sec':b,'srv_chk_sec':d,'dl_sec':O,'buf_kb':int(A.state.get(_l,64)or 64),'spd_mbs':e,'srv_spd_mbs':_sspd,'srv_raw_mb':_rmb,'crc_sec':w,'sha_sec':x,'mir_active':V,'mir_sec':W,'net_active':A1,'net_sec':Ab,'z_cnt':An,'z_mb':Ao,'free_gb':Ap,'old_cnt':A3,'net_scope':ni.get('scope',''),'srv_conn_est':ni.get('srv_conn_est',''),'net_adapter_label':ni.get('label',''),'net_adapter_name':ni.get('desc')or ni.get('name','')};A.ask_modal('backup_report','Звіт про резервне копіювання',json.dumps(Aq,ensure_ascii=_B))
	except Exception as J:
		A.exit_code=1;A.log(f"ПОМИЛКА: {J}",_I);from core.i18n import tr as Ar;_desktop_notify(Ar('HomeGrid Backup: помилка',A.state.get(_R,_S)),str(J)[:200]);A.set_pill('Помилка бекапу',_I)
		if hasattr(A,AI):A9=time.time();A.record_op_event('Помилка',str(J),_C,dur_sec=round(A9-F,1),started_at=F,finished_at=A9)
		_record_cloud_event(A,C,_X,archive=B,size_mb=D,duration_sec=time.time()-F,result=_X,error_type=type(J).__name__);_sync_cloud_reports(A);A.set_progress(0,f"Помилка: {J}")
		if not SILENT_MODE:A.ask_modal('alert','Помилка резервного копіювання',str(J))
	finally:
		if hasattr(A,'flush_logs'):A.flush_logs()
		try:
			import tempfile as As;AA=os.path.join(As.gettempdir(),_y)
			if os.path.isdir(AA):shutil.rmtree(AA,ignore_errors=_A)
		except Exception:0
		with A.lock:A.is_running=_B;A.indeterminate=_B
