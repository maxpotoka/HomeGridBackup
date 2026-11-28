# patch-id: compact-archive-name-hgb-4.10
# patch-id: gfs-scan-cache-2.07
# [ФАЙЛ: core/gfs.py (v2.10 | 28.11.2026 07:30) — ПЛАНИРОВЩИК GFS, ЗАЩИТА KEEP И РОТАЦИЯ КОПИЙ]
_I='(^|_)KEEP(_|\\.)'
_H='new_tag'
_G='backup_dir'
_F='utf-8'
_E='name'
_D='.sha256'
_C=False
_B=True
_A='path'
import os,re
from datetime import datetime
from core.files import format_backup_dt,parse_backup_dt,remove_backup_file
_GFS_PLAN_CACHE={}
def compute_gfs_plan(state):
	H=state;F=H[_G];os.makedirs(F,exist_ok=_B);I=max(1,int(H.get('keep_last_count',5)));D=[]
	try:
		with os.scandir(F)as Q:
			for B in Q:
				if B.name.startswith('.')or not B.name.lower().endswith(('.zip','.tar.zst')):continue
				if not(B.is_file(follow_symlinks=_C)and(B.name.startswith('hgb_')or'KEEP'in B.name)):continue
				J=B.stat(follow_symlinks=_C);D.append((B.name,J.st_size,J.st_mtime_ns))
	except Exception:D=[]
	D.sort(key=lambda item:item[0]);K=os.path.normcase(os.path.abspath(F)),I,tuple(D);L=_GFS_PLAN_CACHE.get(K)
	if L is not None:return L
	C=[]
	for(G,R,S)in D:T=os.path.join(F,G);M=parse_backup_dt(G,S/1e9);C.append({_A:T,_E:G,'size':R,'dt_str':M.strftime('%Y-%m-%d %H:%M'),'dt':M})
	C.sort(key=lambda x:x['dt'],reverse=_B);E={}
	for A in C:
		if re.search(_I,A[_E]):E[A[_A]]='KEEP'
	U=[A for A in C if A[_A]not in E]
	for A in U[:I]:E[A[_A]]='DAILY'
	N,O=[],[]
	for A in C:
		if A[_A]in E:A[_H]=E[A[_A]];N.append(A)
		else:A[_H]='DELETE';O.append(A)
	P=C,N,O;_GFS_PLAN_CACHE[K]=P
	if len(_GFS_PLAN_CACHE)>16:_GFS_PLAN_CACHE.pop(next(iter(_GFS_PLAN_CACHE)))
	return P
def toggle_keep_tag(state,filename):
	G=state[_G];A=os.path.basename(filename or'');C=os.path.join(G,A)
	if not A or not os.path.isfile(C):return _C,''
	if A.startswith('hgb_KEEP_'):B='hgb_'+A[9:]
	elif A.startswith('hgb_'):B='hgb_KEEP_'+A[4:]
	else:B='hgb_KEEP_'+A
	D=os.path.join(G,B)
	if D!=C and not os.path.exists(D):
		os.replace(C,D);E=C+_D
		if os.path.exists(E):
			H=D+_D
			try:
				with open(E,'r',encoding=_F)as F:J=next(iter(F.read().split()),'')
				with open(H,'w',encoding=_F)as F:F.write(f"{J}  {B}\n")
				os.remove(E)
			except Exception:os.replace(E,H)
		return _B,B
	return _C,A
def apply_gfs_cleanup(engine,skip_prompt=_C,sync_cloud=_B):
	W='permanent';A=engine;e,N,B=compute_gfs_plan(A.state);O=A.state[_G];G=A.state.get('delete_mode','trash');P=0
	for D in range(0,len(N),25):
		F=N[D:D+25]
		for C in F:
			K=C[_A];H=K+_D;Q=C[_H];R=format_backup_dt(C['dt']);ext_f='.tar.zst'if C[_E].lower().endswith('.tar.zst')else'.zip';_pfx='hgb_KEEP_'if Q=='KEEP'else'hgb_';E=f"{_pfx}{R}{ext_f}";I=os.path.join(O,E)
			if C[_E]!=E:
				if os.path.exists(I):X=datetime.fromtimestamp(os.path.getmtime(K)).strftime('%f')[:2];E=f"{_pfx}{R}_{X}{ext_f}";I=os.path.join(O,E)
				if C[_E]!=E:
					os.replace(K,I)
					if os.path.exists(H):
						S=I+_D
						try:
							with open(H,'r',encoding=_F)as L:Y=next(iter(L.read().split()),'')
							with open(S,'w',encoding=_F)as L:L.write(f"{Y}  {E}\n")
							os.remove(H)
						except Exception:os.replace(H,S)
					P+=1
	J=0;M=round(sum(A['size']for A in B)/1048576.,1);T=not B
	if B:
		Z='Видалити назавжди з диска'if G in(W,'direct') else'Перемістити у Кошик';a=_B if skip_prompt else A.ask_modal('confirm','Очищення старих бекапів',f"{Z} {len(B)} застарілих копій ({M} МБ)?")
		if a:
			U=25
			for D in range(0,len(B),U):
				F=B[D:D+U]
				for C in F:
					if remove_backup_file(C[_A],G):
						J+=1;V=C[_A]+_D
						if os.path.exists(V):remove_backup_file(V,G)
				A.set_progress(min(100,int((D+len(F))*100/len(B))),f"Ротація GFS: {min(D+len(F),len(B))}/{len(B)}")
			T=J==len(B);b='Видалено з диска назавжди'if G in(W,'direct') else'Переміщено у Кошик';A.log(f"{b}: {J} файл(ів) ({M} МБ).",'ok')
		else:A.log('Очищення застарілих архівів пропущено.','info')
	if sync_cloud and A.state.get('cloud_enabled'):
		try:from core.cloud import sync_cloud_backups as c;c(A,prune=T)
		except Exception as d:A.log(f"Попередження: не вдалося синхронізувати хмарне дзеркало GFS: {d}",'warn')
	return J,P,M
