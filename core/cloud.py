# patch-id: accurate-dl-speed-approx-3.18
# patch-id: show-hw-tag-in-d1-table-3.17
# patch-id: net-scope-adapter-3.01-p2
# patch-id: pass-bench-fields-to-ops-3.09
# patch-id: fix-d1-devs-bench-bars-3.08
# patch-id: merge-d1-bench-metrics-3.07
# patch-id: d1-multi-metrics-3.06
# patch-id: speed-file-securedir-3.05
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
	A=[A for A in _ordered_report_records(records)if A.get(_J)=='success'];B=_F,_B,_L,_M,_N,_W,_Q,_R,_X,_S,_T,_U,_Y,_Z,_a,_b,'host_name','net_scope','srv_host','srv_conn_est','net_adapter_type','net_link_mbps','net_adapter_name',_c
	with open(output_path,'w',encoding='utf-8-sig',newline='')as D:
		C=csv.writer(D,delimiter=';');C.writerow(B)
		for E in A:C.writerow([E.get(A,'')for A in B])
	return len(A)
def record_operation_event(engine,operation_id,event,stage='',archive='',size_mb=_A,duration_sec=_D,**C):
	R='operations.jsonl';L=size_mb;K=archive;J=stage;I=event;H='size_bytes';F=engine;B=duration_sec
	if str(I).startswith('stage_'):return
	M=_device_id(F.state);S=datetime.now().astimezone();D=os.path.join(SECURE_DIR,_K,M);os.makedirs(D,mode=448,exist_ok=_G);E=os.path.join(D,R);A={_F:S.isoformat(timespec='milliseconds'),_B:M,_E:operation_id,_J:I,_W:SCRIPT_VER,_L:platform.system(),_M:platform.release(),_N:platform.machine(),'python_version':platform.python_version(),'archives_total':max(0,int(F.state.get('all_time_cnt',0))),'host_name':platform.node()}
	if J:A[_P]=J
	if K:A[_Q]=os.path.basename(K)
	if L:A[_R]=round(float(L),1)
	if H in C:A[H]=max(0,int(C.pop(H)))
	if B is not _D:B=max(_A,float(B));A[_S]=round(B,3);A['duration_ms']=round(B*1000)
	T={_X,'archive_sequence',_d,_U,_T,_Y,'server_preparing_sec','server_copying_sec','server_processing_sec','server_packing_sec','server_checking_sec',_Z,_a,'mirror_enabled',_b,'net_enabled',_e,_f,'gfs_removed_count','system_info','host_name','net_scope','srv_host','srv_conn_est','net_adapter_name','net_adapter_type','net_link_mbps','net_adapter_label',_c,'result','error_type'}
	for N in T.intersection(C):
		O=C[N]
		if O is not _D:A[N]=O
	with open(E,'a',encoding=_I)as U:U.write(json.dumps(A,ensure_ascii=_C)+chr(10))
	try:
		for G in os.listdir(D):
			if G.endswith(_O)and G!=R:os.remove(os.path.join(D,G))
		with open(E,'r',encoding=_I)as V:P=[A for A in V if A.strip()]
		# patch-id: cloud-gsi-sync-305
		try:
			if str(I)=='success' and F.state.get('global_speed_optin'):
				from core.speed_bench import push_backup_speed
				_spd_v = float(A.get(_U) or A.get(_d) or 0)
				if _spd_v <= 0 and float(A.get(_R) or 0) > 0 and float(A.get(_S) or 0) > 0:
					_spd_v = round(float(A[_R]) / float(A[_S]), 2)
				_os_v = ('%s %s' % (A.get(_L, ''), str(A.get(_M, '')).split('-'))).strip()
				push_backup_speed(F.state, _os_v, A.get('net_adapter_label') or A.get('net_adapter_type') or 'Backup', A.get('net_scope') or 'LAN', A.get(_R, 0), A.get(_S, 0), _spd_v, SCRIPT_VER)
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
	C=_device_id(D);J=os.path.join(SECURE_DIR,_K,C);B=os.path.join(A,_h);os.makedirs(B,exist_ok=_G);E=_collect_report_records((B,J),device_id=C)
	if E:F=os.path.join(B,f"{C}.jsonl.tmp");_write_jsonl_report(E,F);os.replace(F,os.path.join(B,f"{C}.jsonl"))
	G=_collect_report_records((B,));H=os.path.join(A,'HomeGridBackup.log.tmp');_write_plain_text_report(G,H);os.replace(H,os.path.join(A,'HomeGridBackup.log'));I=os.path.join(A,'speed_journal.csv.tmp');_write_speed_csv_report(G,I);os.replace(I,os.path.join(A,'speed_journal.csv'));return _G
def fetch_cloud_speed_stats(engine,refresh=_G):
	k='avg_spd';j='avg_dur';i='spd_f';h='dev_label';S='net_spd_f';R='dur_f';K='.';L=engine.state;T=os.path.expanduser((L.get(_g)or'').strip());U=os.path.join(SECURE_DIR,_K);V=os.path.join(U,'net_cache');B=os.path.join(T,_h)if T else''
	if B and os.path.isdir(B):
		try:
			os.makedirs(V,exist_ok=_G)
			for M in os.listdir(B):
				if M.endswith(_O):shutil.copy2(os.path.join(B,M),os.path.join(V,M))
		except Exception:0
	W=[U]
	if os.path.isdir(V):W.append(V)
	if B and os.path.isdir(B):W.append(B)
	for extra in (os.path.join(T,'reports','net_cache') if T else '', r'P:\HomeGridBackup\.HomeGridBackup-sources', r'P:\HomeGridBackup\reports\net_cache'):
		if extra and os.path.isdir(extra) and extra not in W:W.append(extra)
	l=_collect_report_records(tuple(W));X={}
	for H in _ordered_report_records(l):
		C=str(H.get(_B)or _H);Y=str(H.get(_E)or H.get(_F)or'');Z=X.setdefault((C,Y),{_B:C,_E:Y})
		for(a,b)in H.items():
			if b not in(_D,'',0,_A)or a not in Z:Z[a]=b
	c=str(L.get(_B)or'');I=[]
	for A in X.values():
		N=float(A.get(_S)or _A);D=float(A.get(_R)or _A)
		if N<=_A or D<=_A and not str(A.get(_Q,'')).lower().endswith('.zip'):continue
		d=float(A.get(_T)or _A);G=float(A.get(_U)or _A);apx=_C
		if G<=_A and D>_A and d>_A:G=round(D/d,2)
		if G<=_A:
			G=float(A.get(_d)or _A)
			if G<=_A and D>_A:G=round(D/N,2);apx=_G
		A['spd_approx']=apx
		J=str(A.get(_L)or'').strip();F=str(A.get(_M)or'').strip().partition('-').__getitem__(0)
		if J=='Linux'and K in F:m,q,n=F.partition(K);F=f"{m}.{n.partition(K).__getitem__(0)}"
		elif J=='Darwin':J='macOS';F=F.partition(K).__getitem__(0)
		hn=str(A.get('host_name')or(platform.node()if A.get(_B)==c else'')).strip();e_base=f"{J} {F}".strip()or'OS';e=f"{e_base} • {hn}"if hn else e_base;C=A[_B];A[h]=(f"* {e}"if C==c else e).strip();nt=str(A.get('net_adapter_type')or'').strip();lm=int(A.get('net_link_mbps')or 0);ls=f"{lm//1000} Gbps"if lm>=1000 and lm%1000==0 else(f"{lm} Mbps"if lm>0 else'');al=str(A.get('net_adapter_label')or'').strip()or(f"{nt} • {ls}"if nt and ls else nt);A['net_lbl']=al or'—';A['scope_norm']=str(A.get('net_scope')or'').strip()or'LAN';sh_v=str(A.get('srv_host')or'').strip();sh_v=sh_v or(str((engine.state.get('server')if'engine'in dir()else'')or'').strip().replace('http://','').replace('https://','').rstrip('/')if A.get(_B)==c else'');A['srv_norm']=sh_v;A[R],A['mb_f'],A[i]=round(N,1),round(D,1),round(G,2);f=float(A.get(_e)or _A);A[S]=round(float(A.get(_f)or(D/f if f>0 else 0)),2);I.append(A)
	I.sort(key=lambda x:str(x.get(_F)or''),reverse=_G);g={}
	for A in I:g.setdefault(A[_B],[]).append(A)
	O=[]
	for(C,P)in g.items():E=P[:2];o=round(sum(A[R]for A in E)/len(E),1);ex=[A for A in P if not A.get('spd_approx')and A[i]>0];src_p=ex or P;p=round(sum(A[i]for A in src_p)/len(src_p),2);Q=[A for A in P if A.get(S,0)>0];O.append({_B:C,'label':P[0][h],'is_own':C==c,'total_cnt':len(P),'sample_cnt':len(E),j:o,'min_dur':min(A[R]for A in E),'avg_net_spd':round(sum(A[S]for A in Q)/len(Q),1)if Q else _A,k:p})
	O.sort(key=lambda d:(-d[k],d[j]));return{'ops':I,'devices':O}


def fetch_global_d1_speed_stats(engine):
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
        os_l = str(r.get('os_label') or 'OS').strip()
        k_os = _os_key(os_l)
        seen_os.add(k_os)
        bm = bench_map.get(k_os, {})
        sc = str(r.get('scope') or 'LAN').strip()
        cnt = int(r.get('tests') or 0)
        usr = int(r.get('users') or 1)
        aspd = float(r.get('avg_spd') or 0)
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
        est_dur = round(300.0 / max(0.1, aspd), 1) if aspd > 0 else 0.0
        ops.append({'device_id': did, 'dev_label': f"{short_os} ({usr} PC){hw_sfx}", 'net_lbl': f"{sc} ({cnt}x)", 'scope_norm': sc, 'archive': f"Avg: {aspd} MB/s • Max: {mspd} MB/s", 'mb_f': 300.0, 'dur_f': est_dur, 'spd_f': round(aspd, 2), 'net_spd_f': round(aspd, 2) if is_net else 0.0, 'avg_cpu': acpu, 'avg_disk_w': adw, 'avg_disk_r': adr, 'timestamp': f"{cnt} tests"})
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
        ops.append({'device_id': did, 'dev_label': f"{os_l}{hw_sfx}", 'net_lbl': f"Bench ({cnt}x)", 'scope_norm': 'LAN', 'archive': f"CPU: {acpu} • W: {adw} • R: {adr} MB/s", 'mb_f': 64.0, 'dur_f': 1.0, 'spd_f': 0.0, 'net_spd_f': 0.0, 'avg_cpu': acpu, 'avg_disk_w': adw, 'avg_disk_r': adr, 'timestamp': f"{cnt} bench"})
        devs.append({'device_id': did, 'label': os_l, 'is_own': False, 'total_cnt': cnt, 'sample_cnt': cnt, 'avg_dur': 1.0, 'min_dur': 1.0, 'avg_net_spd': 0.0, 'avg_spd': 0.0, 'avg_cpu': acpu, 'avg_disk_w': adw, 'avg_disk_r': adr, 'net_lbl': f"Bench • {cnt}x"})
    devs.sort(key=lambda d: -(d['avg_spd'] or max(d['avg_cpu'], d['avg_disk_w'], d['avg_disk_r'])))
    return {'ops': ops, 'devices': devs}
