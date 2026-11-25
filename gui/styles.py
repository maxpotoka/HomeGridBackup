# patch-id: stage-window-2.21
# patch-id: homegrid-design-system-2.45
# [ФАЙЛ: gui/styles.py (v2.02 | 22.11.2026 09:10) — ТЕМЫ ОФОРМЛЕНИЯ, МАСШТАБ ЭКРАНА (DPI WIN7) И TOOLTIP]
_d='darwin'
_c='<Enter>'
_b='#0f172a'
_a='#f8fafc'
_Z='#ef4444'
_Y='#f59e0b'
_X='#10b981'
_W='#94a3b8'
_V='#1e293b'
_U='#0b1220'
_T='relief'
_S='pbar_brd'
_R='pbar_bg'
_Q='green_txt'
_P='btn_txt'
_O='log_bg'
_N='inp_bg'
_M='border'
_L='Segoe UI'
_K='#1d6ef2'
_J='#f1f5f9'
_I='cyan'
_H='red'
_G='amber'
_F='green'
_E='blue'
_D='panel'
_C='auto'
_B='#ffffff'
_A=None
import ctypes,os,tkinter as tk
if os.name=='nt':from ctypes import wintypes
from core.config import VALID_SCALES
UI_SCALE_LABELS=[(_C,'Авто (під монітор і DPI)'),('800x600','800 × 600 (SVGA)'),('1024x600','1024 × 600 (Нетбук)'),('1024x768','1024 × 768 (XGA)'),('1280x720','1280 × 720 (HD 720p)'),('1366x768','1366 × 768 (WXGA)'),('1600x900','1600 × 900 (HD+)'),('1920x1080','1920 × 1080 (Full HD)'),('2560x1440','2560 × 1440 (2K QHD)')]
UI_FONT_LABELS=[(0,'Авто (за розміром вікна)'),(8,'8 pt (Дуже дрібний)'),(9,'9 pt (Дрібний)'),(10,'10 pt (Стандартний)'),(11,'11 pt (Середній)'),(12,'12 pt (Великий)'),(14,'14 pt (Дуже великий)'),(16,'16 pt (Підвищений)'),(18,'18 pt (Крупний)'),(20,'20 pt (Дуже крупний)'),(22,'22 pt (Суперкрупний)'),(24,'24 pt (Гігантський)'),(26,'26 pt (Максимальний)')]
PBAR_STYLE_LABELS=[('v8','Адаптивний градієнт (v8)')]
THEMES={'dark':{'bg':_U,_D:'#131c2e','card':'#182338',_M:_V,'text':_J,'muted':_W,_E:_K,_F:_X,_G:_Y,_H:_Z,_I:'#60a5fa',_N:'#23314d',_O:_U,_P:_B,_Q:_B,_R:_V,_S:'#334155','font':_L,_T:'flat'},'light':{'bg':'#f3f6fb',_D:_B,'card':_a,_M:'#dfe7f2','text':_b,'muted':'#64748b',_E:_K,_F:'#059669',_G:'#d97706',_H:'#dc2626',_I:_K,_N:'#e8eef7',_O:_a,_P:_B,_Q:_B,_R:'#e2e8f0',_S:'#cbd5e1','font':_L,_T:'flat'}}
def _calc_screen_metrics(root,scale_pref=_C,font_pref=0,live_outer_wh=_A):
	c='scaling';W=live_outer_wh;V=scale_pref;O=font_pref;D=root;K,L=0,0;E,F=D.winfo_screenwidth()or 1024,D.winfo_screenheight()or 768;A=96;P,Q=16,40
	try:
		B=ctypes.windll.user32;d=ctypes.windll.gdi32
		try:A=B.GetDpiForSystem()
		except Exception:
			R=B.GetDC(0)
			if R:A=d.GetDeviceCaps(R,88)or 96;B.ReleaseDC(0,R)
		if not A or A<72:A=96
		G=wintypes.RECT()
		if B.SystemParametersInfoW(48,0,ctypes.byref(G),0):K,L=G.left,G.top;E,F=max(640,G.right-G.left),max(480,G.bottom-G.top)
		e=B.GetSystemMetrics(32);f=B.GetSystemMetrics(33);g=B.GetSystemMetrics(4);X=B.GetSystemMetrics(92);P=max(8,(e+X)*2);Q=max(28,g+(f+X)*2)
	except Exception:
		try:
			Y=float(D.winfo_fpixels('1i'))
			if 72.<=Y<=384.:A=int(round(Y))
		except Exception:A=96
	if os.name!='nt':
		try:Z=float(D.tk.call('tk',c))*72.;A=int(round(Z))if 72<=Z<=288 else 96
		except Exception:A=96
		K,L=0,0;E=D.winfo_screenwidth()or 1024;F=int((D.winfo_screenheight()or 768)*.93);P,Q=8,34
	I=max(1.,A/96.)
	try:D.tk.call('tk',c,A/72.)
	except Exception:0
	M=V if V in VALID_SCALES else _C
	if W is not _A:h,i=W;C=max(640,int(h));H=max(480,int(i));j=(C/I/12e2+H/I/72e1)/2.;S=round(max(.8,min(1.6,j)),2);T=max(9,min(16,int(round(1e1*S))));a=T
	else:
		if M!=_C and'x'in M:k,l=M.split('x',1);C=min(E,int(k));H=min(F,int(l))
		else:C=min(E,max(900,int(E*.72)));H=min(F,max(600,int(F*.75)))
		S=round(max(.8,min(1.6,C/I/128e1)),2);T=max(9,min(16,int(round(1e1*S))));a=int(O)if isinstance(O,int)and 8<=O<=28 else T
	m=max(620,C-P);n=max(440,H-Q);N=C/I;U=H/I;o=8 if N<860 else 9 if N<1060 else 10 if N<1260 else max(11,min(15,int(N/80)));p=8 if U<620 else 9 if U<720 else max(10,min(15,int(U/52)));q=max(8,min(o,p));b=max(8,min(a,q));J=round(max(.76,min(1.45,b/10.5)),2);r,s=max(5,int(round(9*J))),max(2,int(round(4*J)));t,u=max(5,int(round(8*J))),max(1,int(round(3*J)));v=K+max(0,(E-C)//2);w=L+max(0,(F-H)//2);return{'wa_x':K,'wa_y':L,'sw':E,'sh':F,'outer_w':C,'outer_h':H,'win_w':m,'win_h':n,'pos_x':v,'pos_y':w,'scale_code':M,'font_sz':b,'k':J,'pad_x':r,'pad_y':s,'btn_px':t,'btn_py':u}
class ToolTip:
	def __init__(A,widget,text):
		C='+';B=widget
		if getattr(B,'_has_tooltip',False):return
		B._has_tooltip=True;A.widget=B;A.text=text;A.tipwin=_A;A._after_id=_A;A._watch_id=_A;B.bind(_c,A._schedule,add=C);B.bind('<Leave>',A.hide,add=C);B.bind('<ButtonPress>',A.hide,add=C)
	def _schedule(A,_event=_A):
		if A.tipwin or A._after_id or not A.text:return
		A._after_id=A.widget.after(260,A.show)
	def _pointer_inside(A):
		try:D,E=A.widget.winfo_pointerxy();B,C=A.widget.winfo_rootx(),A.widget.winfo_rooty();F,G=A.widget.winfo_width(),A.widget.winfo_height();return B<=D<=B+F and C<=E<=C+G
		except Exception:return False
	def _watchdog(A):
		A._watch_id=_A
		if not A.tipwin:return
		if not A.widget.winfo_exists()or not A._pointer_inside():A.hide();return
		A._watch_id=A.widget.after(250,A._watchdog)
	def show(A,_event=_A):
		U='solid';T='#060911';S='left';R='linux';import sys as I;A._after_id=_A
		if A.tipwin or not A.text or not A._pointer_inside():return
		B=A.widget.winfo_toplevel();J=getattr(B,'_active_tooltip',_A)
		if J and J is not A:J.hide()
		B._active_tooltip=A;V=getattr(B,'_cur_font_sz',10);E=max(9,V-1);M='Helvetica Neue'if I.platform==_d else'Ubuntu'if I.platform.startswith(R)else _L;from core.i18n import tr;N=tr(A.text,getattr(B,'_cur_lang','en'));O,H=A.widget.winfo_rootx(),A.widget.winfo_rooty();b,P=A.widget.winfo_width(),A.widget.winfo_height()
		if I.platform.startswith(R):
			D=tk.Label(B,text=N,justify=S,background=T,foreground=_J,relief=U,borderwidth=1,padx=max(10,E),pady=max(5,E//2),font=(M,E),wraplength=max(320,min(520,B.winfo_width()-32)));D.update_idletasks();K,G=D.winfo_reqwidth(),D.winfo_reqheight();W,Q=B.winfo_rootx(),B.winfo_rooty();X,Y=max(200,B.winfo_width()),max(150,B.winfo_height());L=max(6,min(O-W+8,X-K-6));F=H-Q-G-6
			if F<6:F=min(Y-G-6,H-Q+P+6)
			D.place(x=L,y=F);D.lift();D.bind(_c,lambda _e:A.hide());A.tipwin=D;A._watch_id=A.widget.after(250,A._watchdog);return
		A.tipwin=C=tk.Toplevel(A.widget);C.withdraw();C.wm_overrideredirect(True);D=tk.Label(C,text=N,justify=S,background=T,foreground=_J,relief=U,borderwidth=1,padx=max(10,E),pady=max(5,E//2),font=(M,E),wraplength=max(360,E*34));D.pack();C.update_idletasks();K,G=C.winfo_reqwidth(),C.winfo_reqheight();Z,a=B.winfo_screenwidth()or 1280,B.winfo_screenheight()or 720;L=max(8,min(O+8,Z-K-8));F=H-G-8
		if F<8:F=min(a-G-8,H+P+8)
		C.wm_geometry(f"+{L}+{F}")
		try:C.transient(B);C.lift();C.attributes('-topmost',True)
		except Exception:0
		C.deiconify()
	def hide(A,_event=_A):
		for B in('_after_id','_watch_id'):
			C=getattr(A,B,_A)
			if C:
				try:A.widget.after_cancel(C)
				except Exception:0
				setattr(A,B,_A)
		if A.tipwin:
			try:A.tipwin.destroy()
			except Exception:0
			A.tipwin=_A
def fix_mac_buttons(root_widget,palette=_A):
	A=root_widget;import sys
	if sys.platform!=_d or A is _A:return
	B=palette or{};G=B.get(_F,_X);H=B.get(_E,'#2b7fff');D=B.get(_H,_Z);I=B.get(_G,_Y);J=B.get(_I,'#38bdf8')
	def E(w):
		try:
			if isinstance(w,tk.Button):
				C=str(w.cget('bg')).lower();F=str(w.cget('fg')).lower()
				if C==str(G).lower():A='#065f46'
				elif C==str(H).lower():A='#1d4ed8'
				elif C==str(D).lower()or F==str(D).lower():A='#b91c1c'
				elif C==str(I).lower():A='#92400e'
				elif F==str(J).lower():A='#0369a1'
				else:A=_b
				w.configure(fg=A,activeforeground=A,disabledforeground=_W,highlightbackground=B.get(_D,'#111827'))
		except Exception:0
		try:
			for K in w.winfo_children():E(K)
		except Exception:0
	E(A)
