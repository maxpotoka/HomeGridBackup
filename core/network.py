# patch-id: actionable-errors-and-terms-3.99c
# patch-id: confirm-modal-inverter-image-sync-3.95
# patch-id: server-inverter-image-fix-display-3.93
# patch-id: server-inverter-image-auth-3.92
# patch-id: server-inverter-image-preview-3.91
# patch-id: net-scope-adapter-3.01-p1
# [ФАЙЛ: core/network.py (v2.06 | 27.11.2026 01:18) — HTTP, PING, TCP, ВЕРИФИКАЦИЯ HGM И СКАНЕР LAN]
_W='NOT_HGM'
_V='server_history'
_U='timeout'
_T='creationflags'
_S='work'
_R='info'
_Q='ignore'
_P='_jar'
_O='warn'
_N='dirty'
_M='https'
_L='err'
_K='utf-8'
_J='nt'
_I='ok'
_H='replace'
_G='server'
_F='.'
_E='client_token'
_D=.0
_C=None
_B=False
_A=True
import json,os,re,socket,sys,time
_ORIG_CREATE_CONN=socket.create_connection
_SOCK_BUF_BYTES=0
def set_socket_buffer_kb(kb):
	global _SOCK_BUF_BYTES
	try:_SOCK_BUF_BYTES=max(0,int(kb or 0))*1024
	except(TypeError,ValueError):_SOCK_BUF_BYTES=0
def _fast_conn(addr,timeout=socket._GLOBAL_DEFAULT_TIMEOUT,source_address=_C,**B):
	A=_ORIG_CREATE_CONN(addr,timeout=timeout,source_address=source_address,**B)
	try:
		A.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
		if _SOCK_BUF_BYTES>0:A.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,_SOCK_BUF_BYTES);A.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,_SOCK_BUF_BYTES)
	except Exception:0
	return A
socket.create_connection=_fast_conn
import http.cookiejar,ipaddress,subprocess
_WIN_NO_WINDOW={_T:134217728}if os.name==_J else{}
import urllib.error,urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from core.config import DEFAULT_TOK,SILENT_MODE,apply_server_auth,commit_state
BROWSER_UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
def _seed_cookie(jar,url,name,value):
	B=value
	if not B:return
	D=urlparse(url);C=D.hostname or''
	if not C:return
	for A in list(jar):
		if A.name==name and A.domain==C:A.value=B;return
	A=http.cookiejar.Cookie(version=0,name=name,value=B,port=_C,port_specified=_B,domain=C,domain_specified=_B,domain_initial_dot=_B,path='/',path_specified=_A,secure=D.scheme==_M,expires=_C,discard=_A,comment=_C,comment_url=_C,rest={},rfc2109=_B);jar.set_cookie(A)
def invoke_http(url,state,method='GET',body=_C,origin='',ref='',timeout=1e1,send_cli=_A,send_ses=_A):
	a='hg_client=([^;]+)';Z='set-cookie';S=origin;R='hg_client';Q='session_token';K='homegrid_dash_session';I=url;A=state;T=A[_E]or DEFAULT_TOK;U=A[Q]if send_ses else'';B=A.get(_P)
	if B is _C:B=http.cookiejar.CookieJar();A[_P]=B
	if send_cli and T:_seed_cookie(B,I,R,T)
	if U:_seed_cookie(B,I,K,U)
	else:
		for C in list(B):
			if C.name==K:B.clear(C.domain,C.path,C.name)
	for V in(_A,_B):
		W=time.time()
		try:
			X=[urllib.request.HTTPCookieProcessor(B)]
			if V:X.append(urllib.request.ProxyHandler({}))
			b=urllib.request.build_opener(*X);J={'User-Agent':BROWSER_UA,'Accept':'application/json, text/html, */*','Accept-Encoding':'identity','Accept-Language':'uk-UA,uk;q=0.9,en;q=0.8'}
			if S:J['Origin']=S
			if ref:J['Referer']=ref
			Y=body.encode(_K)if body is not _C else _C
			if Y is not _C:J['Content-Type']='application/json'
			c=urllib.request.Request(I,data=Y,headers=J,method=method)
			with b.open(c,timeout=timeout)as L:
				M=L.read().decode(_K,errors=_H);N=round((time.time()-W)*1000,1);E=G=''
				for C in B:
					if C.name==K and C.value:E=C.value
					elif C.name==R and C.value:G=C.value
				for(O,H)in L.headers.items():
					if O.lower()==Z:
						if'homegrid_dash_session='in H:
							P=re.search('homegrid_dash_session=([^;]+)',H)
							if P and P.group(1).strip():E=P.group(1).strip();_seed_cookie(B,I,K,E)
						if'hg_client='in H:
							F=re.search(a,H)
							if F and F.group(1).strip():G=F.group(1).strip();_seed_cookie(B,I,R,G)
				if G and G!=A[_E]:A[_E]=G;A[_N]=_A
				if E and E!=A[Q]:A[Q]=E;A[_N]=_A
				return _A,L.status,M,E,'',N
		except urllib.error.HTTPError as D:
			N=round((time.time()-W)*1000,1);M=D.read().decode(_K,errors=_H)if D.fp else''
			if D.headers:
				for(O,H)in D.headers.items():
					if O.lower()==Z:
						F=re.search(a,H)
						if F and F.group(1).strip()!=A[_E]:A[_E]=F.group(1).strip();A[_N]=_A
			return _B,D.code,M,'',str(D),N
		except Exception as D:
			if not V:return _B,0,'','',str(D),_D
	return _B,0,'','','Помилка мережі',_D
def ping_host(host,timeout_ms=2000):
	E='ping';C=timeout_ms;F=time.time()
	try:
		if os.name==_J:A=[E,'-n','1','-w',str(C),host];B=subprocess.run(A,stdin=subprocess.DEVNULL,capture_output=_A,encoding='cp866',**_WIN_NO_WINDOW,errors=_H,timeout=4)
		else:G=max(1,int(round(C/1e3)));H='-t'if sys.platform=='darwin'else'-W';A=[E,'-c','1',H,str(G),host];B=subprocess.run(A,stdin=subprocess.DEVNULL,capture_output=_A,text=_A,errors=_H,**_WIN_NO_WINDOW,timeout=4)
		if B.returncode==0:
			D=re.search('time[=<]\\s*([\\d.,]+)\\s*ms',B.stdout or'',re.IGNORECASE)
			if D:return _A,round(float(D.group(1).replace(',',_F)),1)
			return _A,round((time.time()-F)*1000,1)
	except Exception:0
	return _B,_D
def _fmt_link_speed(mbps):
	try:v=float(mbps or 0)
	except Exception:return''
	if v<=0:return''
	if v>=1000 and int(v)%1000==0:return f"{int(v)//1000} Gbps"
	return f"{int(round(v))} Mbps"
def _classify_adapter(name,desc=''):
	s=f"{name} {desc}".lower()
	if any(k in s for k in('wireguard','openvpn','zerotier','tailscale','wintun','tap-','tun','vpn','ppp','cisco','fortinet','nordlynx'))or name.lower().startswith(('tun','tap','wg','ppp')):return'VPN'
	if any(k in s for k in('wi-fi','wifi','wlan','wireless','802.11','centrino','ath','iwlwifi','rtw','brcm'))or name.lower().startswith(('wl','wlan','wifi')):return'Wi-Fi'
	if any(k in s for k in('vethernet','hyper-v','wsl','docker','vmware','virtualbox','vbox','loopback','bridge'))or name.lower().startswith(('veth','docker','br-','virbr','lo')):return'Virtual'
	if any(k in s for k in('ethernet','gigabit','realtek','intel(r) i2','pcie gbe','lan','usb gbe'))or name.lower().startswith(('en','eth','em','p2p')):return'Ethernet'
	return'LAN'
def _probe_link_quality(host,port,is_lan):
	if not host or not is_lan:return''
	samples=list()
	for _ in range(3):
		t0=time.perf_counter()
		try:
			with socket.create_connection((host,port),timeout=1.2):samples.append((time.perf_counter()-t0)*1000.)
		except Exception:0
	if not samples:return''
	avg_ms=sum(samples)/len(samples);jit=max(samples)-min(samples)
	if avg_ms<2.2 and jit<2.5:return f"Cable/Fast LAN (~{avg_ms:.1f} ms)"
	if avg_ms<6.5 and jit<6.0:return f"Wi-Fi 5GHz / Fast (~{avg_ms:.1f} ms)"
	return f"Wi-Fi 2.4GHz / Busy (~{avg_ms:.1f} ms)"
def detect_network_adapter(target_url=''):
	local_ip,host,port,is_lan='','',18899,_B
	try:
		u=urlparse(target_url if'://'in str(target_url)else f"http://{target_url}");host=u.hostname or'';port=u.port or(443 if u.scheme==_M else 80)
		if host:
			try:ip_o=ipaddress.ip_address(host);is_lan=ip_o.is_private or ip_o.is_loopback
			except Exception:is_lan=host.lower().endswith('.local')or host.lower()in('localhost',)
		s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect((host or'8.8.8.8',port));local_ip=next(iter(s.getsockname()),'');s.close()
	except Exception:
		try:s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));local_ip=next(iter(s.getsockname()),'');s.close()
		except Exception:local_ip=''
	name,desc,atype,mbps='','','LAN',0
	try:
		if os.name==_J and local_ip:
			ps=f"$ip='{local_ip}';$a=Get-NetIPAddress -IPAddress $ip -AddressFamily IPv4 -ErrorAction SilentlyContinue|Select-Object -First 1;if($a){{$n=Get-NetAdapter -InterfaceIndex $a.InterfaceIndex -ErrorAction SilentlyContinue|Select-Object -First 1;if($n){{Write-Output ($n.Name+'|'+$n.InterfaceDescription+'|'+$n.LinkSpeed+'|'+$n.MediaType)}}}}"
			out=subprocess.check_output(('powershell','-NoProfile','-Command',ps),stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2.5,**_WIN_NO_WINDOW).decode(_K,errors=_H).strip()
			if'|'not in out:
				out=subprocess.check_output(('wmic','nic','where','NetEnabled=true','get','Name,NetConnectionID,Speed','/format:csv'),stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2.5,**_WIN_NO_WINDOW).decode(_K,errors=_H)
				for ln in out.splitlines():
					cs=dict(enumerate(ln.split(',')))
					if len(cs)>=4 and cs.get(3,'').strip().isdigit():name=cs.get(2,'').strip();desc=cs.get(1,'').strip();mbps=max(1,int(int(cs.get(3,'0'))//1000000));atype=_classify_adapter(name,desc);break
			if'|'in out:
				pd=dict(enumerate(out.split('|')));name=pd.get(0,'').strip();desc=pd.get(1,'').strip();ls=pd.get(2,'').strip();mt=pd.get(3,'').strip()
				m=re.search('(\\d+(?:\\.\\d+)?)\\s*(Gbps|Mbps|Kbps)',ls,re.I)
				if m:
					val=float(m.group(1));un=m.group(2).lower()
					mbps=int(round(val*1000))if un=='gbps'else int(round(val))if un=='mbps'else max(1,int(round(val/1000)))
				atype=_classify_adapter(name,f"{desc} {mt}")
		elif sys.platform.startswith('linux')and local_ip:
			out=subprocess.check_output(('ip','-4','-o','addr','show'),stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1.5).decode(_K,errors=_H)
			for ln in out.splitlines():
				if f" {local_ip}/"in ln:
					pts=ln.split()
					if len(pts)>=2:name=dict(enumerate(pts)).get(1,'').partition('@').__getitem__(0);break
			if name:
				if os.path.isdir(f"/sys/class/net/{name}/wireless"):atype='Wi-Fi'
				else:atype=_classify_adapter(name)
				try:
					with open(f"/sys/class/net/{name}/speed",'r')as f:sp=int(f.read().strip())
					if sp>0:mbps=sp
				except Exception:0
				if mbps<=0 and atype=='Wi-Fi':
					try:
						iw=subprocess.check_output(('iw','dev',name,'link'),stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1.2).decode(_K,errors=_H)
						m=re.search('tx bitrate:\\s*(\\d+(?:\\.\\d+)?)\\s*MBit/s',iw,re.I)
						if m:mbps=int(round(float(m.group(1))))
					except Exception:0
		elif sys.platform=='darwin'and local_ip:
			out=subprocess.check_output(('ifconfig',),stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1.5).decode(_K,errors=_H)
			cur=''
			for ln in out.splitlines():
				if ln and not ln.isspace()and':'in ln:cur=ln.partition(':').__getitem__(0)
				elif f"inet {local_ip} "in ln and cur:name=cur;break
			if name:
				atype=_classify_adapter(name)
				try:
					med=subprocess.check_output(('ifconfig',name),stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1.2).decode(_K,errors=_H)
					m=re.search('(\\d+)baseT',med,re.I)
					if m:mbps=int(m.group(1))
				except Exception:0
	except Exception:0
	spd_s=_fmt_link_speed(mbps);lbl=f"{atype} • {spd_s}"if spd_s else(atype if(name or local_ip)else'');scope='LAN'if is_lan else'Internet';srv_est=_probe_link_quality(host,port,is_lan);srv_disp=f"{host}:{port}"if host else'';return{'ip':local_ip,'name':name,'desc':desc or name,'type':atype,'link_mbps':mbps,'link_str':spd_s,'label':lbl,'scope':scope,'srv_host':srv_disp,'srv_conn_est':srv_est}
def test_tcp_port(host,port,timeout=2.5):
	A=time.time()
	try:
		with socket.create_connection((host,port),timeout=timeout):return _A,round((time.time()-A)*1000,1)
	except Exception:return _B,_D
def _tcp_probe(host,port,timeout):
	A=time.time()
	try:
		with socket.create_connection((host,port),timeout=timeout):return'open',round((time.time()-A)*1000,1)
	except TimeoutError:return _U,_D
	except ConnectionRefusedError:return'refused',_D
	except OSError:return'error',_D
def _os_gateway_and_arp():
	F='arp';E='route'
	if sys.platform.startswith('linux'):return _linux_proc_net_hints()
	C,D=[],[];B=dict(stdin=subprocess.DEVNULL,capture_output=_A,text=_A,errors=_H,**_WIN_NO_WINDOW,timeout=3)
	if os.name==_J:B[_T]=134217728
	try:
		if os.name==_J:A=subprocess.run([E,'print','0.0.0.0'],**B).stdout or'';C=re.findall('^\\s*0\\.0\\.0\\.0\\s+0\\.0\\.0\\.0\\s+(\\d+\\.\\d+\\.\\d+\\.\\d+)',A,re.MULTILINE);A=subprocess.run([F,'-a'],**B).stdout or'';D=re.findall('^\\s*(\\d+\\.\\d+\\.\\d+\\.\\d+)\\s+[0-9a-fA-F-]{17}\\s+dynamic',A,re.MULTILINE|re.IGNORECASE)
		else:A=subprocess.run([E,'-n','get','default'],**B).stdout or'';C=re.findall('gateway:\\s*(\\d+\\.\\d+\\.\\d+\\.\\d+)',A);A=subprocess.run([F,'-an'],**B).stdout or'';D=re.findall('\\((\\d+\\.\\d+\\.\\d+\\.\\d+)\\) at ',A)
	except Exception:0
	return C,D
def test_hgm_stage2(base_url,state,timeout=6.):
	E=timeout;D=state;C=base_url;I=int(time.time()*1000);J,K,F,A,A,G=invoke_http(f"{C}/api/auth/status?_t={I}",D,timeout=E,send_cli=_A,send_ses=_B)
	if J and K==200 and F:
		try:
			H=json.loads(F)
			if isinstance(H,dict)and isinstance(H.get('authenticated'),bool):return _A,G
		except Exception:0
	A,L,B,A,A,M=invoke_http(f"{C}/login",D,timeout=E,send_cli=_A,send_ses=_B)
	if L==200 and B:
		N=bool(re.search('HomeGrid\\s+Monitor',B,re.IGNORECASE));O=bool(re.search('PV\\s+аналітики|PIN-захист|hg_client|DashboardPanelHeader',B,re.IGNORECASE))
		if N and O:return _A,M or G
	return _B,_D
def _linux_proc_net_hints():
	G='00000000';C,D=[],[]
	if os.name==_J:return C,D
	try:
		with open('/proc/net/route','r',encoding=_K,errors=_Q)as B:
			next(B,_C)
			for E in B:
				A=E.split()
				if len(A)>=3 and A[1]==G and A[2]!=G:
					F=socket.inet_ntoa(int(A[2],16).to_bytes(4,'little'))
					if F not in C:C.append(F)
	except Exception:0
	try:
		with open('/proc/net/arp','r',encoding=_K,errors=_Q)as B:
			next(B,_C)
			for E in B:
				A=E.split()
				if len(A)>=4 and A[2]!='0x0':D.append(A[0])
	except Exception:0
	return C,D
def _local_ipv4_with_prefix():
	A=[]
	if os.name==_J:return A
	try:
		D=subprocess.run(['ip','-4','-o','addr','show'],stdin=subprocess.DEVNULL,capture_output=_A,text=_A,errors=_H,timeout=3).stdout or''
		for E in D.splitlines():
			B=re.search('inet (\\d+\\.\\d+\\.\\d+\\.\\d+)/(\\d+)',E)
			if B:A.append((B.group(1),int(B.group(2))))
	except Exception:0
	if not A:
		try:
			D=subprocess.run(['ifconfig'],stdin=subprocess.DEVNULL,capture_output=_A,text=_A,errors=_H,timeout=3).stdout or''
			for B in re.finditer('inet (?:addr:)?(\\d+\\.\\d+\\.\\d+\\.\\d+)\\s+(?:netmask|Mask:)\\s*(0x[0-9a-fA-F]+|\\d+\\.\\d+\\.\\d+\\.\\d+)',D):
				C=B.group(2)
				if C.startswith('0x'):C=str(ipaddress.IPv4Address(int(C,16)))
				A.append((B.group(1),ipaddress.IPv4Network('0.0.0.0/'+C).prefixlen))
		except Exception:0
	F,H=_os_gateway_and_arp()
	for G in F:A.append((G,24))
	return A
def get_main_subnets(state=_C):
	P='192.168.';O='8.8.8.8';K='172.';F=state;B=set();L=_B
	def G(ip_str,plen=24):
		A=ip_str;nonlocal L
		try:
			C=ipaddress.IPv4Address(A)
			if not C.is_private or C.is_loopback or C.is_link_local:return
			if A.startswith(K):L=_A
			if 22<=plen<24:
				for D in ipaddress.IPv4Network(f"{A}/{plen}",strict=_B).subnets(new_prefix=24):B.add(str(D.network_address).rsplit(_F,1)[0])
			else:E=ipaddress.IPv4Network(f"{A}/24",strict=_B);B.add(str(E.network_address).rsplit(_F,1)[0])
		except ValueError:0
	for(H,Q)in _local_ipv4_with_prefix():G(H,Q)
	I=[]
	try:
		for R in socket.getaddrinfo(socket.gethostname(),_C,socket.AF_INET):J,J,J,J,S=R;I.append(S[0])
	except Exception:0
	try:A=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);A.connect((O,80));I.append(A.getsockname()[0]);A.close()
	except Exception:0
	for H in I:G(H,24)
	if isinstance(F,dict):
		T=[F.get(_G,'')]+list(F.get(_V)or[])
		for C in T:
			try:
				C=(C or'').strip().rstrip('!')
				if not C:continue
				M=urlparse(C if'://'in C else'http://'+C).hostname
				if M:G(M,24)
			except Exception:continue
	D=[]
	try:
		A=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);A.connect((O,80));N=A.getsockname()[0];A.close()
		if not N.startswith(K):D.append(N.rsplit(_F,1)[0])
	except Exception:0
	from core.config import IS_WSL as U
	if U:
		try:
			V=subprocess.check_output(['powershell.exe','-NoProfile','-Command','(Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null}).IPv4Address.IPAddress'],stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1.5,**_WIN_NO_WINDOW).decode(_K,errors=_Q)
			for E in re.findall('\\b(\\d+\\.\\d+\\.\\d+)\\.\\d+\\b',V):
				if not E.startswith(K):
					B.add(E)
					if E not in D:D.append(E)
		except Exception:0
		if not any(A.startswith(P)for A in B):B.update(('192.168.0','192.168.1'))
	def W(pref):
		A=pref
		if A in D:return 0,D.index(A),A
		if A.startswith(P):return 1,0,A
		if A.startswith('10.'):return 2,0,A
		return 3,0,A
	return sorted(B,key=W)
def normalize_server_url(raw):
	G='^\\d{1,3}(\\.\\d{1,3}){3}$';A=(raw or'').strip();B='!'in A;A=A.replace('!','').strip().rstrip('/')
	if not A:return'',B
	if'://'not in A and _F not in A and':'not in A and A.lower()!='localhost':return f"https://{A}.homegridmonitor.com",B
	if not re.match('^https?://',A,re.IGNORECASE):F,H,H=A.partition(':');E=bool(re.match(G,F));A=f"http://{A}"if E or _F not in F else f"https://{A}"
	D=urlparse(A);C=D.hostname or''
	if not C:return'',B
	if D.port:return f"{D.scheme.lower()}://{C}:{D.port}",B
	if D.scheme.lower()==_M:return f"https://{C}",B
	E=bool(re.match(G,C))
	if E or _F not in C:return f"http://{C}:18899",B
	return f"http://{C}",B
def verify_host_and_hgm(engine,srv_url):
	E=srv_url;C=engine;D=urlparse(E);A=D.hostname or'';B=D.port or(443 if D.scheme==_M else 80)
	try:socket.getaddrinfo(A,B)
	except socket.gaierror:return _B,'DNS_FAIL',f"\u0421\u0430\u0439\u0442/\u0434\u043e\u043c\u0435\u043d '{A}' \u043d\u0435 \u0437\u043d\u0430\u0439\u0434\u0435\u043d\u043e (\u043f\u043e\u043c\u0438\u043b\u043a\u0430 DNS). \u041f\u0435\u0440\u0435\u0432\u0456\u0440\u0442\u0435 \u0430\u0434\u0440\u0435\u0441\u0443, \u0432\u0456\u0434\u0441\u0443\u0442\u043d\u0456\u0441\u0442\u044c \u043e\u043f\u0438\u0441\u043e\u043a \u0430\u0431\u043e \u043c\u0435\u0440\u0435\u0436\u0443.",_D,_D
	F,G=ping_host(A,2000)
	if F:C.log(f"ICMP Ping до {A}: {G} мс",_R)
	else:C.log(f"ICMP Ping до {A} без відповіді, перевірка з'єднання ({B})...",_O)
	I,H=test_tcp_port(A,B,3.5)
	if not I:return _B,'TCP_FAIL',f"\u0425\u043e\u0441\u0442 '{A}' \u0456\u0441\u043d\u0443\u0454, \u0430\u043b\u0435 \u043f\u043e\u0440\u0442 {B} \u0437\u0430\u043a\u0440\u0438\u0442\u0438\u0439 \u0430\u0431\u043e \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0438\u0439. \u041f\u0435\u0440\u0435\u0432\u0456\u0440\u0442\u0435 \u043f\u043e\u0440\u0442, \u043c\u0435\u0440\u0435\u0436\u0443 \u0430\u0431\u043e \u0447\u0438 \u0437\u0430\u043f\u0443\u0449\u0435\u043d\u043e \u0441\u0435\u0440\u0432\u0435\u0440 HGM.",_D,_D
	J,K=test_hgm_stage2(E,C.state,7.)
	if not J:return _B,_W,f"Сайт '{A}' доступний, але це НЕ сервер HomeGrid Monitor!",H,_D
	return _A,'OK',f"{A}:{B}",G if F else H,K
def scan_lan_servers(engine):
	A=engine;B=get_main_subnets(A.state)
	if not B:A.log('Активні мережеві адаптери LAN не знайдено!',_L);return[]
	A.log('Сканування підмереж: '+', '.join(f"{A}.0/24"for A in B),_R);C=[]
	with A.lock:F=dict(A.state)
	P,Q=_os_gateway_and_arp();D=set(Q)
	for R in[F.get(_G,'')]+list(F.get(_V)or[]):
		K=urlparse((R or'').strip().rstrip('!')).hostname
		if K:D.add(K)
	S={A.rsplit(_F,1)[0]for A in P};T=[A for A in B if A in S]or B[:1];E=[]
	for L in B:
		G=[f"{L}.{A}"for A in range(1,255)]
		if L in T:E+=[A for A in G if A in D]+[A for A in G if A not in D]
		else:E+=[A for A in G if A in D]
	A.set_progress(_C,f"Сканування {len(E)} адрес...")
	try:
		H=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);H.setblocking(_B)
		for U in E:
			try:H.sendto(b'\x00',(U,9))
			except Exception:0
		H.close();time.sleep(.3)
	except Exception:0
	def V(ip_addr):
		B=ip_addr
		try:
			C,G=_tcp_probe(B,18899,.85)
			if C==_U and B in D:C,G=_tcp_probe(B,18899,1.5)
			if C!='open':return
			E=dict(F);E[_P]=_C;H,I=test_hgm_stage2(f"http://{B}:18899",E,timeout=5.)
			if H:return B,E.get(_E,''),G,I
			A.log(f"[TRACE] {B}:18899 TCP відкрито, API не відповів",_O)
		except Exception:return
	with ThreadPoolExecutor(max_workers=32)as W:
		for M in W.map(V,E):
			if M:
				I,J,N,O=M
				if not any(A==I for(A,B,B)in C):
					C.append((I,N,O));X=f"http://{I}:18899";A.discovered_servers=[(f"http://{A}:18899",B,C)for(A,B,C)in C];A.log(f"Знайдено сервер: {X} (TCP: {N} мс, API: {O} мс)",_I);A.set_pill(f"Знайдено: {len(C)}",_S)
					if J and J!=A.state[_E]:A.state[_E]=J;A.state[_N]=_A
	return C
def fetch_server_inverter_image(engine, srv_url, wait_timeout=0.0):
	import threading
	def _worker():
		try:
			base = (srv_url or '').strip().rstrip('!').rstrip('/')
			if not base:
				return
			apply_server_auth(engine.state, base)
			pin_v = (engine.state.get('login_pin') or '').strip()
			if pin_v and not (engine.state.get('session_token') or '').strip():
				ok_l, _, _, ses_l, _, _ = invoke_http(f"{base}/api/auth/login", engine.state, 'POST', json.dumps({'pin': pin_v}), base, f"{base}/login", 8.0, send_ses=_B)
				if ok_l and ses_l:
					engine.state['session_token'] = ses_l
					commit_state(engine.state)
			inv_id = ''
			for ep in ('/api/inverters', '/api/status', '/api/mini-dashboard'):
				ok, st_c, body, _, _, _ = invoke_http(f"{base}{ep}", engine.state, timeout=6.0)
				if ok and st_c == 200 and body:
					m_id = re.search(r'"(?:selected_inverter_id|inverter_id|default_inverter_id|active_inverter_id)"\s*:\s*"([0-9a-fA-F-]{8,64})"', body)
					if not m_id:
						m_id = re.search(r'inverter_id=([0-9a-fA-F-]{8,64})', body)
					if not m_id:
						m_id = re.search(r'"id"\s*:\s*"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"', body)
					if m_id:
						inv_id = m_id.group(1).strip()
						break
			img_url = f"{base}/api/mini-dashboard/inverter-image?inverter_id={inv_id}" if inv_id else f"{base}/api/mini-dashboard/inverter-image"
			jar = engine.state.get(_P)
			if jar is _C:
				jar = http.cookiejar.CookieJar()
				engine.state[_P] = jar
			cli_t = engine.state.get(_E) or DEFAULT_TOK
			ses_t = engine.state.get('session_token') or ''
			if cli_t:
				_seed_cookie(jar, img_url, 'hg_client', cli_t)
			if ses_t:
				_seed_cookie(jar, img_url, 'homegrid_dash_session', ses_t)
			raw_bytes = b''
			for no_px in (_A, _B):
				try:
					hds = [urllib.request.HTTPCookieProcessor(jar)]
					if no_px:
						hds.append(urllib.request.ProxyHandler({}))
					op = urllib.request.build_opener(*hds)
					req = urllib.request.Request(img_url, headers={'User-Agent': BROWSER_UA, 'Accept': 'image/png,image/webp,image/jpeg,image/gif,*/*'})
					with op.open(req, timeout=8.0) as resp:
						ctype = (resp.headers.get('Content-Type') or '').lower()
						data = resp.read(2097152)
						if data and ('image/' in ctype or data[:8] == b'\x89PNG\r\n\x1a\n' or data[:3] == b'\xff\xd8\xff' or data[:4] == b'RIFF' or data[:6] in (b'GIF87a', b'GIF89a')):
							raw_bytes = data
							break
				except Exception:
					pass
			with engine.lock:
				engine.server_logo_bytes = raw_bytes if raw_bytes else _C
				engine.server_logo_url = base if raw_bytes else ''
				engine.server_logo_sig = (base, len(raw_bytes)) if raw_bytes else _C
		except Exception:
			with engine.lock:
				engine.server_logo_bytes = _C
				engine.server_logo_sig = _C
	_th = threading.Thread(target=_worker, daemon=_A)
	_th.start()
	if wait_timeout and wait_timeout > 0:
		_th.join(timeout=wait_timeout)


def run_connect_task(engine,raw_url,force_skip=_B):
	A=engine;from core.backup import run_backup_task as L
	if A.is_running:return
	A.is_running=_A;A.set_pill('Підключення...',_S);E=_B
	try:
		B,M=normalize_server_url(raw_url);H=force_skip or M
		if not B:A.log('Введіть IP-адресу або домен сайту перед підключенням!',_O);A.set_pill('Не вказано адресу',_L);return
		F=urlparse(B);C=F.hostname or B;D=F.port or(443 if F.scheme==_M else 18899)
		if H:A.state[_G]=B;commit_state(A.state);A.diag_net=f"{C}:{D} (БЕЗ ПЕРЕВІРКИ)";A.diag_ping='Пропущено';A.set_pill('Збережено (!)',_I);A.log(f"Адресу збережено без перевірки: {B}",_O);A.set_progress(100,'Сервер збережено');E=_A
		else:
			A.set_progress(_C,f"Перевірка сайту та HGM ({C}:{D})...");N,I,J,K,G=verify_host_and_hgm(A,B)
			if not N:A.log(J,_L);A.diag_net=f"{C}:{D} ({I})";A.diag_ping='Помилка перевірки';A.set_pill('Не є сервером HGM'if I==_W else'Сайт недоступний',_L);A.set_progress(0,J);return
			A.state[_G]=B;commit_state(A.state);A.diag_net=f"{C}:{D} (ОНЛАЙН)";A.diag_ping=f"TCP {K} мс | API {G} мс";A.set_pill(f"ОНЛАЙН | {G} мс",_I);A.log(f"Підключено до HomeGrid Monitor: {B} (TCP: {K} мс, API: {G} мс)",_I);A.set_progress(100,'Підключення успішне');E=_A
	finally:
		with A.lock:A.is_running=_B;A.indeterminate=_B
	if E:
		fetch_server_inverter_image(A,A.state[_G],wait_timeout=0.0 if SILENT_MODE else 1.8)
	if E and not SILENT_MODE:
		if A.ask_modal('confirm','Сервер підключено',f"Успішно підключено до {A.state[_G]}. Виконати резервне копіювання зараз?"):L(A,A.state[_G],H)
def run_scan_task(engine):
	J='backup';A=engine;from core.backup import run_backup_task as K
	if A.is_running:return
	A.is_running=_A;A.set_pill('Пошук в LAN...',_S);C=[]
	try:
		B=scan_lan_servers(A)
		if not B:A.log('Сервери HomeGrid Monitor у мережі не знайдено.',_L);A.set_pill('Не знайдено',_L);A.set_progress(0,'Сервер не знайдено')
		else:
			C=[(f"http://{A}:18899",B,C)for(A,B,C)in B];A.discovered_servers=C;F,L,G=B[0];H=f"http://{F}:18899";A.state[_G]=H;A.diag_net=f"{F}:18899 (ОНЛАЙН)";A.diag_ping=f"TCP {L} мс | API {G} мс"
			if len(B)==1:A.set_pill(f"ОНЛАЙН | {G} мс",_I);A.set_progress(100,f"Знайдено сервер: {H}")
			else:A.log(f"Сканування завершено. Всього знайдено серверів: {len(B)} шт.",_R);A.set_pill(f"Знайдено: {len(B)}",_I);A.set_progress(100,f"Знайдено {len(B)} серверів у мережі")
	finally:
		with A.lock:A.is_running=_B;A.indeterminate=_B
	if C and not SILENT_MODE:
		E=A.ask_modal('lan_found','Виявлені сервери в мережі','',default_val=C)
		if isinstance(E,dict):
			D=E.get('url','');I=E.get('action','')
			if D:
				A.state[_G]=D
				if I in('save',J):commit_state(A.state);A.log(f"Сервер {D} збережено у «Історія».",_I)
				if I==J:K(A,D,_B)
