# patch-id: pcloud-speed-progress-gradient-2.33
# patch-id: linux-wayland-sni-bridge-2.32
# patch-id: linux-xorg-tray-menu-2.26
# patch-id: macos-tray-quit-apps-2.41
# patch-id: cumulative-linux-tray-pcloud-menu-2.42
# patch-id: fix-linux-tray-menu-2.76
# [ФАЙЛ: gui/tray.py (v2.10 | 24.11.2026 09:25)
# patch-id: macos-quit-and-buttons-2.17
_j='✖ Вихід'
_i='Налаштування'
_h='Аналіз GFS / SHA-256'
_g='Журнал операцій'
_f='Статистика'
_e='Відкрити папку'
_d='▶ Запустити резервне копіювання'
_c='Відкрити HomeGrid Backup'
_b='backup_dir'
_a='server'
_Z='pystray'
_Y='ignore'
_X='DESKTOP_SESSION'
_W='XDG_CURRENT_DESKTOP'
_V='RGBA'
_U='idle'
_T='WAYLAND_DISPLAY'
_S='en'
_R='lang'
_Q='darwin'
_P='err'
_O='warn'
_N='gtk'
_M='sni-bridge'
_L='appindicator'
_K='utf-8'
_J='auto'
_I='xorg'
_H='DBUS_SESSION_BUS_ADDRESS'
_G='DISPLAY'
_F='linux'
_E='none'
_D='info'
_C=False
_B=True
_A=None
import ctypes,os,queue as _queue_mod,threading,time
_TRAY_UI_QUEUE=_queue_mod.SimpleQueue()
def _enqueue_tray_ui(fn):
	if callable(fn):_TRAY_UI_QUEUE.put(fn)
def drain_tray_ui_queue():
	while _B:
		try:A=_TRAY_UI_QUEUE.get_nowait()
		except Exception:break
		try:A()
		except Exception:0
def _linux_tray_diag_line():A=os.environ.get('XDG_SESSION_TYPE','?');B=os.environ.get(_W)or os.environ.get(_X)or'?';C=os.environ.get(_G,'-');D=os.environ.get(_T,'-');E='yes'if os.environ.get(_H)else'no';return f"[TRAY DIAG] OS=Linux | session={A} | DE={B} | DISPLAY={C} | WAYLAND={D} | DBUS={E} | backend={_LNX_TRAY_BE or _E}"
def _clean_sys_env():
	F='unix:path=';E='LD_LIBRARY_PATH';D='LD_LIBRARY_PATH_ORIG';A=os.environ.copy();A['LC_ALL']='C'
	if D in A:A[E]=A[D]
	else:A.pop(E,_A)
	if hasattr(os,'getuid'):
		C=f"/run/user/{os.getuid()}/bus";B=A.get(_H,'')
		if os.path.exists(C)and(not B or F in B and not os.path.exists(B.split(F,1)[1].split(',',1)[0])):A[_H]=f"unix:path={C}";os.environ[_H]=A[_H]
	return A
def _has_appindicator_gi():
	try:
		import gi
		for A in('AyatanaAppIndicator3','AppIndicator3'):
			try:gi.require_version(A,'0.1');__import__(f"gi.repository.{A}");return _B
			except Exception:0
	except Exception:0
	return _C
def _has_gtk_gi():
	try:import gi;gi.require_version('Gtk','3.0');from gi.repository import Gtk;return Gtk is not _A
	except(ImportError,ValueError):return _C
def _has_sni_watcher(env):
	H='org.kde.StatusNotifierWatcher';G='call';F='org.freedesktop.DBus.NameHasOwner';E='--session';C='org.freedesktop.DBus';B='/org/freedesktop/DBus';import re,shutil as I,subprocess as A;J=('dbus-send',[E,'--dest=org.freedesktop.DBus','--type=method_call','--print-reply',B,F,'string:org.kde.StatusNotifierWatcher']),('gdbus',[G,E,'--dest',C,'--object-path',B,'--method',F,H]),('busctl',['--user',G,C,B,C,'NameHasOwner','s',H])
	for(D,K)in J:
		if not I.which(D,path=env.get('PATH')):continue
		try:
			L=A.check_output([D,*K],env=env,stderr=A.DEVNULL,timeout=.9).decode(_K,errors=_Y)
			if re.search('\\btrue\\b',L,re.IGNORECASE):return _B
		except(OSError,A.SubprocessError):continue
	return _C
def _has_x11_tray_manager():
	if not os.environ.get(_G):return _C
	try:
		from ctypes.util import find_library as E;C=E('X11')
		if not C:return _C
		A=ctypes.CDLL(C)
	except OSError:return _C
	A.XOpenDisplay.argtypes=[ctypes.c_char_p];A.XOpenDisplay.restype=ctypes.c_void_p;A.XDefaultScreen.argtypes=[ctypes.c_void_p];A.XDefaultScreen.restype=ctypes.c_int;A.XInternAtom.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int];A.XInternAtom.restype=ctypes.c_ulong;A.XGetSelectionOwner.argtypes=[ctypes.c_void_p,ctypes.c_ulong];A.XGetSelectionOwner.restype=ctypes.c_ulong;A.XCloseDisplay.argtypes=[ctypes.c_void_p];A.XCloseDisplay.restype=ctypes.c_int;B=A.XOpenDisplay(os.environ[_G].encode(_K))
	if not B:return _C
	try:F=A.XDefaultScreen(B);G=f"_NET_SYSTEM_TRAY_S{F}".encode('ascii');D=A.XInternAtom(B,G,0);return bool(D and A.XGetSelectionOwner(B,D))
	finally:A.XCloseDisplay(B)
def _detect_linux_tray_backend():
	B='GI_TYPELIB_PATH';import sys
	if not sys.platform.startswith(_F):return'native'
	from core.config import IS_WSL as C
	if C or not os.environ.get(_G)and not os.environ.get(_T):return''
	if not getattr(sys,'frozen',_C):
		for A in('/usr/lib/x86_64-linux-gnu/girepository-1.0','/usr/lib/i386-linux-gnu/girepository-1.0','/usr/lib/aarch64-linux-gnu/girepository-1.0','/usr/lib/girepository-1.0'):
			if os.path.isdir(A)and A not in os.environ.get(B,''):os.environ[B]=f"{A}:{os.environ.get(B,"")}".rstrip(':')
	D=_clean_sys_env()
	if _has_sni_watcher(D):return _L if _has_appindicator_gi()else _M
	if _has_x11_tray_manager():return _N if _has_gtk_gi()else _I
	return''
_LNX_TRAY_BE=''
_LNX_TRAY_PROBED=_C
_LNX_PROBE_LOCK=threading.Lock()
try:import pystray;from PIL import Image,ImageDraw,ImageFont;HAS_TRAY=_B
except Exception:pystray=_A;Image=_A;ImageDraw=_A;ImageFont=_A;HAS_TRAY=_C
_TRAY_LOCK=threading.Lock()
_TRAY_STARTED=_C
_TRAY_STOP=threading.Event()
_LINUX_TRAY_MODES=_J,_L,_M,_N,_I,_E
_MAC_TRAY_MODES=_J,_Z,_E
TRAY_MODE_HINTS={_L:'Ubuntu/GNOME/XFCE с AppIndicator: нужен пакет gir1.2-ayatanaappindicator3-0.1. Значок должен появиться в верхней панели.',_M:'Wayland или панель StatusNotifier без доступного gi: используется системный /usr/bin/python3. Смотрите строку «AppIndicator bridge» в логе.',_N:'X11: Tkinter-меню внутри окна/панели, запасной вариант, если нет AppIndicator.',_I:'Классический XEmbed-трей: работает только на панелях с X11 System Tray.',_E:'Трей выключен, программа работает без значка.',_Z:'macOS: значок в верхнем Menu Bar через pystray. Если значка нет, смотрите «[TRAY DETAIL]» в логе.'}
def _requested_tray_backend(engine):
	B=engine;A=str(B.state.get('tray_backend',_J)or _J).strip().lower();C=_LINUX_TRAY_MODES if os.sys.platform.startswith(_F)else _MAC_TRAY_MODES
	if A in('',_J):return''
	if A not in C:B.log(f"[TRAY MODE] невідомий режим '{A}', використано auto",_O);return''
	return A
def _status_gradient_rgb(pct,is_run,pill_type):
	C=pill_type
	if C==_P:return 239,68,68,255
	if C==_O:return 245,158,11,255
	if not is_run:return 16,185,129,255
	B=max(.0,min(1.,float(pct)/1e2))
	if B<=.5:A=B/.5;return int(16+-2*A),int(185+-20*A),int(129+104*A),255
	A=(B-.5)/.5;return int(14+231*A),int(165+-7*A),int(233+-222*A),255
def _show_wayland_fallback_badge(engine):
	A=engine;import sys,tkinter as E
	if not sys.platform.startswith(_F)or A.app_ref is _A:return
	C=A.app_ref
	if getattr(C,'_wl_badge',_A)is not _A:return
	try:
		B=E.Toplevel(C.root);B.wm_overrideredirect(_B);B.attributes('-topmost',_B);D=E.Label(B,text='● HomeGrid',fg='#ffffff',bg='#10b981',font=('Ubuntu',9,'bold'),padx=10,pady=4,cursor='hand2');D.pack();D.bind('<Button-1>',lambda _e:C.show_window());B.geometry('+14+38');C._wl_badge=B
		def F():
			if not B.winfo_exists():return
			C,E,G,J=_status_gradient_rgb(A.progress if A.is_running else 0,A.is_running,getattr(A,'pill_type',_U));H=f"#{C:02x}{E:02x}{G:02x}";I=f"● {int(A.progress)}%"if A.is_running else'● HGB OK';D.configure(bg=H,text=I);B.after(1000,F)
		F()
	except Exception:0
_BASE_ICON_CACHE={}
def _get_base_icon(ico_p):
	A=ico_p
	if not A:return
	if A not in _BASE_ICON_CACHE:
		try:_BASE_ICON_CACHE[A]=Image.open(A).convert(_V).resize((64,64),Image.LANCZOS)
		except Exception:_BASE_ICON_CACHE[A]=_A
	return _BASE_ICON_CACHE[A]
def create_tray_image(pct=0,spin_idx=0,pill_type=_U):
	C=pct;from core.files import get_app_icon_path as F;G=F();D=_get_base_icon(G)
	if D is not _A:
		A=D.copy();E=max(0,min(100,int(C)))
		if E>0:B=ImageDraw.Draw(A);B.ellipse([36,36,62,62],fill=(11,18,32,235),outline=(16,185,129,255),width=3);H=-90+int(360*E/1e2);B.arc([38,38,60,60],start=-90,end=H,fill=(16,185,129,255),width=4)
		return A
	A=Image.new(_V,(64,64),(11,18,32,255));B=ImageDraw.Draw(A);I=_status_gradient_rgb(C,C>0,pill_type);B.ellipse([3,3,61,61],fill=I,outline=(255,255,255,220),width=4);return A
def _get_tray_img_safe(pct,is_run,pill_type,spin_idx=0):
	A=pill_type
	try:return create_tray_image(pct,spin_idx,A)
	except Exception:B=Image.new(_V,(64,64),(16,185,129,255)if A=='ok'else(43,127,255,255));C=ImageDraw.Draw(B);C.rectangle((4,4,60,60),outline=(255,255,255,220),width=3);C.text((12,22),f"{int(pct)}%"if is_run else'HGB',fill=(255,255,255,255));return B
def _force_quit_app(engine):
	A=engine;_TRAY_STOP.set();B=threading.current_thread()is threading.main_thread()
	if os.sys.platform!=_Q or B:
		try:
			if A.tray_icon is not _A:A.tray_icon.visible=_C;A.tray_icon.stop();A.tray_icon=_A;time.sleep(.12)
		except Exception:0
		try:
			if A.app_ref is not _A:A.app_ref.root.quit();A.app_ref.root.destroy()
		except Exception:0
	os._exit(0)
def _can_dock_linux_tray():return bool(_LNX_TRAY_BE)
def _tray_backend_available():return HAS_TRAY and(not os.sys.platform.startswith(_F)or _can_dock_linux_tray())
def _tray_status_text(engine,language,elapsed_sec=0):
	C=language;B=engine;A=elapsed_sec;from core.i18n import tr
	if not B.is_running:return tr('Готовий до резервного копіювання',C)
	G=int(B.progress);A=max(0,int(A));D,H=divmod(A,3600);E,F=divmod(H,60);I=f"{D}:{E:02d}:{F:02d}"if D else f"{E}:{F:02d}";return f"{tr("Архівація",C)} · {I} · {G}%"
def _tray_problem():
	import sys
	if not HAS_TRAY:return'Трей: не встановлено pystray і Pillow'
	if sys.platform.startswith(_F)and not _LNX_TRAY_BE:
		if not os.environ.get(_G)and not os.environ.get(_T):return'Немає графічної сесії (DISPLAY не задано) — трей вимкнено'
		A=f"{os.environ.get(_W,"")} {os.environ.get(_X,"")}".upper()
		if'XFCE'in A:return'Трей XFCE: встановіть xfce4-statusnotifier-plugin і додайте «Status Notifier» на панель'
		if'GNOME'in A or'UNITY'in A:return'Трей GNOME: встановіть розширення AppIndicator and KStatusNotifierItem Support'
		if'KDE'in A or'PLASMA'in A:return'Трей KDE: перевірте, що увімкнено віджет «Системний лоток»'
		return'Панель не підтримує трей (потрібен StatusNotifier або XEmbed)'
	return'Системний трей недоступний'
def _start_tray_thread(engine):
	O='visible';N='HomeGrid Backup';I='[TRAY MODE] трей вимкнено вручну в налаштуваннях.';A=engine;global _TRAY_STARTED,_LNX_TRAY_BE,_LNX_TRAY_PROBED
	if os.sys.platform.startswith(_F):
		with _LNX_PROBE_LOCK:
			if not _LNX_TRAY_PROBED:
				_LNX_TRAY_PROBED=_B;A.tray_ready_event=threading.Event()
				def J():
					C='PYSTRAY_BACKEND';global _LNX_TRAY_BE;B=_requested_tray_backend(A)
					if B:_LNX_TRAY_BE=''if B==_E else B;A.log(f"[TRAY MODE] вибрано вручну: {B}. {TRAY_MODE_HINTS.get(B,"")} Після зміни режиму перезапустіть застосунок.",_D)
					else:_LNX_TRAY_BE=_detect_linux_tray_backend()
					A.log(_linux_tray_diag_line(),_D)
					if _LNX_TRAY_BE==_M:
						if _start_wayland_sni_bridge(A):
							with _TRAY_LOCK:D=_B
							return
						_LNX_TRAY_BE=_I if _has_x11_tray_manager()else''
					if _LNX_TRAY_BE in(_L,_N,_I)and not os.environ.get(C):os.environ[C]=_LNX_TRAY_BE
					if not _LNX_TRAY_BE:
						with _TRAY_LOCK:D=_C
						A.tray_ready=_C;A.tray_icon=_A;A.tray_ready_event.set()
						if B==_E:A.log(I,_D)
						else:A.log(_tray_problem(),_O)
						_enqueue_tray_ui(lambda:_show_wayland_fallback_badge(A));return
					_start_tray_thread(A)
				threading.Thread(target=J,daemon=_B).start();return
	from core.config import IS_WSL as P,NO_TRAY as Q
	with _TRAY_LOCK:
		if _TRAY_STARTED:return
		if Q or not A.state.get('tray_enabled',_B):_TRAY_STARTED=_B;A.tray_icon=_A;A.log('Трей вимкнено (--no-tray або в налаштуваннях).',_D);return
		if P:_TRAY_STARTED=_B;A.tray_icon=_A;A.log('Системний трей недоступний у середовищі WSL — робота продовжується без іконки в треї.',_D);return
		if os.sys.platform==_Q and _requested_tray_backend(A)==_E:_TRAY_STARTED=_B;A.tray_icon=_A;A.log(I,_D);return
		if not _tray_backend_available():_TRAY_STARTED=_B;A.tray_icon=_A;A.log(_tray_problem(),_O);return
		_TRAY_STARTED=_B;_TRAY_STOP.clear();A.tray_ready=_C;A.tray_error='';A.tray_ready_event=threading.Event()
	from core.backup import run_backup_task as R;from core.i18n import tr as C
	def S(icon,item):
		if A.app_ref is not _A:_enqueue_tray_ui(A.app_ref.show_window)
	def T(icon,item):
		if A.is_running:return
		threading.Thread(target=R,args=(A,A.state.get(_a,''),_C,_C,_C),daemon=_B).start()
	def U(icon,item):_force_quit_app(A)
	def V(icon,item):from core.config import DEFAULT_BACKUP_DIR as B;from core.files import open_folder_native as C;C(A.state.get(_b)or B)
	def D(method_name):
		def B(icon,item):
			if A.app_ref is not _A:
				def B():
					A.app_ref.show_window();B=getattr(A.app_ref,method_name,_A)
					if callable(B):B()
				_enqueue_tray_ui(B)
		return B
	B=_A
	def K():
		nonlocal B
		if not A.is_running:B=_A;return 0
		if B is _A:B=time.monotonic()
		return int(time.monotonic()-B)
	def L():B=A.state.get(_R,_S);E=K();F=_tray_status_text(A,B,E);return pystray.Menu(pystray.MenuItem(C(_c,B),S,default=_B,enabled=lambda item:A.app_ref is not _A),pystray.Menu.SEPARATOR,pystray.MenuItem(F,lambda i,it:_A,enabled=_C),pystray.MenuItem(C(_d,B),T,enabled=lambda item:not A.is_running),pystray.MenuItem(C(_e,B),V),pystray.Menu.SEPARATOR,pystray.MenuItem(C(_f,B),D('open_stats_modal'),enabled=lambda item:A.app_ref is not _A),pystray.MenuItem('☁ '+('Статистика pCloud'if B=='uk'else'pCloud Stats'),D('open_cloud_stats_modal'),enabled=lambda item:A.app_ref is not _A),pystray.MenuItem(C(_g,B),D('open_ops_history'),enabled=lambda item:A.app_ref is not _A),pystray.MenuItem(C(_h,B),D('open_analyze'),enabled=lambda item:A.app_ref is not _A),pystray.MenuItem(C(_i,B),D('open_settings'),enabled=lambda item:A.app_ref is not _A),pystray.Menu.SEPARATOR,pystray.MenuItem(C(_j,B),U))
	try:E=pystray.Icon(f"HomeGridBackup_{os.getpid()}",_get_tray_img_safe(0,_C,_U,0),N,L())
	except Exception as W:
		with _TRAY_LOCK:_TRAY_STARTED=_C
		A.tray_icon=_A;A.tray_error=str(W);A.tray_ready_event.set();A.log('Не вдалося створити значок системного трею.',_P);return
	A.tray_icon=E
	def F(exc):
		global _TRAY_STARTED;A.tray_ready=_C;A.tray_error=str(exc)or'Невідома помилка запуску трею.';A.tray_icon=_A;A.tray_ready_event.set();_TRAY_STOP.set()
		with _TRAY_LOCK:_TRAY_STARTED=_C
		A.log('Не вдалося запустити значок системного трею.',_P);A.log(f"[TRAY DETAIL] {A.tray_error}",_P)
		if A.app_ref is not _A:_enqueue_tray_ui(A.app_ref.show_window)
	def M(new_icon,new_menu,new_title):
		E=new_title;D=new_menu;C=new_icon;B=A.tray_icon
		if B is _A or not A.tray_ready or not getattr(B,O,_B):return
		try:
			if C is not _A:B.icon=C
			if D is not _A:B.menu=D;B.update_menu()
			if E is not _A:B.title=E
		except Exception:0
	def X():
		E=0;P,Q,R=_A,_A,'';S=.0;Y=os.sys.platform==_Q;G=os.name=='nt'
		while not _TRAY_STOP.is_set():
			_TRAY_STOP.wait(1.)
			if _TRAY_STOP.is_set():break
			try:
				if A.tray_icon is _A:break
				if not A.tray_ready:continue
				if not getattr(A.tray_icon,O,_B):continue
				H=int(A.progress)if A.is_running else 0;T=H//10*10 if G and A.is_running else H;U=A.state.get(_R,_S);V=T,A.is_running,A.pill_type;W=0 if G else H if A.is_running else 0,A.is_running,U,A.app_ref is not _A;Z=K();I=f"HomeGrid Backup: {_tray_status_text(A,U,Z)}"if A.is_running else N;B=_A
				if V!=P:B=_get_tray_img_safe(T,A.is_running,A.pill_type,0);P=V
				C=_A;X=time.monotonic();a=not G and X-S>=3.
				if W!=Q or A.is_running and a:C=L();Q=W;S=X
				D=_A
				if I!=R:D=I;R=I
				if B is not _A or C is not _A or D is not _A:
					if Y:_enqueue_tray_ui(lambda i=B,m=C,t=D:M(i,m,t))
					else:M(B,C,D)
				E=0
			except AssertionError as J:F(J);break
			except Exception as J:
				E+=1
				if E>=3:F(J);break
	def G(ready_icon):
		B=ready_icon
		try:
			B.visible=_B
			try:B.update_menu()
			except Exception:0
			A.tray_ready=_B;A.log(f"Значок системного трею активовано ({type(B).__module__}).",_D)
		except Exception as C:F(C)
		else:A.tray_ready_event.set()
	def Y():
		try:E.run(setup=G)
		except Exception as A:F(A)
	threading.Thread(target=X,daemon=_B).start()
	if os.sys.platform==_Q:
		def H():
			try:
				if hasattr(E,'run_detached'):E.run_detached(setup=G)
				else:G(E)
			except Exception as A:F(A)
		if A.app_ref is not _A:A.app_ref.root.after(0,H)
		else:H()
	else:threading.Thread(target=Y,daemon=_B).start()
_SNI_HELPER='\nimport sys, json, threading, signal, gi\ngi.require_version("Gtk", "3.0")\ntry:\n    gi.require_version("AyatanaAppIndicator3", "0.1")\n    from gi.repository import AyatanaAppIndicator3 as AI\nexcept Exception:\n    gi.require_version("AppIndicator3", "0.1")\n    from gi.repository import AppIndicator3 as AI\nfrom gi.repository import Gtk, GLib\n\nind = AI.Indicator.new("homegrid-backup", next(iter(sys.argv[1:])), AI.IndicatorCategory.APPLICATION_STATUS)\nind.set_status(AI.IndicatorStatus.ACTIVE)\nmenu = Gtk.Menu()\nitems = {}\nfor k, lbl in json.loads(next(iter(sys.argv[2:]))):\n    if lbl is None:\n        menu.append(Gtk.SeparatorMenuItem())\n        continue\n    mi = Gtk.MenuItem(label=lbl)\n    if k == "status":\n        mi.set_sensitive(False)\n    else:\n        mi.connect("activate", lambda _w, c=k: print(json.dumps({"cmd": c}), flush=True))\n    menu.append(mi)\n    items[k] = mi\nmenu.show_all()\nind.set_menu(menu)\nif "open" in items:\n    ind.set_secondary_activate_target(items["open"])\nprint(json.dumps({"ready": True}), flush=True)\n\ndef _in_loop():\n    for ln in sys.stdin:\n        try:\n            d = json.loads(ln)\n            if "status" in d: GLib.idle_add(items["status"].set_label, d["status"])\n            if "running" in d: GLib.idle_add(items["backup"].set_sensitive, not d["running"])\n            if d.get("quit"): break\n        except Exception:\n            pass\n    GLib.idle_add(Gtk.main_quit)\n\nthreading.Thread(target=_in_loop, daemon=True).start()\nsignal.signal(signal.SIGINT, signal.SIG_DFL)\nGtk.main()\n'
def _start_wayland_sni_bridge(engine):
	R='exit';Q='settings';P='analyze';O='history';N='cstats';M='stats';L='folder';K='backup';J='status';I='open';H='/usr/bin/python3';A=engine;import json as F,subprocess as E;from core.backup import run_backup_task as S;from core.config import DEFAULT_BACKUP_DIR as T;from core.files import get_app_icon_path as U,open_folder_native as V;from core.i18n import tr as D;G=H if os.path.exists(H)else _A
	if not G:return _C
	B=A.state.get(_R,_S);W=[(I,D(_c,B)),('s1',_A),(J,_tray_status_text(A,B,0)),(K,D(_d,B)),(L,D(_e,B)),('s2',_A),(M,D(_f,B)),(N,'☁ Статистика pCloud'),(O,D(_g,B)),(P,D(_h,B)),(Q,D(_i,B)),('s3',_A),(R,D(_j,B))];X=U()or'drive-harddisk'
	try:
		C=E.Popen([G,'-c',_SNI_HELPER,X,F.dumps(W,ensure_ascii=_C)],stdin=E.PIPE,stdout=E.PIPE,stderr=E.DEVNULL,text=_B,encoding=_K,bufsize=1,env=_clean_sys_env());Y=C.stdout.readline()
		if'"ready": true'not in Y.lower():C.terminate();return _C
	except Exception:return _C
	class Z:
		visible=_B
		def stop(A):
			try:C.stdin.write('{"quit":true}\n');C.stdin.flush();C.terminate()
			except Exception:0
	A.tray_icon=Z();A.tray_ready=_B;A.tray_error=''
	if getattr(A,'tray_ready_event',_A):A.tray_ready_event.set()
	A.log('Активовано системний трей Wayland (AppIndicator bridge).',_D)
	def a(cmd):
		C=cmd;B=A.app_ref
		if C==R:_force_quit_app(A)
		elif C==L:V(A.state.get(_b)or T)
		elif C==K and not A.is_running:threading.Thread(target=S,args=(A,A.state.get(_a,''),_C,_C,_C),daemon=_B).start()
		elif B is not _A:
			D={I:B.show_window,M:lambda:(B.show_window(),B.open_stats_modal()),N:lambda:(B.show_window(),B.open_cloud_stats_modal()),O:lambda:(B.show_window(),B.open_ops_history()),P:lambda:(B.show_window(),B.open_analyze()),Q:lambda:(B.show_window(),B.open_settings())}
			if C in D:_enqueue_tray_ui(D[C])
	def b():
		for B in C.stdout:
			try:
				A=F.loads(B).get('cmd')
				if A:a(A)
			except Exception:0
	def c():
		B,G,D,H=_A,'',_A,.0
		while not _TRAY_STOP.is_set()and C.poll()is _A:
			_TRAY_STOP.wait(1.)
			if not A.is_running:B=_A
			elif B is _A:B=time.monotonic()
			K=int(time.monotonic()-B)if B else 0;E=_tray_status_text(A,A.state.get(_R,_S),K);I=time.monotonic()
			if E!=G or A.is_running!=D:
				if A.is_running==D and I-H<2.:continue
				try:C.stdin.write(F.dumps({J:E,'running':bool(A.is_running)},ensure_ascii=_C)+'\n');C.stdin.flush();G,D,H=E,bool(A.is_running),I
				except Exception:break
	threading.Thread(target=b,daemon=_B).start();threading.Thread(target=c,daemon=_B).start();return _B
def _start_show_window_listener(engine,event_name='Global\\HomeGridBackup_ShowWindow_v1'):
	A=engine
	if os.name!='nt':
		def B():
			try:
				import hashlib as F,socket as C,sys,tempfile as G;H=F.md5(os.path.realpath(sys.argv[0]).encode(_K,errors=_Y)).hexdigest()[:10];D=os.path.join(G.gettempdir(),f"hgb_inst_{H}.port");B=C.socket(C.AF_INET,C.SOCK_STREAM);B.bind(('127.0.0.1',0));B.listen(2);import atexit as I;I.register(lambda p=D:os.path.exists(p)and os.remove(p))
				with open(D,'w')as J:J.write(str(B.getsockname()[1]))
				while _B:
					E,L=B.accept();K=E.recv(16);E.close()
					if b'SHOW'in K and A.app_ref is not _A:_enqueue_tray_ui(A.app_ref.show_window)
			except Exception:0
		threading.Thread(target=B,daemon=_B).start();return
	def C():
		try:
			B=ctypes.windll.kernel32;C=B.CreateEventW(_A,_C,_C,event_name)
			while C:
				if B.WaitForSingleObject(C,1000)==0 and A.app_ref is not _A:A.app_ref.root.after(0,A.app_ref.show_window)
		except Exception:0
	threading.Thread(target=C,daemon=_B).start()
