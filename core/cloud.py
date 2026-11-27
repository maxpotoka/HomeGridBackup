# patch-id: cache-3sec-stats-90s-4.09
# patch-id: smart-bottleneck-4.06
# patch-id: py38-win32-no-removesuffix-3.74
# patch-id: cloud-union-d1-keys-3.71
# patch-id: d1-mine-backup-safe-3.68
# patch-id: d1-sync-keys-fix-3.61
# patch-id: d1-cache-toggle-setting-3.58
# patch-id: owner-prefix-anon-3.56
# patch-id: canon-srv-lan-wan-label-3.51
# patch-id: auto-owner-canon-srv-3.50
# patch-id: d1-always-send-3.48
# patch-id: live-d1-sync-3.47
# patch-id: client-os-binding-3.58
import stat, tempfile, threading
_rep_lock = threading.Lock()
def _reports_base_dir():
	h = os.path.expanduser('~')
	d = os.path.join(h, 'documents') if os.path.isdir(os.path.join(h, 'documents')) else (os.path.join(h, 'Documents') if os.path.isdir(os.path.join(h, 'Documents')) else '')
	if os.name == 'nt' or os.sys.platform == 'darwin':
		b = os.path.join(d or h, 'HomeGridBackup', _K)
	else:
		b = os.path.join(h, 'HomeGridBackup', _K)
	return b
_h='.HomeGridBackup-sources'
_g='net_dir'
_f='net_speed_mbps'
_e='net_duration_sec'
_d='speed_mbps'
_c='summary'
_b='mirror_duration_sec'
_a='sha256_duration_sec'
_Z='crc_duration_sec'
_Y='server_duration_sec'
_X='files_count'
_W='app_version'
_V='archives'
_U='download_speed_mbps'
_T='download_duration_sec'
_S='duration_sec'
_R='size_mb'
_Q='archive'
_P='stage'
_O='.jsonl'
_N='architecture'
_M='platform_version'
_L='platform'
_K='reports'
_J='event'
_I='utf-8'
_H='unknown'
_G=True
_F='timestamp'
_E='operation_id'
_D=None
_C=False
_B='device_id'
_A=.0
import shutil,csv,json,os,platform,re
from datetime import datetime
from uuid import uuid4
from core.config import SCRIPT_VER,SECURE_DIR
_DEVICE_ID_RE=re.compile('^[0-9a-f]{32}$')
class CloudRateLimitError(RuntimeError):0
def cloud_sync_error_text(error,language='en'):return str(error)
def new_operation_id():return uuid4().hex
def validate_cloud_settings(remote,cloud_path):A=(cloud_path or'').strip().strip('/');return A or'HomeGridBackup'
def _device_id(state):
	A=str(state.get(_B)or'')
	if not _DEVICE_ID_RE.fullmatch(A):raise ValueError('The device ID is missing or invalid.')
	return A
def sync_cloud_backups(engine,prune=_C,progress_cb=_D):return _C
def sync_cloud_reports(engine):return _C
def sync_pending_cloud_data(engine,force=_C):return{_V:0,_K:0,'total':0}
def start_cloud_sync_worker(engine,force=_C,on_complete=_D):return _C
def cloud_sync_queue_state(engine):return{_V:0,_K:0,'total':0}
def cloud_archive_sync_status(engine,archive):return _H
def get_cloud_dest_stats(state):0
def _collect_report_records(source_dirs,device_id=_D):
	E=device_id;F={}
	for B in source_dirs:
		if not os.path.isdir(B):continue
		for(I,J,K)in os.walk(B):
			J.sort()
			for G in sorted(K):
				if not G.endswith(_O):continue
				H=os.path.join(I,G);L=os.path.relpath(H,B)
				try:
					with open(H,'r',encoding=_I)as M:
						for(N,C)in enumerate(M,1):
							if not C.strip():continue
							A=json.loads(C)
							if not isinstance(A,dict):continue
							if E is not _D and A.get(_B)!=E:continue
							D=tuple(A.get(B,'')for B in(_B,_E,_J,_F,_P))
							if not all(D[:4]):D=L,N,C.strip()
							F[D]=A
				except Exception:continue
	return F
def _ordered_report_records(records):
	def A(record):
		A=record;C=A.get(_F,'')
		try:B=datetime.fromisoformat(C).timestamp()
		except(TypeError,ValueError,OverflowError):B=_A
		return B,A.get(_B,''),A.get(_E,''),A.get(_J,''),A.get(_P,'')
	return sorted(records.values(),key=A)
def _write_jsonl_report(records,output_path):
	A=_ordered_report_records(records)[-50:]
	with open(output_path,'w',encoding=_I,newline='')as B:
		for C in A:B.write(json.dumps(C,ensure_ascii=_C,sort_keys=_G)+chr(10))
	return len(A)
def _write_plain_text_report(records,output_path):
	D=_ordered_report_records(records);E={_F,_B,_E,_J,_L,_M,_N}
	with open(output_path,'w',encoding=_I,newline='')as F:
		for A in D:
			G=' '.join(str(A.get(B,'')).strip()for B in(_L,_M,_N)if A.get(B))or _H;B=[f"[{A.get(_F,_H)}]",f"OS={G}",f"device={A.get(_B,_H)}",f"event={A.get(_J,_H)}"]
			if A.get(_E):B.append(f"operation={A[_E]}")
			for C in sorted(A):
				if C not in E:H=json.dumps(A[C],ensure_ascii=_C,sort_keys=_G);B.append(f"{C}={H}")
			F.write(' | '.join(B)+chr(10))
	return len(D)
def _write_speed_csv_report(records,output_path):
	A=[A for A in _ordered_report_records(records)if A.get(_J)=='success'];B=_F,_B,_L,_M,_N,_W,_Q,_R,_X,_S,_T,_U,_Y,_Z,_a,_b,'net_scope','srv_conn_est','net_adapter_type','net_link_mbps','net_adapter_name',_c
	with open(output_path,'w',encoding='utf-8-sig',newline='')as D:
		C=csv.writer(D,delimiter=';');C.writerow(B)
		for E in A:C.writerow([E.get(A,'')for A in B])
	return len(A)
def record_operation_event(engine,operation_id,event,stage='',archive='',size_mb=_A,duration_sec=_D,**C):
	R='operations.jsonl';L=size_mb;K=archive;J=stage;I=event;H='size_bytes';F=engine;B=duration_sec
	if str(I).startswith('stage_'):return
	M=_device_id(F.state);S=datetime.now().astimezone();D=os.path.join(_reports_base_dir(),M);
	try:os.makedirs(D,exist_ok=_G)
	except Exception:D=os.path.join(tempfile.gettempdir(),'HomeGridBackup_reports',M);os.makedirs(D,exist_ok=_G)
	E=os.path.join(D,R);A={_F:S.isoformat(timespec='milliseconds'),_B:M,_E:operation_id,_J:I,_W:SCRIPT_VER,_L:platform.system(),_M:platform.release(),_N:platform.machine(),'python_version':platform.python_version(),'archives_total':max(0,int(F.state.get('all_time_cnt',0))),'host_name':''}
	if J:A[_P]=J
	if K:A[_Q]=os.path.basename(K)
	if L:A[_R]=round(float(L),1)
	if H in C:A[H]=max(0,int(C.pop(H)))
	if B is not _D:B=max(_A,float(B));A[_S]=round(B,3);A['duration_ms']=round(B*1000)
	_srv_t=float(A.get(_Y)or A.get('server_packing_sec')or 0)
	if float(A.get('srv_speed_mbps')or 0)<=0 and _srv_t>0 and float(A.get(_R)or 0)>0:A['srv_speed_mbps']=round(float(A[_R])/_srv_t,2)
	T={_X,'archive_sequence','srv_speed_mbps','srv_raw_mb',_d,_U,_T,_Y,'server_preparing_sec','server_copying_sec','server_processing_sec','server_packing_sec','server_checking_sec',_Z,_a,'mirror_enabled',_b,'net_enabled',_e,_f,'gfs_removed_count','system_info','net_scope','srv_conn_est','net_adapter_name','net_adapter_type','net_link_mbps','net_adapter_label','srv_host','os_bit','buf_kb',_c,'result','error_type'}
	for N in T.intersection(C):
		O=C[N]
		if O is not _D:A[N]=O
	with _rep_lock:
		for _att in range(3):
			try:
				if os.path.exists(E):os.chmod(E,stat.S_IWRITE|stat.S_IREAD)
				with open(E,'a',encoding=_I)as U:U.write(json.dumps(A,ensure_ascii=_C)+chr(10))
				break
			except PermissionError:
				if _att==2:raise
				import time as _tm;_tm.sleep(0.05)
	try:
		for G in os.listdir(D):
			if G.endswith(_O)and G!=R:os.remove(os.path.join(D,G))
		with open(E,'r',encoding=_I)as V:P=[A for A in V if A.strip()]
		try:
			if str(I)=='success':
				from core.speed_bench import push_backup_speed
				_spd_v = float(A.get(_U) or A.get(_d) or 0)
				if _spd_v <= 0 and float(A.get(_R) or 0) > 0 and float(A.get(_S) or 0) > 0:
					_spd_v = round(float(A[_R]) / float(A[_S]), 2)
				_os_v = ('%s %s' % (A.get(_L, ''), str(A.get(_M, '')).partition('-').__getitem__(0))).strip()
				push_backup_speed(F.state, _os_v, A.get('net_adapter_label') or A.get('net_adapter_type') or 'Backup', A.get('net_scope') or 'LAN', A.get(_R, 0), A.get(_S, 0), _spd_v, SCRIPT_VER, float(A.get('srv_speed_mbps') or 0), int(A.get('net_link_mbps') or 0), str(A.get('srv_host') or ''), int(A.get('buf_kb') or 64))
		except Exception:
			pass
		if len(P)>50:
			Q=E+'.tmp'
			with open(Q,'w',encoding=_I)as W:W.writelines(P[-50:])
			os.replace(Q,E)
	except Exception:0
def sync_network_shared_journal(engine):
	D=engine.state;A=os.path.expanduser((D.get(_g)or'').strip())
	if not A or not os.path.isdir(A):return _C
	C=_device_id(D);J=os.path.join(_reports_base_dir(),C);B=os.path.join(A,_h);os.makedirs(B,exist_ok=_G);E=_collect_report_records((B,J),device_id=C)
	if E:F=os.path.join(B,f"{C}.jsonl.tmp");_write_jsonl_report(E,F);os.replace(F,os.path.join(B,f"{C}.jsonl"))
	G=_collect_report_records((B,));H=os.path.join(A,'HomeGridBackup.log.tmp');_write_plain_text_report(G,H);os.replace(H,os.path.join(A,'HomeGridBackup.log'));I=os.path.join(A,'speed_journal.csv.tmp');_write_speed_csv_report(G,I);os.replace(I,os.path.join(A,'speed_journal.csv'));return _G
def fetch_cloud_speed_stats(engine,refresh=_G):
	k='avg_spd';j='avg_dur';i='spd_f';h='dev_label';S='net_spd_f';R='dur_f';K='.';L=engine.state;T=os.path.expanduser((L.get(_g)or'').strip());U=_reports_base_dir();V=os.path.join(U,'net_cache');_old_u=os.path.join(SECURE_DIR,_K);B=os.path.join(T,_h)if T else''
	if B and os.path.isdir(B):
		try:
			os.makedirs(V,exist_ok=_G)
			for M in os.listdir(B):
				if M.endswith(_O):shutil.copy2(os.path.join(B,M),os.path.join(V,M))
		except Exception:0
	W=[U]
	if os.path.isdir(_old_u)and _old_u!=U:W.append(_old_u)
	if os.path.isdir(V):W.append(V)
	if B and os.path.isdir(B):W.append(B)
	for extra in (os.path.join(T,'reports','net_cache') if T else '',):
		if extra and os.path.isdir(extra) and extra not in W:W.append(extra)
	l=_collect_report_records(tuple(W));X={}
	for H in _ordered_report_records(l):
		C=str(H.get(_B)or _H);Y=str(H.get(_E)or H.get(_F)or'');Z=X.setdefault((C,Y),{_B:C,_E:Y})
		for(a,b)in H.items():
			if b not in(_D,'',0,_A)or a not in Z:Z[a]=b
	c=str(L.get(_B)or'');I=[]
	for A in X.values():
		N=float(A.get(_S)or _A);D=float(A.get(_R)or _A)
		if N<=_A or D<=_A and not str(A.get(_Q,'')).lower().endswith(('.zip','.tar.zst')):continue
		d=float(A.get(_T)or _A);G=float(A.get(_U)or _A);apx=_C
		if G<=_A and D>_A and d>_A:G=round(D/d,2)
		if G<=_A:
			G=float(A.get(_d)or _A)
			if G<=_A and D>_A:G=round(D/N,2);apx=_G
		A['spd_approx']=apx
		J=str(A.get(_L)or'').strip();F=str(A.get(_M)or'').strip().partition('-').__getitem__(0)
		if J=='Linux'and K in F:m,q,n=F.partition(K);F=f"{m}.{n.partition(K).__getitem__(0)}"
		elif J=='Darwin':J='macOS';F=F.partition(K).__getitem__(0)
		hn=str(A.get('host_name')or(platform.node()if A.get(_B)==c else'')).strip();e_base=f"{J} {F}".strip()or'OS';e=f"{e_base} • {hn}"if hn else e_base;C=A[_B];A[h]=(f"* {e}"if C==c else e).strip();nt=str(A.get('net_adapter_type')or'').strip();lm=int(A.get('net_link_mbps')or 0);ls=f"{lm//1000} Gbps"if lm>=1000 and lm%1000==0 else(f"{lm} Mbps"if lm>0 else'');al=str(A.get('net_adapter_label')or'').strip()or(f"{nt} • {ls}"if nt and ls else nt);A['net_lbl']=al or'—';A['scope_norm']=str(A.get('net_scope')or'').strip()or'LAN';sh_v=str(A.get('srv_host')or'').strip();sh_v=sh_v or(str(L.get('server')or'').strip().replace('http://','').replace('https://','').rstrip('/')if A.get(_B)==c else'');A['srv_norm']=sh_v;A[R],A['mb_f'],A[i]=round(N,1),round(D,1),round(G,2);f=float(A.get(_e)or _A);A[S]=round(float(A.get(_f)or(D/f if f>0 else 0)),2);I.append(A)
	I.sort(key=lambda x:str(x.get(_F)or''),reverse=_G);g={}
	for A in I:g.setdefault(A[_B],[]).append(A)
	O=[]
	for(C,P)in g.items():ex=[A for A in P if not A.get('spd_approx')and A[i]>0];E=(ex or P)[:5];o=round(sum(A[R]for A in E)/len(E),1);tot_mb_s=sum(A['mb_f']for A in E);tot_dl_s=sum(float(A.get(_T)or 0)for A in E);p=round(tot_mb_s/tot_dl_s,2)if tot_dl_s>0 else round(sum(A[i]for A in E)/len(E),2);Q=[A for A in E if A.get(S,0)>0];O.append({_B:C,'label':P[0][h],'is_own':C==c,'total_cnt':len(P),'sample_cnt':len(E),j:o,'min_dur':min(A[R]for A in E),'avg_net_spd':round(sum(A[S]for A in Q)/len(Q),1)if Q else _A,k:p})
	O.sort(key=lambda d:(-d[k],d[j]))
	srv_g={};srv_ops=[];_def_srv=(str(L.get('server')or'').replace('http://','').replace('https://','').strip().rstrip('/'))
	for A in I:
		if float(A.get('srv_raw_mb')or 0)<=0 and float(A.get('srv_speed_mbps')or 0)<10:continue
		sv_tm=float(A.get(_Y)or A.get('server_packing_sec')or 0)
		sv_raw=float(A.get('srv_raw_mb')or 0)
		sv_sp=float(A.get('srv_speed_mbps')or 0)
		if sv_raw>0 and sv_tm>0:sv_sp=round(sv_raw/sv_tm,2)
		elif sv_sp<=0 and sv_tm>0 and float(A.get('mb_f')or 0)>0:sv_sp=round(float(A.get('mb_f')or 0)/sv_tm,2)
		if sv_sp<=0:continue
		sn=str(A.get('srv_norm')or'').strip()
		if not sn or sn=='Server':sn=_def_srv or'HomeGrid Server'
		sid=f"srv_{sn}"
		srv_g.setdefault(sn,[]).append((sv_sp,sv_tm,sv_raw or float(A.get('mb_f')or 0)))
		op_s=dict(A);op_s[_B]=sid;op_s[h]=f"* {sn}";op_s['net_lbl']='Server CPU/Disk';op_s['scope_norm']='ALL';op_s[i]=round(sv_sp,2);op_s[R]=round(sv_tm,1);op_s['mb_f']=round(sv_raw or float(A.get('mb_f')or 0),1);op_s['spd_approx']=_C;op_s['is_d1_srv']=_C
		srv_ops.append(op_s)
	SRV=[]
	for(sn,sp_l)in srv_g.items():
		sm=sp_l[:5];sdur=round(sum(x.__getitem__(1)for x in sm)/len(sm),1);sspd=round(sum(x.__getitem__(0)for x in sm)/len(sm),2);sid=f"srv_{sn}"
		SRV.append({_B:sid,'label':f"* {sn}",'is_own':_G,'is_d1_srv':_C,'scope_norm':'ALL','total_cnt':len(sp_l),'sample_cnt':len(sm),j:sdur,'min_dur':min(x.__getitem__(1)for x in sm),'avg_net_spd':_A,k:sspd,'net_lbl':f"{len(sp_l)}x"})
	try:
		from core.speed_bench import fetch_global_stats
		for idx_s,r_s in enumerate(fetch_global_stats()):
			asrv_v=float(r_s.get('avg_srv')or 0)
			if asrv_v<=0:continue
			os_s=str(r_s.get('os_label')or'Server').replace("['",'').replace("']",'').strip();hw_s=str(r_s.get('hw_tag')or'').strip();cnt_s=int(r_s.get('tests')or 1);usr_s=int(r_s.get('users')or 1);sid=f"d1_srv_{idx_s}_{os_s}";lbl_s=f"[D1] {os_s}"+(f" ({hw_s})"if hw_s else'')
			SRV.append({_B:sid,'label':lbl_s,'is_own':_C,'is_d1_srv':_G,'scope_norm':'ALL','total_cnt':cnt_s,'sample_cnt':cnt_s,j:_A,'min_dur':_A,'avg_net_spd':_A,k:round(asrv_v,2),'net_lbl':f"D1 ? {usr_s} PC ({cnt_s}x)"})
			srv_ops.append({_B:sid,h:lbl_s,'net_lbl':f"D1 ({cnt_s}x)",'scope_norm':'ALL',_Q:f"Server pack: {asrv_v} MB/s",'mb_f':_A,R:_A,i:round(asrv_v,2),S:_A,'spd_approx':_C,'is_d1_srv':_G,_F:f"{cnt_s} tests"})
	except Exception:0
	SRV.sort(key=lambda d:(-d[k],d[j]))
	return{'ops':I,'devices':O,'servers':SRV,'srv_ops':srv_ops}

def fetch_global_d1_speed_stats(engine):
	try:
	    from core.speed_bench import fetch_global_stats
	    rows = fetch_global_stats()
	    def _os_key(val):
	        pts = str(val or '').strip().split()
	        if len(pts) >= 2 and pts[0] == 'Linux':
	            return 'Linux ' + '.'.join(pts[1].split('.')[:2])
	        return ' '.join(pts[:2]) if len(pts) >= 2 else (pts[0] if pts else '')
	    bench_map = {}
	    for x in rows:
	        if str(x.get('adapter') or '').strip().lower() == 'bench':
	            k_os = _os_key(x.get('os_label'))
	            if k_os:
	                bench_map[k_os] = x
	    ops, devs, seen_os = [], [], set()
	    for idx, r in enumerate(rows):
	        ad = str(r.get('adapter') or '').strip()
	        if ad.lower() == 'bench':
	            continue
	        os_l = str(r.get('os_label') or 'OS').replace("['", '').replace("']", '').strip()
	        k_os = _os_key(os_l)
	        seen_os.add(k_os)
	        bm = bench_map.get(k_os, {})
	        sc = str(r.get('scope') or 'LAN').strip()
	        cnt = int(r.get('tests') or 0)
	        usr = int(r.get('users') or 1)
	        aspd = float(r.get('avg_spd') or 0); asrv = float(r.get('avg_srv') or 0)
	        mspd = float(r.get('max_spd') or aspd)
	        acpu = round(float(r.get('avg_cpu') or bm.get('avg_cpu') or 0), 1)
	        adw = round(float(r.get('avg_disk_w') or bm.get('avg_disk_w') or 0), 1)
	        adr = round(float(r.get('avg_disk_r') or bm.get('avg_disk_r') or 0), 1)
	        if aspd <= 0 and acpu <= 0 and adw <= 0 and adr <= 0:
	            continue
	        short_os = os_l.replace('Pro for Workstations', 'Pro').replace('Home 22H2', 'Home').replace('Ultimate', '').strip()
	        hw_t = str(r.get('hw_tag') or bm.get('hw_tag') or '').strip()
	        hw_sfx = f' • {hw_t}' if hw_t else ''
	        did = f"d1_{idx}_{os_l}_{sc}"
	        is_net = (sc == 'Internet')
	        raw_dur = float(r.get('dur_sec') or 0); est_dur = round(raw_dur if raw_dur > 0 else (100.0 / max(0.1, aspd) if aspd > 0 else 0.0), 1)
	        ops.append({'device_id': did, 'dev_label': f"{short_os} ({usr} PC){hw_sfx}", 'net_lbl': f"{sc} ({cnt}x)", 'scope_norm': sc, 'archive': f"Avg: {aspd} MB/s • Max: {mspd} MB/s", 'mb_f': round(float(r.get('size_mb') or 100.0), 1), 'dur_f': est_dur, 'spd_f': round(aspd, 2), 'net_spd_f': round(aspd, 2) if is_net else 0.0, 'avg_cpu': acpu, 'avg_disk_w': adw, 'avg_disk_r': adr, 'timestamp': f"{cnt} tests"})
	        devs.append({'device_id': did, 'label': short_os, 'is_own': False, 'total_cnt': cnt, 'sample_cnt': cnt, 'avg_dur': est_dur, 'min_dur': est_dur, 'avg_net_spd': round(aspd, 2) if is_net else 0.0, 'avg_spd': round(aspd, 2), 'avg_cpu': acpu, 'avg_disk_w': adw, 'avg_disk_r': adr, 'net_lbl': f"{sc} • {cnt}x"})
	    for k_os, bm in bench_map.items():
	        if k_os in seen_os:
	            continue
	        os_l = str(bm.get('os_label') or k_os).strip()
	        hw_t = str(bm.get('hw_tag') or '').strip()
	        hw_sfx = f' • {hw_t}' if hw_t else ''
	        cnt = int(bm.get('tests') or 1)
	        acpu = round(float(bm.get('avg_cpu') or 0), 1)
	        adw = round(float(bm.get('avg_disk_w') or 0), 1)
	        adr = round(float(bm.get('avg_disk_r') or 0), 1)
	        if acpu <= 0 and adw <= 0 and adr <= 0:
	            continue
	        did = f"d1_bench_{os_l}"
	        ops.append({'device_id': did, 'dev_label': f"{os_l}{hw_sfx}", 'net_lbl': f"Bench ({cnt}x)", 'scope_norm': 'LAN', 'archive': f"CPU: {acpu} • W: {adw} • R: {adr} MB/s", 'mb_f': 32.0, 'dur_f': 0.0, 'spd_f': round(max(acpu, adw, adr), 2), 'net_spd_f': 0.0, 'avg_cpu': acpu, 'avg_disk_w': adw, 'avg_disk_r': adr, 'timestamp': f"{cnt} bench"})
	        devs.append({'device_id': did, 'label': os_l, 'is_own': False, 'total_cnt': cnt, 'sample_cnt': cnt, 'avg_dur': 0.0, 'min_dur': 0.0, 'avg_net_spd': 0.0, 'avg_spd': round(max(acpu, adw, adr), 2), 'avg_cpu': acpu, 'avg_disk_w': adw, 'avg_disk_r': adr, 'net_lbl': f"Bench • {cnt}x"})
	    devs.sort(key=lambda d: -(0.5 * d['avg_spd'] + 0.3 * max(d['avg_disk_w'], d['avg_disk_r']) + 0.2 * d['avg_cpu']))
	    return {'ops': ops, 'devices': devs}
	except Exception:
		return dict(ops=[],devices=[])


def _med(v):
    import statistics as _st
    x = [float(i) for i in v if float(i or 0) > 0]
    return round(_st.median(x), 1) if x else 0.0

def _grp_lbl(sc, ad, lk, est=''):
    if str(sc).lower() == 'internet':
        return 'Internet (WAN)'
    a_low = f'{ad} {est}'.lower()
    is_wifi = any(w in a_low for w in ('wi-fi', 'wifi', 'wlan', 'wireless', '802.11'))
    kind = 'Wi-Fi' if is_wifi else 'Ethernet'
    m = int(lk or 0)
    l = f'{round(m/1000.,1):g} Gbps' if m >= 1000 else (f'{m} Mbps' if m > 0 else '')
    return f'LAN • {kind} ({l})' if l else f'LAN • {kind}'

def _os_arch_lbl(raw_sys, os_bit=''):
    t = str(raw_sys or '').strip()
    if '-bit)' in t:
        return t
    import platform as _pl, struct as _st
    b = str(os_bit or '').strip() or f"{_st.calcsize('P')*8}-bit"
    base = t.split('[')[0].split('|')[0].strip() if ('[' in t or '|' in t) else (t or f"{_pl.system()} {_pl.release()}".strip())
    return f"{base} ({b})"

def _net_pair_key(srv_h, os_lbl, sc, ad, lk, buf_kb, est=''):
    sh = str(srv_h or '').strip()
    for _suf in (':443', ':80'):
        if sh.endswith(_suf):
            sh = sh[:-len(_suf)]
    sh = sh or 'Unknown server'
    os_s = _os_arch_lbl(os_lbl)
    base = _grp_lbl(sc, ad, lk, est)
    b_kb = int(buf_kb or 64)
    return f"{sh} • {os_s} • {base}"

def _os_base_norm(val):
    s = str(val or '').strip()
    s = s.split('(')[0].split('[')[0].strip()
    pts = s.split()
    if len(pts) >= 2 and pts[0].lower() == 'windows':
        return f"Windows {pts[1]}"
    if len(pts) >= 2 and pts[0].lower() == 'linux':
        return f"Linux {pts[1].split('.')[0]}"
    return s.lower()

def _canon_srv_label(raw_host, st):
    h = str(raw_host or '').strip().replace('http://', '').replace('https://', '').split('/')[0].strip()
    h_no_port = h.split(':')[0].strip()
    if not h_no_port or h_no_port == 'Server':
        h_no_port = str((st or {}).get('server') or '').replace('http://', '').replace('https://', '').split('/')[0].split(':')[0].strip()
    cands = [str((st or {}).get('server') or '')] + list((st or {}).get('server_history') or [])
    dom = ''
    for c in cands:
        ch = str(c).replace('http://', '').replace('https://', '').split('/')[0].split(':')[0].strip()
        if ch and not ch.replace('.', '').isdigit() and ch != 'localhost':
            dom = ch; break
    has_lan = any(str(c).replace('http://', '').replace('https://', '').startswith(('192.168.', '10.', '172.', '127.', 'localhost')) for c in cands)
    is_lan_ip = h_no_port.startswith(('192.168.', '10.', '172.', '127.')) or h_no_port == 'localhost'
    if dom and (is_lan_ip or h_no_port == dom):
        return f"{dom} (LAN + WAN)" if (has_lan or is_lan_ip) else dom
    return h_no_port or 'Unknown server'

def build_three_section_stats(engine, refresh=True):
    import time as _tm_c
    _st_c = getattr(engine, 'state', {}) or {}
    _csig = (_st_c.get('lang', 'uk'), bool(_st_c.get('show_bottleneck', True)), getattr(engine, '_chart_rev', 0))
    if not refresh and getattr(engine, '_3sec_cache_sig', None) == _csig and (_tm_c.time() - getattr(engine, '_3sec_cache_t', 0.0)) < 90.0:
        _cached = getattr(engine, '_3sec_cache_val', None)
        if isinstance(_cached, dict): return dict(_cached)
    from core.speed_bench import _anon_id, _owner_id, fetch_global_stats, sync_local_history_to_d1
    st = getattr(engine, 'state', {}) or {}
    aid = _anon_id(st)
    oid = _owner_id(st)
    ops = fetch_cloud_speed_stats(engine, refresh=False).get('ops', [])
    sync_local_history_to_d1(st, ops, log_fn=getattr(engine, 'log', None))
    all_d1 = fetch_global_stats('ALL', use_cache=bool(st.get('d1_use_cache', True)))
    own_p = aid.split(':')[0] if ':' in aid else ''
    def _is_mine(r):
        ra = str(r.get('anon_id') or '')
        if not ra:
            return False
        if own_p and ':' in ra:
            return ra.split(':')[0] == own_p
        return ra == aid
    d1 = [r for r in all_d1 if not _is_mine(r)]
    my_d1_b = [r for r in all_d1 if _is_mine(r) and str(r.get('kind') or '') == 'backup']
    if my_d1_b:
        _loc_os = {str(x.get('system_info') or x.get('platform') or '').partition('(').__getitem__(0).strip() for x in ops if x.get('system_info') or x.get('platform')}
        for _mr in my_d1_b:
            _mos_full = str(_mr.get('os_label') or '').strip()
            _mos_base = _mos_full.partition('(').__getitem__(0).strip()
            if _mos_base and _mos_base not in _loc_os:
                _sz = float(_mr.get('size_mb') or 100.0)
                _sp = float(_mr.get('spd_mbs') or 0.0)
                _sv = float(_mr.get('srv_mbs') or 0.0)
                if _sp <= 0 and _sv <= 0:
                    continue
                _dur = round(_sz / _sp, 2) if _sp > 0 else 1.0
                _sh = _canon_srv_label(_mr.get('srv_host'), st)
                _sc = str(_mr.get('scope') or 'LAN')
                _ad = str(_mr.get('adapter') or 'Backup')
                ops.append({
                    'event': 'success',
                    'system_info': _mos_full,
                    'platform': _mos_base,
                    'srv_host': _sh,
                    'srv_norm': _sh,
                    'net_adapter_label': _ad,
                    'net_adapter_type': _ad,
                    'net_lbl': _ad,
                    'net_link_mbps': int(_mr.get('link_mbps') or 0),
                    'scope_norm': _sc,
                    'net_scope': _sc,
                    'dev_label': _mos_full,
                    'buf_kb': int(_mr.get('buf_kb') or 64),
                    'mb_f': _sz,
                    'size_mb': _sz,
                    'dur_f': _dur,
                    'duration_sec': _dur,
                    'spd_f': _sp,
                    'net_spd_f': _sp,
                    'download_speed_mbps': _sp,
                    'srv_speed_mbps': _sv,
                    'spd_approx': False,
                })
    srv_my = {}
    for o in ops:
        sv = float(o.get('srv_speed_mbps') or 0)
        tm = float(o.get('server_duration_sec') or o.get('server_packing_sec') or 0)
        if tm <= 0 and float(o.get('dur_f') or 0) > float(o.get('download_duration_sec') or 0) + 0.2:
            tm = round(float(o.get('dur_f')) - float(o.get('download_duration_sec') or 0), 2)
        rw = float(o.get('srv_raw_mb') or 0); rw_fall = float(o.get('mb_f') or 0)
        if rw > 0 and tm > 0:
            sv = round(rw / tm, 2)
        elif sv <= 0 and rw_fall > 0 and tm > 0:
            sv = round(rw_fall / tm, 2)
        if sv <= 0:
            continue
        h_base = _canon_srv_label(o.get('srv_host') or o.get('srv_norm'), st)
        os_c = _os_arch_lbl(o.get('system_info'), o.get('os_bit'))
        h = f"{h_base} • {os_c}"
        srv_my.setdefault(h, []).append((sv, float(o.get('srv_raw_mb') or 0) > 0, os_c))
    d1_srv_by_os = {}
    for r in d1:
        if r.get('kind') == 'bench' or str(r.get('adapter') or '').lower() == 'bench':
            continue
        sv = float(r.get('srv_mbs') or r.get('avg_srv') or 0)
        if sv <= 0:
            continue
        os_k = _os_base_norm(r.get('os_label'))
        n_rep = max(1, int(r.get('tests') or 1))
        d1_srv_by_os.setdefault(os_k, []).extend([sv] * n_rep)
    srv_rows = []
    _seen_srv_os = set()
    for h, items_my in srv_my.items():
        _raw_l = [s[0] for s in items_my if s[1]][:5]
        v_my = _raw_l or [s[0] for s in items_my][:5]
        os_tag = items_my[0][2]
        _ok = _os_base_norm(os_tag)
        _seen_srv_os.add(_ok)
        v_d1 = d1_srv_by_os.get(_ok, [])
        srv_rows.append({'name': h, 'os': os_tag, 'my': _med(v_my), 'd1': _med(v_d1), 'n_my': len(v_my), 'n_d1': len(v_d1)})
    _d1_os_lbl = {}
    for r in d1:
        if r.get('kind') != 'bench' and float(r.get('srv_mbs') or r.get('avg_srv') or 0) > 0:
            _ok = _os_base_norm(r.get('os_label'))
            if _ok and _ok not in _d1_os_lbl:
                _d1_os_lbl[_ok] = str(r.get('os_label') or _ok).strip()
    for _ok, v_d1 in d1_srv_by_os.items():
        if _ok not in _seen_srv_os and v_d1:
            os_tag = _d1_os_lbl.get(_ok, _ok)
            srv_rows.append({'name': f'Cloud D1 • {os_tag}', 'os': os_tag, 'my': 0.0, 'd1': _med(v_d1), 'n_my': 0, 'n_d1': len(v_d1)})
    net_my, net_sz = {}, {}
    for o in ops:
        sp, sz = float(o.get('spd_f') or 0), float(o.get('mb_f') or 0)
        if sp <= 0 or o.get('spd_approx'):
            continue
        sh = _canon_srv_label(o.get('srv_host') or o.get('srv_norm'), st)
        os_s = _os_arch_lbl(o.get('system_info'), o.get('os_bit'))
        b_kb = int(o.get('buf_kb') or 64)
        g = _net_pair_key(sh, os_s, o.get('scope_norm'), o.get('net_adapter_type') or o.get('net_adapter_label'), o.get('net_link_mbps'), b_kb, o.get('srv_conn_est'))
        net_my.setdefault(g, []).append(sp)
        if sz > 0:
            net_sz.setdefault(g, []).append(sz)
    net_rows = []
    for g, v in net_my.items():
        parts = [p.strip() for p in g.split('•')]
        os_part = parts[1] if len(parts) > 1 else ''
        os_k = _os_base_norm(os_part)
        is_wan = 'Internet' in g
        dm = []
        for r in d1:
            if r.get('kind') == 'bench' or str(r.get('adapter') or '').lower() == 'bench':
                continue
            sp_d = float(r.get('spd_mbs') or r.get('avg_spd') or 0)
            if sp_d <= 0:
                continue
            if _os_base_norm(r.get('os_label')) != os_k:
                continue
            r_wan = (str(r.get('scope') or '').lower() == 'internet')
            if r_wan != is_wan:
                continue
            dm.extend([sp_d] * max(1, int(r.get('tests') or 1)))
        net_rows.append({'group': g, 'os': os_part, 'my': _med(v), 'd1': _med(dm), 'n_my': len(v), 'n_d1': len(dm)})
    _seen_net_os = {(_os_base_norm(r['os']), 'Internet' in r['group']) for r in net_rows}
    _d1_net_grp = {}
    for r in d1:
        if r.get('kind') == 'bench' or str(r.get('adapter') or '').lower() == 'bench':
            continue
        sp_d = float(r.get('spd_mbs') or r.get('avg_spd') or 0)
        if sp_d <= 0:
            continue
        os_raw = str(r.get('os_label') or '').strip()
        _ok = _os_base_norm(os_raw)
        r_wan = (str(r.get('scope') or '').lower() == 'internet')
        if (_ok, r_wan) in _seen_net_os:
            continue
        _d1_net_grp.setdefault((_ok, r_wan, os_raw), []).extend([sp_d] * max(1, int(r.get('tests') or 1)))
    for (_ok, r_wan, os_raw), dm in _d1_net_grp.items():
        sc_lbl = 'Internet' if r_wan else 'LAN'
        net_rows.append({'group': f'Cloud D1 • {os_raw} • {sc_lbl}', 'os': os_raw, 'my': 0.0, 'd1': _med(dm), 'n_my': 0, 'n_d1': len(dm)})
    import platform as _pl
    from core.speed_bench import load_local_benchmarks, _hw_tag
    def_pc = f"{_pl.node()} ({_hw_tag()})"[:48]
    d1_b = [r for r in d1 if r.get('kind') == 'bench' or str(r.get('adapter') or '').lower() == 'bench' or float(r.get('cpu_mbs') or r.get('avg_cpu') or 0) > 0]
    my_b = load_local_benchmarks() + [r for r in all_d1 if _is_mine(r) and (r.get('kind') == 'bench' or float(r.get('cpu_mbs') or 0) > 0)]
    by_pc = {}
    for x in my_b:
        pc_n = str(x.get('pc') or def_pc).strip() or def_pc
        by_pc.setdefault(pc_n, []).append(x)
    if not by_pc:
        by_pc[def_pc] = []
    hw_rows = []
    for pc_n, items in by_pc.items():
        os_hw = next((str(x.get('os_label')) for x in items if x.get('os_label')), '') or (pc_n.split('[', 1)[1].split(']', 1)[0] if '[' in pc_n and ']' in pc_n else _os_arch_lbl(''))
        os_k = _os_base_norm(os_hw)
        d1_match = [x for x in d1_b if _os_base_norm(x.get('os_label')) == os_k] or d1_b
        for k, k_alt, m in (('cpu_mbs', 'avg_cpu', 'CPU (CRC32)'), ('sha_mbs', 'avg_sha', 'SHA-256'), ('disk_w_mbs', 'avg_disk_w', 'Disk Write'), ('disk_r_mbs', 'avg_disk_r', 'Disk Read')):
            v_my = [x.get(k) for x in items if float(x.get(k) or 0) > 0]
            v_d1 = [float(x.get(k) or x.get(k_alt) or 0) for x in d1_match if float(x.get(k) or x.get(k_alt) or 0) > 0]
            hw_rows.append({'pc': pc_n, 'os': os_hw, 'metric': f"{pc_n} • {m}", 'my': _med(v_my), 'd1': _med(v_d1), 'n_my': len(v_my), 'n_d1': len(v_d1)})
    bn_info = analyze_bottleneck(engine, d1_rows=d1, lang=st.get('lang', 'uk'))
    _res = {'server': srv_rows, 'network': net_rows, 'hardware': hw_rows, 'bottleneck': bn_info}
    try: engine._3sec_cache_sig = _csig; engine._3sec_cache_t = _tm_c.time(); engine._3sec_cache_val = dict(_res)
    except Exception: pass
    return _res

def analyze_bottleneck(engine, d1_rows=None, lang='uk'):
    st = getattr(engine, 'state', {}) or {}; uk = (lang == 'uk')
    if not bool(st.get('show_bottleneck', True)):
        return {'enabled': False, 'level': 'off', 'text': ''}
    try: did = _device_id(st)
    except Exception: did = str(st.get('device_id') or '')
    recs = _collect_report_records((_reports_base_dir(),), device_id=did or None)
    succ = [r for r in _ordered_report_records(recs) if str(r.get('event') or '') == 'success' and float(r.get('size_mb') or 0) > 0]
    if len(succ) < 6:
        t_low = f"\u0412\u0443\u0437\u044c\u043a\u0435 \u043c\u0456\u0441\u0446\u0435: \u043c\u0430\u043b\u043e \u0434\u0430\u043d\u0438\u0445 (\u043f\u043e\u0442\u0440\u0456\u0431\u043d\u043e \u043c\u0456\u043d. 6 \u0431\u0435\u043a\u0430\u043f\u0456\u0432, \u0437\u0430\u0440\u0430\u0437: {len(succ)})" if uk else f"Bottleneck: low history (need 6+ backups, have {len(succ)})"
        return {'enabled': True, 'level': 'muted', 'text': t_low}
    cur, hist = succ[-1], succ[-21:-1]
    def _sp(r):
        sz = float(r.get('size_mb') or 0); rw = float(r.get('srv_raw_mb') or 0) or sz
        srv_t = float(r.get('server_duration_sec') or 0) or sum(float(r.get(k) or 0) for k in ('server_preparing_sec','server_copying_sec','server_processing_sec','server_packing_sec','server_checking_sec'))
        ss = float(r.get('srv_speed_mbps') or 0) or (rw / srv_t if srv_t > 0 and rw > 0 else 0.0)
        dt = float(r.get('download_duration_sec') or 0)
        sd = float(r.get('download_speed_mbps') or 0) or (sz / dt if dt > 0 and sz > 0 else 0.0)
        vt = float(r.get('crc_duration_sec') or 0) + float(r.get('sha256_duration_sec') or 0)
        mt = float(r.get('mirror_duration_sec') or 0)
        return {'srv': round(ss,1), 'dl': round(sd,1), 'ver': round(sz/vt,1) if vt>=0.05 and sz>0 else 0.0, 'mir': round(sz/mt,1) if r.get('mirror_enabled') and mt>=0.05 and sz>0 else 0.0}
    cs, hl = _sp(cur), [_sp(x) for x in hist]
    nm = {'srv': '\u0441\u0435\u0440\u0432\u0435\u0440' if uk else 'server', 'dl': '\u0437\u0430\u0432\u0430\u043d\u0442\u0430\u0436\u0435\u043d\u043d\u044f' if uk else 'download', 'ver': '\u043f\u0435\u0440\u0435\u0432\u0456\u0440\u043a\u0430 CRC/SHA' if uk else 'CRC/SHA check', 'mir': '\u0434\u0437\u0435\u0440\u043a\u0430\u043b\u043e' if uk else 'mirror'}
    cd = [(cs[k]/_med([x[k] for x in hl if x[k]>0]), k, cs[k], _med([x[k] for x in hl if x[k]>0])) for k in nm if cs[k]>0 and len([x[k] for x in hl if x[k]>0])>=4]
    if not cd: return {'enabled': True, 'level': 'muted', 'text': '\u0412\u0443\u0437\u044c\u043a\u0435 \u043c\u0456\u0441\u0446\u0435: \u043c\u0430\u043b\u043e \u0456\u0441\u0442\u043e\u0440\u0456\u0457 \u0435\u0442\u0430\u043f\u0456\u0432' if uk else 'Bottleneck: low stage history'}
    cd.sort(); sc, wk, cv, mv = next(iter(cd))
    if sc >= 0.80: return {'enabled': True, 'level': 'ok', 'text': '\u0412\u0443\u0437\u044c\u043a\u0435 \u043c\u0456\u0441\u0446\u0435: \u0432\u0441\u0456 \u0435\u0442\u0430\u043f\u0438 \u0432 \u043c\u0435\u0436\u0430\u0445 \u043d\u043e\u0440\u043c\u0438' if uk else 'Bottleneck: all stages within normal range'}
    dr = max(1, int(round((1.0 - sc) * 100))); un = '\u041c\u0411/\u0441' if uk else 'MB/s'; ok_os = _os_base_norm(cur.get('system_info') or cur.get('platform'))
    dm = _med([float(r.get('srv_mbs' if wk=='srv' else 'spd_mbs') or 0) for r in (d1_rows or []) if r.get('kind')!='bench' and (not ok_os or _os_base_norm(r.get('os_label'))==ok_os)]) if wk in ('srv','dl') else 0.0
    lvl = 'err' if (dm > 0 and cv < dm * 0.75) else 'warn'
    tl = (f" \u041d\u0438\u0436\u0447\u0435 D1 ({dm} {un}) \u2014 \u0441\u0438\u0441\u0442\u0435\u043c\u043d\u0435 \u043e\u0431\u043c\u0435\u0436\u0435\u043d\u043d\u044f." if lvl=='err' else f" \u0412 \u043c\u0435\u0436\u0430\u0445 D1 ({dm} {un}) \u2014 \u0440\u0430\u0437\u043e\u0432\u0430 \u043f\u0440\u043e\u0441\u0430\u0434\u043a\u0430.") if (dm>0 and uk) else ((f" Below D1 ({dm} {un}) ? systemic." if lvl=='err' else f" Within D1 ({dm} {un}) ? transient.") if dm>0 else '')
    tx = (f"\u0412\u0443\u0437\u044c\u043a\u0435 \u043c\u0456\u0441\u0446\u0435: {nm[wk]}, {cv} {un} (\u043d\u043e\u0440\u043c\u0430 {mv} {un}, -{dr}%)." if uk else f"Bottleneck: {nm[wk]}, {cv} {un} (norm {mv} {un}, -{dr}%).") + tl
    return {'enabled': True, 'level': lvl, 'text': tx}

