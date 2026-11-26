# patch-id: force-tall-pbar-and-grid-2.74
# [ФАЙЛ: gui/widgets.py (v2.10 | 24.11.2026 02:15) — ИНДИКАТОР ПРОГРЕССА (V8 + LITE)]
_W='hidden'
_V='#1d6ef2'
_U='Segoe UI'
_T='all'
_S='disabled'
_R='#f1f5f9'
_Q='border'
_P='bold'
_O='<Button-1>'
_N='#94a3b8'
_M='#1e293b'
_L='#23314d'
_K='normal'
_J='inp_bg'
_I='left'
_H='text'
_G=False
_F='#131c2e'
_E='muted'
_D='card'
_C='panel'
_B='hand2'
_A=None
import sys,tkinter as tk
from core.i18n import tr
from gui.styles import THEMES
PBAR_FROM='#2563eb'
PBAR_TO='#10b981'
STRIPS=60
LITE_CHARS=36
MONO='Menlo'if sys.platform=='darwin'else'DejaVu Sans Mono'if sys.platform.startswith('linux')else'Consolas'
class HomeGridToggle(tk.Frame):
	def __init__(A,parent,variable,command=_A,compact=_G,on_text='Увімкнено',off_text='Вимкнено',palette=_A,font_fam=_U,font_sz=10):
		B=font_sz;A.var=variable;A.cmd=command;A.compact=bool(compact);A.on_text=on_text;A.off_text=off_text;A._fam=font_fam;A._fs=B;A._state=_K;A._pal=palette or{_C:_F,_D:_F,_J:_L,_Q:_M,_H:_R,_E:_N,'blue':_V};super().__init__(parent,bg=A._pal.get(_D,_F),bd=0,highlightthickness=0)
		if A.compact:D,E=max(36,int(B*3.4)),max(20,int(B*1.9));A.cv=tk.Canvas(A,width=D,height=E,bg=A._pal.get(_C,_F),highlightthickness=0,bd=0,cursor=_B);A.cv.pack();A.cv.bind(_O,A._on_click_compact)
		else:
			A.r_on=tk.Frame(A,bg=A._pal[_D],cursor=_B);A.r_on.pack(fill='x',pady=(2,4));A.cv_on=tk.Canvas(A.r_on,width=22,height=22,bg=A._pal[_D],highlightthickness=0,bd=0,cursor=_B);A.cv_on.pack(side=_I,padx=(0,8));A.lbl_on=tk.Label(A.r_on,text=A.on_text,bg=A._pal[_D],fg=A._pal[_H],font=(A._fam,A._fs),cursor=_B);A.lbl_on.pack(side=_I);A.sep=tk.Frame(A,height=1,bg=A._pal.get(_Q,_M));A.sep.pack(fill='x',pady=2);A.r_off=tk.Frame(A,bg=A._pal[_D],cursor=_B);A.r_off.pack(fill='x',pady=(4,2));A.cv_off=tk.Canvas(A.r_off,width=22,height=22,bg=A._pal[_D],highlightthickness=0,bd=0,cursor=_B);A.cv_off.pack(side=_I,padx=(0,8));A.lbl_off=tk.Label(A.r_off,text=A.off_text,bg=A._pal[_D],fg=A._pal[_H],font=(A._fam,A._fs),cursor=_B);A.lbl_off.pack(side=_I)
			for C in(A.r_on,A.cv_on,A.lbl_on):C.bind(_O,lambda _e:A._set_val(True))
			for C in(A.r_off,A.cv_off,A.lbl_off):C.bind(_O,lambda _e:A._set_val(_G))
		A.redraw()
	def _on_click_compact(A,_e=_A):
		if A._state!=_S:A._set_val(not bool(A.var.get()))
	def _set_val(A,val):
		if A._state==_S:return
		A.var.set(bool(val));A.redraw()
		if callable(A.cmd):A.cmd()
	def apply_style(A,palette=_A,state=_A,on_text=_A,off_text=_A,font_fam=_A,font_sz=_A):
		G=font_sz;F=font_fam;E=off_text;D=on_text;C=state;B=palette
		if B:A._pal=B
		if C:A._state=C
		if D is not _A:A.on_text=D
		if E is not _A:A.off_text=E
		if F:A._fam=F
		if G:A._fs=G
		A.redraw()
	def redraw(A):
		P='#64748b';C=A._pal;D=bool(A.var.get());G=C.get('blue',_V)
		if A.compact:N=C.get(_C,_F);A.configure(bg=N);A.cv.configure(bg=N,cursor=''if A._state==_S else _B);A.cv.delete(_T);E,K=int(A.cv.cget('width')),int(A.cv.cget('height'));B=(K-4)//2;L=G if D else C.get(_J,_L);H=G if D else C.get(_E,P);A.cv.create_arc(2,2,2+B*2,2+B*2,start=90,extent=180,fill=L,outline=H);A.cv.create_arc(E-2-B*2,2,E-2,2+B*2,start=270,extent=180,fill=L,outline=H);A.cv.create_rectangle(2+B,2,E-2-B,2+B*2,fill=L,outline='');A.cv.create_line(2+B,2,E-2-B,2,fill=H);A.cv.create_line(2+B,2+B*2,E-2-B,2+B*2,fill=H);O=E-4-B if D else 4+B;I=max(4,B-3);A.cv.create_oval(O-I,K//2-I,O+I,K//2+I,fill='#ffffff'if D else C.get(_E,_N),outline='');return
		J=C.get(_D,_F);A.configure(bg=J);A.sep.configure(bg=C.get(_Q,_M))
		for(Q,F,R,M,S)in((A.r_on,A.cv_on,A.lbl_on,D,A.on_text),(A.r_off,A.cv_off,A.lbl_off,not D,A.off_text)):
			Q.configure(bg=J);F.configure(bg=J);R.configure(text=S,bg=J,fg=C.get(_H,_R)if M else C.get(_E,_N),font=(A._fam,A._fs,_P if M else _K));F.delete(_T)
			if M:F.create_oval(2,2,20,20,outline=G,width=2,fill=C.get(_J,_L));F.create_oval(6,6,16,16,fill=G,outline='')
			else:F.create_oval(2,2,20,20,outline=C.get(_E,P),width=2,fill=C.get(_J,_L))
def make_ui_icons(sz,fg_hex,accent_hex):
	I=fg_hex;D=accent_hex
	try:from PIL import Image as J,ImageDraw as L,ImageTk as M
	except Exception:return{}
	K,A=max(14,int(sz)),max(14,int(sz))*2;C=max(2,A//10);F={}
	def G():B=J.new('RGBA',(A,A),(0,0,0,0));return B,L.Draw(B)
	def H(im):return M.PhotoImage(im.resize((K,K),J.LANCZOS))
	E,B=G();B.ellipse([3,3,A-4,A-4],outline=I,width=C);B.line([A//2,A//4,A//2,A//2,A*3//4,A//2],fill=I,width=C);F['hist']=H(E);E,B=G();B.polygon([(A//2,3),(A-4,A//4),(A*4//5,A*3//4),(A//2,A-3),(A//5,A*3//4),(4,A//4)],outline=D,width=C);F['shield']=H(E);E,B=G();B.ellipse([A//4,A//4,A*3//4,A*3//4],outline=D,width=C);B.ellipse([A*2//5,A*2//5,A*3//5,A*3//5],fill=D);F['gear']=H(E);E,B=G();B.ellipse([A//4,A//5,A*3//4,A*3//4],outline=D,width=C);B.ellipse([3,A*2//5,A//2,A*4//5],outline=D,width=C);B.ellipse([A//2,A*2//5,A-4,A*4//5],outline=D,width=C);B.line([A//4,A*4//5,A*3//4,A*4//5],fill=D,width=C);F['cloud']=H(E);return F
class SidebarNavItem(tk.Frame):
	def __init__(A,parent,icon_img,icon_fallback,label_text,on_click,palette,font_fam=_U,font_sz=10,height_px=40):
		E=font_sz;D=font_fam;C=icon_img;B=palette;A._pal=B;A._on_click=on_click;A._active=_G;A._fam=D;A._fs=E;super().__init__(parent,bg=B[_C],height=height_px,cursor=_B,bd=0,highlightthickness=0);A.pack_propagate(_G);A.inner=tk.Frame(A,bg=B[_C],padx=12,cursor=_B);A.inner.pack(fill='both',expand=True)
		if C is not _A:A.lbl_ico=tk.Label(A.inner,image=C,bg=B[_C],cursor=_B);A.lbl_ico._img_ref=C
		else:A.lbl_ico=tk.Label(A.inner,text=icon_fallback,width=2,anchor='center',bg=B[_C],fg=B[_E],font=(D,E,_P),cursor=_B)
		A.lbl_ico.pack(side=_I,padx=(0,8));A.lbl_txt=tk.Label(A.inner,text=label_text,anchor='w',bg=B[_C],fg=B[_H],font=(D,E),cursor=_B);A.lbl_txt.pack(side=_I,fill='x',expand=True)
		for F in(A,A.inner,A.lbl_ico,A.lbl_txt):F.bind(_O,A._handle_click);F.bind('<Enter>',A._on_enter);F.bind('<Leave>',A._on_leave)
	def _handle_click(A,_e=_A):
		if callable(A._on_click):A._on_click()
	def _on_enter(A,_e=_A):
		if not A._active:
			B=A._pal.get(_D,'#182338')
			for C in(A,A.inner,A.lbl_ico,A.lbl_txt):C.configure(bg=B)
	def _on_leave(A,_e=_A):
		if not A._active:
			B=A._pal.get(_C,_F)
			for C in(A,A.inner,A.lbl_ico,A.lbl_txt):C.configure(bg=B)
	def set_active(A,is_active,text_override=_A):
		B=text_override;A._active=bool(is_active)
		if B is not _A:A.lbl_txt.configure(text=B)
		D='#1c2a44'if A._active and A._pal.get('bg')=='#0b1220'else A._pal.get(_J)if A._active else A._pal.get(_C);C=A._pal.get('cyan','#60a5fa')if A._active else A._pal.get(_H,_R)
		for E in(A,A.inner,A.lbl_ico,A.lbl_txt):E.configure(bg=D)
		A.lbl_txt.configure(fg=C,font=(A._fam,A._fs,_P if A._active else _K))
		if not hasattr(A.lbl_ico,'_img_ref'):A.lbl_ico.configure(fg=C if A._active else A._pal.get(_E,_N))
class StyledProgressBar(tk.Canvas):
	def __init__(A,parent,height=20,**B):super().__init__(parent,height=height,highlightthickness=0,bd=0,**B);A.pct=0;A.indet=_G;A.lite_mode=_G;A.theme=THEMES['dark'];A.lang='en';A._phase=0;A._strips=[];A._text=_A;A._cw=A._ch=0;A.bind('<Configure>',lambda e:A._rebuild())
	def set_state(A,pct,indet,style_name,lite_mode,theme,status_lbl='',lang='en'):
		B=theme;A.lang=lang or'en';A.pct=max(0,min(100,int(pct or 0)));A.indet=bool(indet)
		if A.indet:A._phase=(A._phase+1)%40
		C=bool(lite_mode)
		if C!=A.lite_mode or B!=A.theme or A._cw==0 or abs(A.winfo_height()-A._ch)>2:A.lite_mode=C;A.theme=B;A._rebuild();return
		A._update()
	def _rebuild(A):
		A.delete(_T);A._strips=[];A._text=_A;E=max(10,A.winfo_width());C=max(10,A.winfo_height());A._cw,A._ch=E,C
		if A.lite_mode:A.configure(bg=A.theme['bg']);L=max(11,min(18,C//3));A._text=A.create_text(4,C//2,anchor='w',text='',fill=A.theme['cyan'],font=(MONO,L,_P))
		else:
			A.configure(bg=A.theme.get('pbar_bg',_M));A.create_rectangle(0,0,E-1,C-1,outline=A.theme.get('pbar_brd','#475569'),width=1);B=A.winfo_rgb(A.theme.get('pbar_from',PBAR_FROM));F=A.winfo_rgb(A.theme.get('pbar_to',PBAR_TO));G=E-4;D=max(1,min(G,STRIPS))
			for H in range(D):I=H/max(1,D-1);M=int((B[0]+(F[0]-B[0])*I)/256);N=int((B[1]+(F[1]-B[1])*I)/256);O=int((B[2]+(F[2]-B[2])*I)/256);J=2+G*H//D;K=2+G*(H+1)//D;P=A.create_rectangle(J,2,K,C-2,fill=f"#{M:02x}{N:02x}{O:02x}",outline='',state=_W);A._strips.append((J,K,P))
		A._update()
	def _update(A):
		if A.lite_mode:
			if A._text is _A:return
			if A.indet:
				L=A._phase%(LITE_CHARS-4);G=['-']*LITE_CHARS
				for M in range(4):G[L+M]='#'
				H=f"[{''.join(G)}] {tr('пошук...',A.lang)}"
			else:I=int(round(A.pct/1e2*LITE_CHARS));H=f"[{'#'*I}{'-'*(LITE_CHARS-I)}] {A.pct:3d}%"
			A.itemconfigure(A._text,text=H);return
		C,N=A._cw,A._ch
		if A.indet:E=max(40,int(C*.28));B=int(A._phase/39.*(C+E)-E);D=B+E
		else:B=2;D=2+int((C-4)*A.pct/1e2)
		B,D=max(2,B),min(C-2,D)
		for(O,P,F)in A._strips:
			J,K=max(O,B),min(P,D)
			if K>J:A.coords(F,J,2,K,N-2);A.itemconfigure(F,state=_K)
			else:A.itemconfigure(F,state=_W)
