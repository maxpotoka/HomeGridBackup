# patch-id: main-win-adapter-badge-3.02
# patch-id: startup-version-log-2.80
# patch-id: i18n-ping-and-retry-en-2.79
# patch-id: fix-net-drive-status-and-build-retry-2.78
# patch-id: idle-ui-cache-2.19
# patch-id: opt-log-i18n-ui-2.20
# patch-id: mirror-btn-sig-2.22
# patch-id: adaptive-ui-poll-2.11
# patch-id: ui-widget-signatures-2.12
# patch-id: macos-tray-quit-apps-2.41
# patch-id: cumulative-linux-tray-pcloud-menu-2.42
# patch-id: card-conn-copies-2.59
# patch-id: archives-label-and-logs-dir-2.60
# patch-id: dest-stats-bg-worker-2.61
# patch-id: pcloud-inline-path-2.63
# patch-id: lan-btn-layout68-2.64
# patch-id: fav-servers-pills-2.65
# patch-id: fix-grid-rows-2.65a
# patch-id: big-bottom-pbar-2.66
# patch-id: pcloud-stats-refresh-compact-2.67
# patch-id: split-last-backup-2.68
# patch-id: pretty-last-backup-2.69
# patch-id: tall-pbar-server-marquee-2.70
# patch-id: remove-mirror-ui-2.71-p1
# patch-id: force-tall-pbar-and-grid-2.74
# [ФАЙЛ: gui/window.py (v2.31 | 24.11.2026 02:15) — ГЛАВНОЕ ОКНО HOMEGRIDAPP И ФОНОВЫЙ ЦИКЛ UI]
# patch-id: center-storage-notepad-2.40
# patch-id: dashboard-redesign-2.34
# patch-id: homegrid-design-system-2.45
_AR='discovered_servers'
_AQ='dest_rows'
_AP='🛡 Перевірка SHA'
_AO='local_enabled'
_AN='☀️ Світла тема'
_AM='green_txt'
_AL='Відкрити папку'
_AK='HomeGrid Backup'
_AJ='Налаштування'
_AI='Про програму'
_AH='DejaVu Sans Mono'
_AG='Noto Sans'
_AF='Liberation Sans'
_AE='DejaVu Sans'
_AD='Helvetica Neue'
_AC='mirror_enabled'
_AB='request_dest_stats_refresh'
_AA='free_gb'
_A9='Очікування'
_A8='Автопошук LAN'
_A7='btn_txt'
_A6='inp_bg'
_A5='Consolas'
_A4='Segoe UI'
_A3='mirror_dir'
_A2='_dest_stats'
_A1='utf-8'
_A0='solid'
_z='err'
_y='withdrawn'
_x='iconic'
_w='HomeGridBackup'
_v='server'
_u='favorite_servers'
_t='network'
_s='center'
_r='theme'
_q='#ffffff'
_p='cloud_path'
_o='win_h'
_n='win_w'
_m='ui_font'
_l='net_enabled'
_k='cloud_enabled'
_j='net_dir'
_i='auto'
_h='ui_scale'
_g='pcloud'
_f='blue'
_e='info'
_d='linux'
_c='1.0'
_b='amber'
_a='lite_mode'
_Z='dark'
_Y='normal'
_X='darwin'
_W='disabled'
_V='en'
_U='lang'
_T='red'
_S='warn'
_R='backup_dir'
_Q='ok'
_P='cyan'
_O='border'
_N='card'
_M='end'
_L='font_sz'
_K='green'
_J='w'
_I='muted'
_H='text'
_G='hand2'
_F=False
_E='left'
_D=True
_C='bold'
_B=None
_A='panel'
import os,threading,time,tkinter as tk
from core.backup import run_backup_task
from core.build_variant import WINDOWS7_CLOUD_SYNC_PREVIEW
from core.config import BUILD_DATE,DEFAULT_BACKUP_DIR,NO_TRAY,SCRIPT_VER,commit_state,get_logs_dir
from core.files import choose_folder_native,get_app_icon_path,open_folder_native
from core.i18n import apply_widget_i18n,tr
from core.network import normalize_server_url,run_connect_task,run_scan_task
from gui.dialogs import DialogsMixin
from gui.styles import THEMES,UI_SCALE_LABELS,ToolTip,_calc_screen_metrics,fix_mac_buttons
from gui.widgets import HomeGridToggle,StyledProgressBar
class HomeGridApp(DialogsMixin):
	def __init__(A,root,engine):
		I='<<Cut>>';H='<<Copy>>';G='<<Paste>>';F='break';E='Entry';A.root=root;A.root.withdraw();A.engine=engine;A.metrics=_calc_screen_metrics(root,A.engine.state.get(_h,_i),A.engine.state.get(_m,0));A.last_log_len=0;A._last_log_item=_B;A.last_modal_id=_B;A.hw_notice_shown=_F;A._srv_typing_timer=_B;A._resize_timer=_B;A._last_live_wh=0,0;A._ignore_resize_until=time.time()+1.;A.root.title(f"HomeGrid Backup v{SCRIPT_VER} (від {BUILD_DATE})");B=A.metrics;A.root.geometry(f"{B[_n]}x{B[_o]}+{B["pos_x"]}+{B["pos_y"]}");A.root.minsize(min(620,B[_n]),min(420,B[_o]));import sys as C,tkinter.font as D;J=set(D.families(A.root))if C.platform.startswith(_d)else set();A._base_fam=_AD if C.platform==_X else next((A for A in('Ubuntu',_AE,_AF,_AG)if A in J),'Sans')if C.platform.startswith(_d)else _A4;A._mono_fam='Menlo'if C.platform==_X else _AH if C.platform.startswith(_d)else _A5;A.F_MAIN=D.Font(root=A.root,family=A._base_fam,size=B[_L]);A.F_BOLD=D.Font(root=A.root,family=A._base_fam,size=B[_L],weight=_C);A.F_SUB=D.Font(root=A.root,family=A._base_fam,size=max(8,B[_L]-1));A.F_CAP=D.Font(root=A.root,family=A._base_fam,size=max(8,B[_L]-2),weight=_C);A.F_TITLE=D.Font(root=A.root,family=A._base_fam,size=B[_L]+4,weight=_C);A._watch_pending=_B;A.root.protocol('WM_DELETE_WINDOW',A.on_window_close);A.var_srv=tk.StringVar(value=A.engine.state.get(_v,''));A.var_dir=tk.StringVar(value=A.engine.state.get(_R,''));A.var_net_dir=tk.StringVar(value=A.engine.state.get(_j,''));A.var_cloud_path=tk.StringVar(value=A.engine.state.get(_p,_w));A.var_net=tk.StringVar(value='Не перевірено');A.var_disk=tk.StringVar(value='0 архівів (0 МБ)');A.var_last_bkp=tk.StringVar(value='Перевірка...');A.var_last_bkp_sub=tk.StringVar(value='');A.var_strat=tk.StringVar(value='');A.var_stage=tk.StringVar(value=A.engine.stage);A.var_pct=tk.StringVar(value='0%')
		if C.platform==_X:A.root.bind_class(E,'<Command-v>',lambda e:e.widget.event_generate(G));A.root.bind_class(E,'<Command-c>',lambda e:e.widget.event_generate(H));A.root.bind_class(E,'<Command-x>',lambda e:e.widget.event_generate(I));A.root.bind_class(E,'<Command-a>',lambda e:(e.widget.select_range(0,_M),F)[1])
		elif C.platform.startswith(_d):
			def K(e):
				if not e.state&4:return
				A={54:H,55:G,53:I}
				if e.keycode in A:e.widget.event_generate(A[e.keycode]);return F
				if e.keycode==38:e.widget.select_range(0,_M);return F
			A.root.bind_class(E,'<KeyPress>',K,add='+')
		A._setup_native_menubar();A._build_ui();A.apply_theme_and_mode();A.root.deiconify();A.root.resizable(_D,_D);A.root.minsize(620,420);A.root.update_idletasks();A._last_live_wh=A.root.winfo_width(),A.root.winfo_height();A.engine.log(f"Версія програми: v{SCRIPT_VER} (від {BUILD_DATE})",_e);A.root.after(60,A._apply_window_icon);A.root.after(250,A._watch_size);A.root.after(300,A._poll_ui)
		if hasattr(A.engine,'start_dest_stats_worker'):A.root.after(150,A.engine.start_dest_stats_worker)
		if WINDOWS7_CLOUD_SYNC_PREVIEW and A.engine.state.get(_k):A.root.after(5000,A._retry_pending_cloud_sync)
	def _setup_native_menubar(A):
		import sys
		if sys.platform!=_X:
			try:A.root.configure(menu='')
			except Exception:0
			return
		try:
			D=A.engine.state.get(_U,_V);C=tk.Menu(A.root);B=tk.Menu(C,name='apple',tearoff=0);B.add_command(label=tr(_AI,D)+' HomeGrid Backup',command=A.open_about);B.add_separator();B.add_command(label=tr(_AJ,D)+'...',accelerator='Command+,',command=A.open_settings);C.add_cascade(label=_AK,menu=B)
			try:A.root.createcommand('tk::mac::Quit',A.confirm_exit)
			except Exception:0
			A.root.configure(menu=C)
		except Exception:0
	def open_burger_menu(A):C=A.engine.state.get(_U,_V);D=A._get_palette();B=tk.Menu(A.root,tearoff=0,bg=D[_A],fg=D[_H],activebackground=D[_f],activeforeground=_q,font=(A._base_fam,A.metrics[_L]));B.add_command(label='▶  '+tr('ЗАПУСТИТИ БЕКАП',C),command=A.do_backup);B.add_command(label='🔍  '+tr('Автопошук',C),command=A.do_scan);B.add_command(label='📂  '+tr(_AL,C),command=A.open_backup_folder);B.add_separator();B.add_command(label='📊  '+tr('Статистика',C),command=A.open_stats_modal);B.add_command(label='📋  '+tr('Журнал операцій',C),command=A.open_ops_history);B.add_command(label='🛡  '+tr('Аналіз GFS / SHA-256',C),command=A.open_analyze);B.add_separator();B.add_command(label='⚙  '+tr(_AJ,C),command=A.open_settings);B.add_command(label='ℹ  '+tr(_AI,C),command=A.open_about);B.add_separator();B.add_command(label='✖  '+tr('Вихід',C),command=A.confirm_exit);B.tk_popup(A.btn_burger.winfo_rootx(),A.btn_burger.winfo_rooty()+A.btn_burger.winfo_height())
	def _apply_window_icon(A):
		B=get_app_icon_path()
		if not B:return
		if os.name=='nt':
			try:A.root.iconbitmap(default=B)
			except Exception:0
		try:from PIL import Image as C,ImageTk as D;E=C.open(B).convert('RGBA');A._win_icons=[D.PhotoImage(E.resize((A,A),C.LANCZOS))for A in(16,32,48,64)];A.root.iconphoto(_D,*A._win_icons)
		except Exception:0
	def _warmup_ttk_styles(B):
		try:A=tk.Toplevel(B.root);A.withdraw();A.geometry('1x1+-100+-100');A.update_idletasks();A.destroy()
		except Exception:0
	def _watch_size(A):
		try:
			if not A.root.winfo_exists():return
			if A.root.state()in(_x,_y):A.root.after(2000,A._watch_size);return
			if time.time()>=getattr(A,'_ignore_resize_until',0):
				B,C=A.root.winfo_width(),A.root.winfo_height()
				if B>=500 and C>=350:
					if(B,C)!=A._last_live_wh:A._last_live_wh=B,C;A._watch_pending=B,C
					elif A._watch_pending is not _B:D,E=A._watch_pending;A._watch_pending=_B;A._on_live_resize_done(D,E)
		except Exception:0
		A.root.after(200,A._watch_size)
	def _on_live_resize_done(A,cw,ch):
		C=A.metrics;D=cw+(C['outer_w']-C[_n]);E=ch+(C['outer_h']-C[_o]);B=A.engine.state
		if B.get(_m,0)!=0 or B.get(_h,_i)!=_i:B[_m]=0;B[_h]=_i;commit_state(B)
		A.apply_theme_and_mode(resize_win=_F,live_outer_wh=(D,E));A.root.update_idletasks();A._last_live_wh=A.root.winfo_width(),A.root.winfo_height()
	def show_window(A):
		B='-topmost';import sys;A._ignore_resize_until=time.time()+.7
		try:
			if A.root.state()in(_x,_y):A.root.deiconify();A.root.state(_Y)
			if not sys.platform.startswith(_d):A.root.attributes(B,_D);A.root.update_idletasks();A.root.attributes(B,_F)
			A.root.lift();A.root.focus_force()
		except Exception:0
	def on_window_close(A):
		F='minimize_to_tray';import sys
		if sys.platform==_X:
			if bool(A.engine.state.get(F,_D)):A.root.iconify();A.engine.log('Вікно згорнуто у Dock (програма продовжує роботу).',_e);return
			if getattr(A,'_exit_confirm_open',_F):from gui.tray import _force_quit_app as G;G(A.engine);return
			A._exit_confirm_open=_D;A.confirm_exit();return
		if NO_TRAY or not A.engine.state.get('tray_enabled',_D):A.root.iconify();A.engine.log('Вікно згорнуто в панель задач (трей вимкнено).',_e);return
		C=bool(A.engine.state.get(F,_D))
		if C:from gui.tray import HAS_TRAY as E,_start_tray_thread as H
		else:E=_F
		if C and E:
			try:
				if A.engine.tray_icon is _B:H(A.engine)
				D=getattr(A.engine,'tray_ready_event',_B);I=bool(A.engine.tray_icon is not _B and D is not _B and(D.is_set()or D.wait(2.5))and getattr(A.engine,'tray_ready',_F))
				if I:A.root.withdraw();A.engine.log('Значок системного трею запущено; вікно приховано.',_e);return
			except Exception as J:A.engine.tray_error=str(J);A.engine.log('Не вдалося перевірити запуск значка системного трею.',_z)
		if sys.platform.startswith(_d)and C:
			A.root.iconify();B=getattr(A.engine,'tray_error','')
			if not B:from gui.tray import _tray_problem as K;B=K()
			A.engine.log('Запуск трею не підтверджено; вікно згорнуто на панель задач.',_S)
			if B:A.engine.log(f"[TRAY DETAIL] {B}",_S)
			return
		A.confirm_exit()
	def _get_palette(B):
		A='#000000';C=B.engine.state.get(_r,_Z)
		if B.engine.state.get(_a,_F):return{'bg':A,_A:'#050505',_N:'#0a0a0a',_O:'#4b5563',_H:'#f3f4f6',_I:'#9ca3af',_f:'#1d4ed8',_K:'#047857',_b:'#b45309',_T:'#b91c1c',_P:'#38bdf8',_A6:A,'log_bg':A,_A7:_q,_AM:_q,'font':_A5,'relief':_A0}
		return THEMES.get(C,THEMES[_Z])
	def _on_srv_key_release(A,event=_B):
		B=event
		if B and B.keysym in('BackSpace','Delete','Left','Right','Home','End','Shift_L','Shift_R','Control_L','Control_R'):return
		if A._srv_typing_timer:
			try:A.root.after_cancel(A._srv_typing_timer)
			except Exception:0
		A._srv_typing_timer=A.root.after(800,A._apply_srv_autofill)
	def _build_ui(A):
		h='Налаштування pCloud';g='<Return>';f='bottom';Y='top';Q='<FocusOut>';P='both';K='<Button-1>';I='nsew';H='ew';G='right';D='x';E,F=A.metrics['pad_y'],A.metrics['pad_x'];B=A.metrics[_L];A.var_cloud_st=tk.StringVar(value='pCloud: вимкнено');A.header=tk.Frame(A.root,padx=F,pady=max(6,E),bd=0,highlightthickness=1);A.header.pack(side=Y,fill=D);L=tk.Frame(A.header);L.pack(side=_E,fill=D,expand=_D);A.btn_burger=tk.Button(L,text='☰',command=A.open_burger_menu,padx=8,pady=2,bd=0,cursor=_G);A.btn_burger.pack(side=_E,padx=(0,8));A.lbl_title=tk.Label(L,text=_AK,font=(A._base_fam,B+4,_C));A.lbl_title.pack(side=_E);A.lbl_sub=tk.Label(L,text='',font=(A._base_fam,1));M=tk.Frame(A.header);M.pack(side=G);A.btn_cloud_badge=tk.Button(M,textvariable=A.var_cloud_st,command=lambda:A.open_settings(initial_tab=2),padx=10,pady=3,bd=0,cursor=_G);A.btn_theme=tk.Button(M,text=_AN,command=A.toggle_theme_quick,padx=10,pady=3,bd=0,cursor=_G);A.btn_theme.pack(side=_E,padx=(0,6));A.btn_mode=tk.Button(M,text='Графіка ▾',command=A.open_mode_menu,padx=8,pady=3,bd=0,cursor=_G);A.btn_mode.pack(side=_E);A.footer=tk.Frame(A.root,padx=F,pady=max(6,E),bd=0,highlightthickness=1);A.footer.pack(side=f,fill=D);A.body=tk.Frame(A.root,padx=F,pady=E);A.body.pack(side=Y,fill=P,expand=_D);A.top_split=tk.Frame(A.body);A.top_split.pack(fill=D,pady=(0,E));A.top_split.columnconfigure(0,weight=68);A.top_split.columnconfigure(1,weight=32);A.card_conn=tk.Frame(A.top_split,padx=F,pady=E,bd=0,highlightthickness=1);A.card_conn.grid(row=0,column=0,sticky=I,padx=(0,max(6,F//2)));R=tk.Frame(A.card_conn,bd=0,highlightthickness=0);R.pack(fill=D,pady=(0,4));A.lbl_c1=tk.Label(R,text='Підключення та папки',font=(A._base_fam,B,_C));A.lbl_c1.pack(side=_E);A.var_srv_badge=tk.StringVar(value='');A.lbl_srv_badge=tk.Label(R,textvariable=A.var_srv_badge,font=(A._base_fam,max(8,B-1),_C));A.lbl_srv_badge.pack(side=G);C=tk.Frame(A.card_conn,bd=0,highlightthickness=0);C.pack(fill=D);C.columnconfigure(0,minsize=max(106,B*11));C.columnconfigure(1,weight=1);C.columnconfigure(2,minsize=max(34,B*3),uniform='cc_mid');C.columnconfigure(3,minsize=max(102,B*10),uniform='cc_act');A.l_srv=tk.Label(C,text='Сервер:',anchor=_J,font=(A._base_fam,B));A.l_srv.grid(row=0,column=0,sticky=_J,padx=(0,6),pady=3);S=tk.Frame(C,bd=0,highlightthickness=0);S.grid(row=0,column=1,columnspan=2,sticky=H,padx=(0,4),pady=3);A.ent_srv=tk.Entry(S,width=1,textvariable=A.var_srv,bd=0,highlightthickness=1,font=(A._base_fam,B));A.ent_srv.pack(side=_E,fill=D,expand=_D,ipady=4);A.btn_scan=tk.Button(S,text=_A8,command=A.on_scan_btn_click,padx=10,pady=2,bd=0,highlightthickness=1,cursor=_G);A.btn_scan.pack(side=_E,padx=(6,0),fill='y');A.btn_conn=tk.Button(C,text='Підключити',command=A.do_connect,pady=2,bd=0,cursor=_G);A.btn_conn.grid(row=0,column=3,sticky=I,padx=(4,0),pady=3);A.l_fav=tk.Label(C,text='Обрані:',anchor=_J,font=(A._base_fam,max(8,B-1)));A.l_fav.grid(row=1,column=0,sticky=_J,padx=(0,6),pady=2);A.fav_bar=tk.Frame(C,bd=0,highlightthickness=0);A.fav_bar.grid(row=1,column=1,columnspan=2,sticky=H,padx=(0,4),pady=2);A.btn_hist=tk.Button(C,text='Історія',command=A.open_history_modal,pady=1,bd=0,highlightthickness=1,cursor=_G);A.btn_hist.grid(row=1,column=3,sticky=I,padx=(4,0),pady=2);A.conn_sep=tk.Frame(C,height=1,bd=0,highlightthickness=0);A.conn_sep.grid(row=2,column=0,columnspan=4,sticky=H,pady=(5,4));A.l_copies_hdr=tk.Label(C,text='Сховища:',anchor=_J,font=(A._base_fam,max(8,B-1),_C));A.l_copies_hdr.grid(row=3,column=0,columnspan=4,sticky=_J,pady=(0,2));T=tk.Frame(C,bd=0,highlightthickness=0);T.grid(row=4,column=0,sticky=_J,padx=(8,6),pady=3);A.var_loc_en=tk.BooleanVar(value=bool(A.engine.state.get(_AO,_D)));A.chk_loc_tog=HomeGridToggle(T,variable=A.var_loc_en,command=lambda:(A.engine.state.update(local_enabled=bool(A.var_loc_en.get())),commit_state(A.engine.state),A._update_mirror_btn()),compact=_D,palette=A._get_palette(),font_sz=max(8,B-1));A.chk_loc_tog.pack(side=_E,padx=(0,5));A.l_dir=tk.Label(T,text='Локально',anchor=_J,font=(A._base_fam,max(8,B-1)),cursor=_G);A.l_dir.pack(side=_E);A.l_dir.bind(K,lambda _e:A.chk_loc_tog._on_click_compact());A.ent_dir=tk.Entry(C,width=1,textvariable=A.var_dir,bd=0,highlightthickness=1,font=(A._base_fam,B));A.ent_dir.grid(row=4,column=1,sticky=H,padx=(0,4),pady=3,ipady=3);A.btn_dir=tk.Button(C,text='📂',command=A.choose_dir,pady=1,bd=0,highlightthickness=1,cursor=_G);A.btn_dir.grid(row=4,column=2,sticky=I,padx=2,pady=3);A.var_loc_st=tk.StringVar(value='—');A.lbl_loc_st=tk.Label(C,textvariable=A.var_loc_st,anchor=_J,font=(A._base_fam,max(8,B-1)),cursor=_G);A.lbl_loc_st.grid(row=4,column=3,sticky=_J,padx=(6,0),pady=3);A.lbl_loc_st.bind(K,lambda _e:A.open_backup_folder());A.btn_open_dir=tk.Button(C,text='↗',command=A.open_backup_folder);U=tk.Frame(C,bd=0,highlightthickness=0);U.grid(row=5,column=0,sticky=_J,padx=(8,6),pady=2);A.var_net_en=tk.BooleanVar(value=bool(A.engine.state.get(_l,_F))and bool(A.var_net_dir.get().strip()));A.chk_net_tog=HomeGridToggle(U,variable=A.var_net_en,command=A.toggle_net_dir,compact=_D,palette=A._get_palette(),font_sz=max(8,B-1));A.chk_net_tog.pack(side=_E,padx=(0,5));A.l_net=tk.Label(U,text='Мережа',anchor=_J,font=(A._base_fam,max(8,B-1)),cursor=_G);A.l_net.pack(side=_E);A.l_net.bind(K,lambda _e:A.chk_net_tog._on_click_compact());A.ent_net=tk.Entry(C,width=1,textvariable=A.var_net_dir,state=_W,bd=0,highlightthickness=1,font=(A._base_fam,B));A.ent_net.grid(row=5,column=1,sticky=H,padx=(0,4),pady=2,ipady=3);A.btn_net=tk.Button(C,text='📂',command=A.choose_net_dir,state=_W,pady=1,bd=0,highlightthickness=1,cursor=_G);A.btn_net.grid(row=5,column=2,sticky=I,padx=2,pady=2);A.var_net_st=tk.StringVar(value='—');A.lbl_net_st=tk.Label(C,textvariable=A.var_net_st,anchor=_J,font=(A._base_fam,max(8,B-1)));A.lbl_net_st.grid(row=5,column=3,sticky=_J,padx=(6,0),pady=2);Z=tk.Frame(C,bd=0,highlightthickness=0);A.var_cld_en=tk.BooleanVar(value=bool(A.engine.state.get(_k,_F)));A.chk_cld_tog=HomeGridToggle(Z,variable=A.var_cld_en,command=A.toggle_cloud_quick,compact=_D,palette=A._get_palette(),font_sz=max(8,B-1));A.chk_cld_tog.pack(side=_E,padx=(0,5));A.l_cld=tk.Label(Z,text='pCloud',anchor=_J,font=(A._base_fam,max(8,B-1)),cursor=_G);A.l_cld.pack(side=_E);A.l_cld.bind(K,lambda _e:A.chk_cld_tog._on_click_compact());A.ent_cld=tk.Entry(C,width=1,textvariable=A.var_cloud_path,state=_W,bd=0,highlightthickness=1,font=(A._base_fam,B));A.btn_cld_cfg=tk.Button(C,text='⚙',command=lambda:A.open_settings(initial_tab=2),pady=1,bd=0,highlightthickness=1,cursor=_G);A.var_cld_st=tk.StringVar(value='● вимкнено');A.lbl_cld_st=tk.Label(C,textvariable=A.var_cld_st,anchor=_J,font=(A._base_fam,max(8,B-1)),cursor=_G);A.lbl_cld_st.bind(K,lambda _e:A.open_settings(initial_tab=2));A.ent_srv.bind(g,lambda e:(A._apply_srv_autofill(),A.do_connect()));A.ent_srv.bind(Q,lambda e:(A._apply_srv_autofill(),A._render_fav_servers()));A.ent_srv.bind('<KeyRelease>',A._on_srv_key_release);A.ent_dir.bind(Q,lambda e:A.save_dir_manual());A.ent_net.bind(Q,lambda e:A.save_net_manual());A.ent_cld.bind(Q,lambda e:A.save_cloud_path_manual());A.ent_cld.bind(g,lambda e:A.save_cloud_path_manual());A.card_stat=tk.Frame(A.top_split,padx=F,pady=E,bd=0,highlightthickness=1);A.card_stat.grid(row=0,column=1,sticky=I,padx=(max(6,F//2),0));A.lbl_c2=tk.Label(A.card_stat,text='Сховище та аналітика',font=(A._base_fam,B,_C),anchor=_s);A.lbl_c2.pack(fill=D,pady=(0,6));V=tk.Frame(A.card_stat);V.pack(anchor=_s,pady=2);A.t2_cap=tk.Label(V,text='ЛОКАЛЬНО:',font=(A._base_fam,max(8,B-1),_C));A.t2_cap.pack(side=_E,padx=(0,6));A.t2_val=tk.Label(V,textvariable=A.var_disk,font=(A._base_fam,B,_C));A.t2_val.pack(side=_E);A.dest_rows={}
		for(a,i)in((_t,'МЕРЕЖА:'),(_g,'PCLOUD:')):
			N=tk.Frame(A.card_stat);b=tk.StringVar(value='—');c=tk.Label(N,text=i,font=(A._base_fam,max(8,B-2),_C));c.pack(side=_E,padx=(0,5));d=tk.Label(N,textvariable=b,font=(A._base_fam,max(8,B-1),_C));d.pack(side=_E)
			if a==_g:A.btn_refresh_cld=tk.Button(N,text=chr(8635),command=A._force_refresh_pcloud_stats,padx=5,pady=0,bd=0,highlightthickness=1,cursor=_G);A.btn_refresh_cld.pack(side=_E,padx=(6,0));ToolTip(A.btn_refresh_cld,'Оновити статистику pCloud')
			A.dest_rows[a]=N,c,d,b
		W=tk.Frame(A.card_stat);W.pack(anchor=_s,pady=(2,0));A.t3_cap=tk.Label(W,text='ОСТАННІЙ:',font=(A._base_fam,max(8,B-1),_C));A.t3_cap.pack(side=_E,padx=(0,6));A.t3_val=tk.Label(W,textvariable=A.var_last_bkp,font=(A._base_fam,B,_C));A.t3_val.pack(side=_E);A.t3_sub=tk.Label(A.card_stat,textvariable=A.var_last_bkp_sub,font=(A._base_fam,max(8,B-1),_C));A.t3_sub.pack(anchor=_s,pady=(0,2));A.stat_btns=tk.Frame(A.card_stat);A.stat_btns.pack(fill=D,pady=(8,0));A.stat_btns.columnconfigure(0,weight=1);A.stat_btns.columnconfigure(1,weight=1);A.btn_stats=tk.Button(A.stat_btns,text='📊 Локально',command=A.open_stats_modal,pady=4,bd=0,cursor=_G);A.btn_stats.grid(row=0,column=0,sticky=H,padx=(0,4),pady=2);A.btn_cstats=tk.Button(A.stat_btns,text='🌐 Мережа',command=A.open_cloud_stats_modal,pady=4,bd=0,cursor=_G);A.btn_cstats.grid(row=0,column=1,sticky=H,padx=(4,0),pady=2);A.btn_ops_hist=tk.Button(A.stat_btns,text='📋 Журнал',command=A.open_ops_history,pady=4,bd=0,cursor=_G);A.btn_ops_hist.grid(row=1,column=0,sticky=H,padx=(0,4),pady=2);A.btn_analyze=tk.Button(A.stat_btns,text=_AP,command=A.open_analyze,pady=4,bd=0,cursor=_G);A.btn_analyze.grid(row=1,column=1,sticky=H,padx=(4,0),pady=2);A.card_prog=tk.Frame(A.body,padx=F,pady=E,bd=0,highlightthickness=1);A.card_prog.pack(side=f,fill=D,pady=(E,0));J=tk.Frame(A.card_prog);J.pack(fill=D,pady=(0,6));A.lbl_stage=tk.Label(J,textvariable=A.var_stage,font=(A._base_fam,B+2,_C));A.lbl_stage.pack(side=_E);A.lbl_pct=tk.Label(J,textvariable=A.var_pct,font=(A._base_fam,B+4,_C));A.lbl_pct.pack(side=G);A.lbl_pill=tk.Label(J,text=_A9,padx=10,pady=2,bd=0,font=(A._base_fam,B,_C));A.lbl_pill.pack(side=G,padx=(0,12));A.lbl_load_3s=tk.Label(J,text='CPU: --% | RAM: --%',font=(A._base_fam,max(8,B-1),_C));A.lbl_load_3s.pack(side=G,padx=(0,12));A.root.after(1000,A._tick_3s_loader);A.pbar=StyledProgressBar(A.card_prog,height=84);A.pbar.pack(fill=D,ipady=4);A.card_log=tk.Frame(A.body,padx=F,pady=E,bd=0,highlightthickness=1);A.card_log.pack(side=Y,fill=P,expand=_D);O=tk.Frame(A.card_log);O.pack(fill=D,pady=(0,4));A.lbl_c4=tk.Label(O,text='Системний лог',font=(A._base_fam,B,_C));A.lbl_c4.pack(side=_E);A.btn_clear_log=tk.Button(O,text='Очистити',command=A.clear_log_view,padx=8,pady=1,bd=0,cursor=_G);A.btn_clear_log.pack(side=G);A.btn_open_log=tk.Button(O,text='📄 backup.log',command=A.open_raw_log_file,padx=8,pady=1,bd=0,cursor=_G);A.btn_open_log.pack(side=G,padx=(0,6));X=tk.Frame(A.card_log);X.pack(fill=P,expand=_D);A.txt_log=tk.Text(X,height=10,wrap='word',state=_W,font=(A._base_fam,B),bd=0,highlightthickness=1,padx=10,pady=6,spacing1=1,spacing3=1);e=tk.Scrollbar(X,command=A.txt_log.yview);A.txt_log.configure(yscrollcommand=e.set);e.pack(side=G,fill='y');A.txt_log.pack(side=_E,fill=P,expand=_D);A.txt_log.bind('<Configure>',lambda _e:A._center_log_vertically(),add='+');A.btn_start=tk.Button(A.footer,text='▶ ЗАПУСТИТИ БЕКАП',command=A.do_backup,font=(A._base_fam,B,_C),padx=18,pady=5,bd=0,cursor=_G);A.btn_start.pack(side=_E,padx=(0,10));A.btn_strat=tk.Button(A.footer,text='⚙ Налаштування',command=A.open_settings,padx=12,pady=5,bd=0,cursor=_G);A.btn_strat.pack(side=_E,padx=6);A.btn_about=tk.Button(A.footer,text='ℹ Про програму',command=A.open_about,padx=12,pady=5,bd=0,cursor=_G);A.btn_about.pack(side=_E,padx=6);A.btn_exit=tk.Button(A.footer,text='✖ Вихід',command=A.confirm_exit,padx=14,pady=5,bd=0,cursor=_G);A.btn_exit.pack(side=G)
		for(j,k)in((A.btn_scan,'Автоматичний пошук серверів HomeGrid Monitor у локальній мережі'),(A.btn_hist,'Відкрити список раніше збережених адрес серверів'),(A.btn_dir,'Обрати папку'),(A.btn_open_dir,_AL),(A.btn_net,'Обрати мережеву папку'),(A.ent_cld,'Папка у хмарі pCloud (напр. HomeGridBackup)'),(A.btn_cld_cfg,h),(A.lbl_cld_st,h),(A.btn_open_log,'Відкрити текстовий файл backup.log')):ToolTip(j,k)
	def open_raw_log_file(C):
		import subprocess as A,sys;D=get_logs_dir(C.engine.state);os.makedirs(D,exist_ok=_D);B=os.path.join(D,'backup.log')
		if not os.path.isfile(B):
			with open(B,_J,encoding=_A1)as E:E.write('')
		try:
			if os.name=='nt':os.startfile(B)
			elif sys.platform==_X:A.Popen(['open','-t',B])
			else:A.Popen(['xdg-open',B],stdin=A.DEVNULL,stdout=A.DEVNULL,stderr=A.DEVNULL)
		except Exception as F:C.engine.log(f"Не вдалося відкрити backup.log: {F}",_S)
	def apply_theme_and_mode(A,resize_win=_F,live_outer_wh=_B):
		Q=resize_win;A.metrics=_calc_screen_metrics(A.root,A.engine.state.get(_h,_i),A.engine.state.get(_m,0),live_outer_wh=live_outer_wh);E=A.metrics
		if Q:
			try:
				if A.root.state()=='zoomed':A.root.state(_Y)
			except Exception:0
			A.root.minsize(min(620,E[_n]),min(420,E[_o]));A.root.geometry(f"{E[_n]}x{E[_o]}+{E["pos_x"]}+{E["pos_y"]}")
		B=A._get_palette();C=E[_L];A.root._cur_font_sz=C;I,J=E['btn_px'],E['btn_py'];R,S=E['pad_x'],E['pad_y'];K=bool(A.engine.state.get(_a,_F));Z=A.engine.state.get(_r,_Z);import sys
		if sys.platform==_X:D='Menlo'if K else _AD
		elif sys.platform.startswith(_d):import tkinter.font as a;T=set(a.families(A.root))if not hasattr(A,'_lnx_f')else A._lnx_f;A._lnx_f=T;D=_AH if K else next((A for A in('Ubuntu',_AE,_AF,_AG)if A in T),'Sans')
		else:D=_A5 if K else B.get('font',_A4)
		U=_A0 if K else B.get('relief',_A0);b=2 if U in('raised','groove')else 1;A.F_MAIN.configure(family=D,size=C);A.F_BOLD.configure(family=D,size=C);A.F_SUB.configure(family=D,size=max(8,C-1));A.F_CAP.configure(family=D,size=max(8,C-2));A.F_TITLE.configure(family=D,size=C+4);M,F,G,N=A.F_MAIN,A.F_BOLD,A.F_SUB,A.F_CAP
		try:A.root.option_add('*TCombobox*Listbox.font',M)
		except Exception:0
		A.root.configure(bg=B['bg']);A.body.configure(bg=B['bg'],padx=R,pady=S)
		if hasattr(A,'top_split'):A.top_split.configure(bg=B['bg'])
		if hasattr(A,'lbl_c2'):A.lbl_c2.configure(bg=B[_A],fg=B[_H],font=F)
		if hasattr(A,'btn_burger'):A.btn_burger.configure(bg=B[_N],fg=B[_H],font=F)
		if hasattr(A,'btn_open_log'):A.btn_open_log.configure(bg=B[_N],fg=B[_P],font=G)
		if hasattr(A,'btn_cloud_badge'):V=bool(A.engine.state.get(_k));A.var_cloud_st.set('☁ pCloud: ON'if V else'☁ pCloud: OFF');A.btn_cloud_badge.configure(bg=B[_N],fg=B[_K]if V else B[_I],font=G)
		for c in(A.header,A.card_conn,A.card_stat,A.card_prog,A.card_log,A.footer):c.configure(bg=B[_A],highlightbackground=B[_O],padx=R,pady=S,relief=U,bd=b)
		def W(node):
			for C in node.winfo_children():
				if isinstance(C,tk.Frame)and not isinstance(C,HomeGridToggle):C.configure(bg=B[_O]if C is getattr(A,'conn_sep',_B)else B[_A],bd=0,highlightthickness=0);W(C)
		for d in(A.header,A.card_conn,A.card_stat,A.card_prog,A.card_log):W(d)
		A.lbl_title.configure(bg=B[_A],fg=B[_H],font=(D,C+4,_C));A.lbl_sub.configure(bg=B[_A],fg=B[_I],font=G);A.lbl_srv_badge.configure(bg=B[_A],bd=0,highlightthickness=0)
		for P in(A.lbl_c1,A.lbl_c4):P.configure(bg=B[_A],fg=B[_H],font=F)
		A.lbl_stage.configure(bg=B[_A],fg=B[_H],font=(D,C+2,_C));A.lbl_pct.configure(bg=B[_A],fg=B[_K],font=(D,C+4,_C))
		for P in(A.l_srv,A.l_fav):P.configure(bg=B[_A],fg=B[_I],font=M)
		A.l_copies_hdr.configure(bg=B[_A],fg=B[_I],font=N)
		for e in(A.ent_srv,A.ent_dir,A.ent_net,A.ent_cld):e.configure(bg=B[_A6],fg=B[_H],insertbackground=B[_H],highlightbackground=B[_O],highlightcolor=B[_f],font=M)
		X=F;A.t2_cap.configure(bg=B[_A],fg=B[_I],font=N);A.t2_val.configure(bg=B[_A],fg=B[_K],font=X)
		for(j,f,g,k)in getattr(A,_AQ,{}).values():f.configure(bg=B[_A],fg=B[_I],font=N);g.configure(bg=B[_A],fg=B[_P],font=G)
		if hasattr(A,'t3_cap'):A.t3_cap.configure(bg=B[_A],fg=B[_I],font=N);A.t3_val.configure(bg=B[_A],fg=B[_P],font=X)
		if hasattr(A,'t3_sub'):A.t3_sub.configure(bg=B[_A],fg=B[_K],font=G)
		if hasattr(A,'lbl_pct'):A.lbl_pct.configure(bg=B[_A],fg=B[_K],font=(D,C+4,_C))
		A.pbar.configure(height=max(84,C*6+20));A.txt_log.configure(bg=B['log_bg'],fg=B[_H],font=(D,C));A.txt_log.tag_configure('dim',foreground=B[_I]);A.txt_log.tag_configure(_Q,foreground=B[_H]);A.txt_log.tag_configure(_S,foreground=B[_b]);A.txt_log.tag_configure(_z,foreground=B[_T]);A.txt_log.tag_configure(_e,foreground=B[_H]);A.txt_log.tag_configure('b_ok',background='#dcfce7',foreground='#15803d',font=(D,max(8,C-1),_C));A.txt_log.tag_configure('b_info',background='#dbeafe',foreground='#1d4ed8',font=(D,max(8,C-1),_C));A.txt_log.tag_configure('b_warn',background='#fef3c7',foreground='#b45309',font=(D,max(8,C-1),_C));A.txt_log.tag_configure('b_err',background='#fee2e2',foreground='#b91c1c',font=(D,max(8,C-1),_C));H=B[_I]
		for O in(A.btn_scan,A.btn_hist,A.btn_dir,A.btn_open_dir,A.btn_net,A.btn_cld_cfg,A.btn_about):O.configure(highlightbackground=B[_O]);O.configure(bg=B[_N],fg=B[_H],disabledforeground=H,activebackground=B[_O],activeforeground=B[_H],font=M,padx=I,pady=J)
		A.btn_clear_log.configure(bg=B[_N],fg=B[_I],disabledforeground=H,activebackground=B[_O],activeforeground=B[_H],font=G,padx=max(6,I-2),pady=1);A.btn_conn.configure(bg=B[_f],fg=B[_A7],disabledforeground=H,font=F,padx=I,pady=J);A.btn_start.configure(bg=B[_K],fg=B[_AM],disabledforeground=H,font=F,padx=I+4,pady=J+1)
		for O in(A.btn_analyze,A.btn_ops_hist,A.btn_stats,A.btn_cstats,A.btn_strat):O.configure(bg=B[_N],fg=B[_P],disabledforeground=H,font=F,padx=I,pady=J)
		A.btn_exit.configure(bg=B[_A],fg=B[_T],disabledforeground=H,font=F,padx=I,pady=J)
		if hasattr(A,'btn_refresh_cld'):A.btn_refresh_cld.configure(bg=B[_N],fg=B[_P],highlightbackground=B[_O],font=G)
		if hasattr(A,'btn_pick_lan'):A.btn_pick_lan.configure(bg=B[_N],fg=B[_K],disabledforeground=H,font=F,padx=I,pady=J)
		if hasattr(A,'btn_theme'):h=_AN if Z==_Z else'🌙 Темна тема';A.btn_theme.configure(text=h,bg=B[_N],fg=B[_H],activebackground=B[_O],activeforeground=B[_H],relief=_A0,bd=1,font=G,padx=8,pady=2)
		Y=f"{E["outer_w"]}×{E["outer_h"]}";i=f"LITE ({Y}) ▾"if K else f"Графіка ({Y}) ▾";A.btn_mode.configure(text=i,bg=B[_A],fg=B[_I],relief='flat',bd=0,disabledforeground=H,font=G,padx=6,pady=2);A.btn_scan.configure(fg=B[_P],font=F);A._render_fav_servers();A._update_mirror_btn()
		try:
			if Q:A._ignore_resize_until=time.time()+.5
			A.root.update_idletasks();A.root.minsize(620,420)
		except Exception:0
		L=A.engine.state.get(_U,_V);A.root._cur_lang=L;A.root.title(tr(f"HomeGrid Backup v{SCRIPT_VER} (від {BUILD_DATE})",L));apply_widget_i18n(A.root,L);A.btn_cstats.configure(text='🌐 Мережа'if L=='uk'else'🌐 Network');A.btn_analyze.configure(text=_AP if L=='uk'else'🛡 Verify SHA');fix_mac_buttons(A.root,B)
		if hasattr(A,'_setup_native_menubar'):A._setup_native_menubar()
	def on_scan_btn_click(A):
		D=getattr(A.engine,_AR,[])or[]
		if not D:A.do_scan();return
		E=A.engine.state.get(_U,_V);C=A._get_palette();G=A.metrics[_L];B=tk.Menu(A.root,tearoff=0,bg=C[_A],fg=C[_H],activebackground=C[_f],activeforeground=_q,font=(A._base_fam,G))
		for(F,H,I)in D:B.add_command(label=tr(f"{F}   (TCP: {H} мс, API: {I} мс)",E),command=lambda u=F:A._select_discovered_server(u))
		B.add_separator();B.add_command(label=tr(_A8,E),command=A.do_scan);B.tk_popup(A.btn_scan.winfo_rootx(),A.btn_scan.winfo_rooty()+A.btn_scan.winfo_height())
	def _select_discovered_server(A,url):B=url;A.var_srv.set(B);A.engine.state[_v]=B;A._last_synced_srv=B;A._render_fav_servers();A.engine.log(f"Обрано виявлений у мережі сервер: {B}",_Q)
	def _add_current_to_favs(A):
		A._apply_srv_autofill();B=A.var_srv.get().strip().rstrip('/')
		if not B:return
		C=[A.strip().rstrip('/')for A in A.engine.state.get(_u)or[]if A.strip()]
		if B not in C:C.append(B);A.engine.state[_u]=C[:8];commit_state(A.engine.state);A._render_fav_servers()
	def _remove_from_favs(A,url):B=(url or'').strip().rstrip('/');A.engine.state[_u]=[A for A in A.engine.state.get(_u)or[]if A.strip().rstrip('/')!=B];commit_state(A.engine.state);A._render_fav_servers()
	def _pick_fav_server(A,url):B=url;A.var_srv.set(B);A.engine.state[_v]=B;A._last_synced_srv=B;commit_state(A.engine.state);A._render_fav_servers()
	def _render_fav_servers(A):
		if not hasattr(A,'fav_bar')or not A.fav_bar.winfo_exists():return
		for J in A.fav_bar.winfo_children():J.destroy()
		B=A._get_palette();K=A.engine.state.get(_U,_V);I=max(8,A.metrics[_L]-1);F=(A.var_srv.get()or'').strip().rstrip('/');G=[A.strip().rstrip('/')for A in A.engine.state.get(_u)or[]if A.strip()]
		for C in G[:4]:D=C==F;E=C.replace('http://','').replace('https://','');E=E[:19]+'...'if len(E)>22 else E;L='★'if D else'☆';H=tk.Button(A.fav_bar,text=f"{L} {E}",command=lambda t=C:A._pick_fav_server(t),bg=B[_f]if D else B[_N],fg=B[_A7]if D else B[_H],activebackground=B[_O],activeforeground=B[_H],bd=0,highlightthickness=1,highlightbackground=B[_P]if D else B[_O],font=(A._base_fam,I,_C if D else _Y),padx=8,pady=1,cursor=_G);H.pack(side=_E,padx=(0,4));H.bind('<Button-3>',lambda _e,t=C:A._remove_from_favs(t));ToolTip(H,f"{C} (ПКМ — прибрати з обраних)")
		if F and F not in G and len(G)<8:M=tk.Button(A.fav_bar,text=tr('+ Додати',K),command=A._add_current_to_favs,bg=B[_N],fg=B[_P],activebackground=B[_O],activeforeground=B[_H],bd=0,highlightthickness=1,highlightbackground=B[_O],font=(A._base_fam,I,_C),padx=8,pady=1,cursor=_G);M.pack(side=_E,padx=(0,4))
	def toggle_theme_quick(A):B=A.engine.state.get(_r,_Z);A.engine.state[_r]='light'if B==_Z else _Z;A.engine.state[_a]=_F;commit_state(A.engine.state);A.apply_theme_and_mode(resize_win=_F)
	def open_mode_menu(A):
		D=A._get_palette();F=A.metrics[_L];B=tk.Menu(A.root,tearoff=0,bg=D[_A],fg=D[_H],activebackground=D[_f],activeforeground=_q,font=(A._base_fam,F));C=A.engine.state.get(_U,_V);B.add_command(label=tr('✨ Повна графіка (стандартний режим)',C),command=lambda:A._set_graphic_mode(_F));B.add_command(label=tr('⚡ Ультралегкий LITE-режим (швидкий текст)',C),command=lambda:A._set_graphic_mode(_D));B.add_separator();G=A.engine.state.get(_h,_i)
		for(E,H)in UI_SCALE_LABELS:I='✔ 'if E==G else'    ';B.add_command(label=f"{I}{tr(H,C)}",command=lambda c=E:A._set_screen_scale_quick(c))
		B.add_separator();B.add_command(label=tr('⚙️ Налаштування екрана та шрифту...',C),command=A.open_settings);J=A.btn_mode.winfo_rootx();K=A.btn_mode.winfo_rooty()+A.btn_mode.winfo_height();B.tk_popup(J,K)
	def _set_graphic_mode(A,is_lite):A.engine.state[_a]=bool(is_lite);commit_state(A.engine.state);A.apply_theme_and_mode(resize_win=_D)
	def _set_screen_scale_quick(A,scale_code):A.engine.state[_h]=scale_code;A.engine.state[_m]=0;commit_state(A.engine.state);A.apply_theme_and_mode(resize_win=_D)
	def _apply_srv_autofill(A):
		B=A.var_srv.get().strip()
		if not B:return
		C,E=normalize_server_url(B)
		if C:
			D=f"{C}!"if E else C
			if D!=B:
				A.var_srv.set(D)
				try:A.ent_srv.icursor(_M)
				except Exception:0
	def _update_mirror_btn(A):
		Q='net';L='● офлайн';import shutil as R;F=A.engine.state.get(_U,_V);M=bool(getattr(A.engine,'is_running',_F));I=bool(A.engine.state.get(_AO,_D));J=bool(A.engine.state.get(_l,_F));S=(A.var_dir.get()or'').strip();T=(A.var_net_dir.get()or'').strip();B=A._get_palette();N=A.metrics[_L];C=getattr(A,'_base_fam',_A4),max(8,N-1);A.var_loc_en.set(I);A.var_net_en.set(J)
		for U in(A.chk_loc_tog,A.chk_net_tog):U.apply_style(palette=B,state=_W if M else _Y,font_sz=max(8,N-1))
		A.l_dir.configure(bg=B[_A],fg=B[_H]if I else B[_I],font=C);A.l_net.configure(bg=B[_A],fg=B[_H]if J else B[_I],font=C)
		with A.engine.lock:G=dict((getattr(A.engine,_A2,{})or{}).get(_t)or{})if(getattr(A.engine,_A2,{})or{}).get(_t)is not _B else _B
		for(V,O,W,X,D,E,K)in(('loc',I,A.ent_dir,A.btn_dir,A.var_loc_st,A.lbl_loc_st,S),(Q,J,A.ent_net,A.btn_net,A.var_net_st,A.lbl_net_st,T)):
			P=_W if M or not O else _Y;W.configure(state=P,bg=B[_A6],fg=B[_H],disabledbackground=B[_A],disabledforeground=B[_I]);X.configure(state=P)
			if not O or not K:D.set('—');E.configure(bg=B[_A],fg=B[_I],font=C)
			elif V==Q:
				if G is _B:D.set('● ...');E.configure(bg=B[_A],fg=B[_I],font=C)
				elif G.get(_Q):H=G.get(_AA,-1);D.set(f"● {H} "+('ГБ'if F=='uk'else'GB')if H>=0 else'● Online');E.configure(bg=B[_A],fg=B[_b]if G.get('stale')else B[_K],font=C)
				else:D.set(tr(L,F));E.configure(bg=B[_A],fg=B[_T],font=C)
			else:
				try:
					if os.path.isdir(K):H=round(R.disk_usage(K).free/1024**3,1);D.set(f"● {H} "+('ГБ'if F=='uk'else'GB'));E.configure(bg=B[_A],fg=B[_K],font=C)
					else:D.set(tr(L,F));E.configure(bg=B[_A],fg=B[_T],font=C)
				except Exception:D.set(tr(L,F));E.configure(bg=B[_A],fg=B[_T],font=C)
		if hasattr(A.engine,_AB):A.engine.request_dest_stats_refresh()
	def open_backup_folder(A):B=A.var_dir.get().strip()or A.engine.state.get(_R)or DEFAULT_BACKUP_DIR;open_folder_native(B)
	def _center_log_vertically(A):
		B='vcenter'
		try:
			if not hasattr(A,'txt_log')or not A.txt_log.winfo_exists():return
			C=A.txt_log.winfo_height()
			if C<=24:return
			D=A.txt_log.get(_c,'end-1c')
			if not D.strip():A.txt_log.tag_remove(B,_c,_M);return
			G=D.splitlines();E=len(G);H=A.metrics.get(_L,10);I=max(18,int(H*1.9));F=E*I;A.txt_log.tag_remove(B,_c,_M);J=int(185*A.metrics.get('k',1.))
			if 0<E<=5 and F+14<C<=J:K=max(2,int((C-F)//2)-4);A.txt_log.tag_configure(B,spacing1=K);A.txt_log.tag_add(B,_c,'1.end')
		except Exception:0
	def clear_log_view(A):
		with A.engine.lock:A.engine.logs.clear()
		A.last_log_len=-1
	def do_connect(A):A._apply_srv_autofill();threading.Thread(target=run_connect_task,args=(A.engine,A.var_srv.get(),_F),daemon=_D).start()
	def do_scan(A):threading.Thread(target=run_scan_task,args=(A.engine,),daemon=_D).start()
	def do_backup(A):A._apply_srv_autofill();A.save_net_manual();A.save_cloud_path_manual();threading.Thread(target=run_backup_task,args=(A.engine,A.var_srv.get(),_F,_F,_F),daemon=_D).start()
	def reset_pins(A):
		if not A.engine.is_running:A.engine.state['session_token']=A.engine.state['login_pin']=A.engine.state['editor_pin']='';commit_state(A.engine.state);A.engine.log('Збережені PIN-коди та токен сесії очищено (Keyring / .env).',_S)
	def choose_dir(A):
		B=choose_folder_native(A.engine.state[_R])
		if B:A.engine.state[_R]=B;A.var_dir.set(B);commit_state(A.engine.state);A.engine.log(f"Папку збереження змінено на: {B}",_Q)
	def reset_dir(A):A.engine.state[_R]=os.path.normpath(DEFAULT_BACKUP_DIR);A.var_dir.set(A.engine.state[_R]);commit_state(A.engine.state);A.engine.log(f"Папку збереження встановлено: {A.engine.state[_R]}",_Q)
	def save_dir_manual(A):
		B=A.var_dir.get().strip()
		if B:A.engine.state[_R]=os.path.normpath(os.path.expanduser(B));commit_state(A.engine.state)
	def choose_mirror(A):
		if not bool(A.var_mir_en.get()):return
		D=A.engine.state.get(_A3)or A.engine.state[_R];B=choose_folder_native(D)
		if B:
			A.engine.state[_A3]=B;A.engine.state[_AC]=_D;A.var_mirror.set(B);commit_state(A.engine.state);E=getattr(A,'_was_running_ui',_F);C=bool(A.engine.is_running)
			if E and not C:A._mir_btn_sig=_B
			A._was_running_ui=C;A._update_mirror_btn();A.engine.log(f"Папку дзеркального копіювання увімкнено: {B}",_Q)
	def toggle_mirror(A):
		B=bool(A.var_mir_en.get());A.engine.state[_AC]=B;commit_state(A.engine.state);A._update_mirror_btn()
		if B:
			try:A.ent_mir.focus_set();A.ent_mir.icursor(_M)
			except Exception:0
	def save_mirror_manual(A):B=A.var_mirror.get().strip();A.engine.state[_A3]=os.path.normpath(os.path.expanduser(B))if B else'';A.engine.state[_AC]=bool(A.var_mir_en.get())and bool(A.engine.state[_A3]);commit_state(A.engine.state);A._update_mirror_btn()
	def choose_net_dir(A):
		if not bool(A.var_net_en.get()):return
		B=choose_folder_native(A.engine.state.get(_j)or A.engine.state[_R])
		if B:A.engine.state[_j]=B;A.engine.state[_l]=_D;A.var_net_dir.set(B);commit_state(A.engine.state);A._update_mirror_btn();A.engine.log(f"Папку мережі змінено на: {B}",_Q)
	def toggle_net_dir(A):
		B=bool(A.var_net_en.get());A.engine.state[_l]=B;commit_state(A.engine.state);A._update_mirror_btn()
		if B and not A.var_net_dir.get().strip():A.choose_net_dir()
	def save_net_manual(A):B=A.var_net_dir.get().strip();A.engine.state[_j]=os.path.normpath(os.path.expanduser(B))if B else'';A.engine.state[_l]=bool(A.var_net_en.get())and bool(A.engine.state[_j]);commit_state(A.engine.state);A._update_mirror_btn()
	def _force_refresh_pcloud_stats(A):
		with A.engine.lock:
			if hasattr(A.engine,_A2):A.engine._dest_stats[_g]=_B
		if hasattr(A.engine,_AB):A.engine.request_dest_stats_refresh()
	def save_cloud_path_manual(A):
		C=(A.var_cloud_path.get()or'').strip();D=str(A.engine.state.get('cloud_remote')or _g).strip()
		try:from core.cloud import validate_cloud_settings as E;B=E(D,C or _w)
		except Exception as F:A.engine.log(str(F),_S);B=A.engine.state.get(_p)or _w
		A.var_cloud_path.set(B)
		if A.engine.state.get(_p)!=B:
			A.engine.state[_p]=B;commit_state(A.engine.state)
			if hasattr(A.engine,_AB):A.engine.request_dest_stats_refresh()
		A._update_mirror_btn()
	def toggle_cloud_quick(A):
		B=bool(A.var_cld_en.get());A.engine.state[_k]=B
		if B and not(A.var_cloud_path.get()or'').strip():A.var_cloud_path.set(A.engine.state.get(_p)or _w)
		commit_state(A.engine.state);A._update_mirror_btn()
		if B:
			try:A.ent_cld.focus_set();A.ent_cld.icursor(_M)
			except Exception:0
	def _retry_pending_cloud_sync(A):
		if not WINDOWS7_CLOUD_SYNC_PREVIEW or not A.engine.state.get(_k):return
		try:
			from core.cloud import cloud_sync_queue_state as B,start_cloud_sync_worker as C
			if B(A.engine)['total']:C(A.engine)
		except Exception as D:A.engine.log(f"Не вдалося перевірити чергу хмарної синхронізації: {D}",_S)
	def _get_sys_load(G):
		a='MemAvailable';Z='/proc/meminfo';Y='/proc/stat';X='_prv_cpu';M='0';H,F=0,0
		try:
			if os.name=='nt':
				import ctypes as A
				class N(A.Structure):_fields_=[('l',A.c_ulong),('m',A.c_ulong)]+[('u',A.c_ulonglong)]*7
				J=N();J.l=A.sizeof(N)
				if A.windll.kernel32.GlobalMemoryStatusEx(A.byref(J)):F=int(J.m)
				O,P,Q=A.c_ulonglong(),A.c_ulonglong(),A.c_ulonglong()
				if A.windll.kernel32.GetSystemTimes(A.byref(O),A.byref(P),A.byref(Q)):
					B=O.value,P.value+Q.value;C=getattr(G,X,_B);G._prv_cpu=B
					if C and B[1]>C[1]:H=max(0,min(100,int(round(1e2*(1.-(B[0]-C[0])/(B[1]-C[1]))))))
			elif os.path.exists(Y)and os.path.exists(Z):
				with open(Y,'r',encoding=_A1)as K:L=[int(A)for A in K.readline().split()[1:8]]
				B=L[3]+L[4],sum(L);C=getattr(G,X,_B);G._prv_cpu=B
				if C and B[1]>C[1]:H=max(0,min(100,int(round(1e2*(1.-(B[0]-C[0])/(B[1]-C[1]))))))
				with open(Z,'r',encoding=_A1)as K:D=dict(A.split(':',1)for A in K if':'in A)
				E=int(D['MemTotal'].split()[0])
				if a in D:I=int(D[a].split()[0])
				else:I=int(D.get('MemFree',M).split()[0])+int(D.get('Buffers',M).split()[0])+int(D.get('Cached',M).split()[0])
				F=max(0,min(100,int(round(1e2*(E-I)/max(1,E)))))
			else:
				if hasattr(os,'getloadavg'):H=max(0,min(100,int(round(os.getloadavg()[0]/max(1,os.cpu_count()or 1)*100))))
				import sys as b
				if b.platform==_X:import subprocess as R,re as S;T=int(R.check_output(['sysctl','-n','hw.memsize'],timeout=.3).decode().strip());U=R.check_output(['vm_stat'],timeout=.3).decode(_A1,errors='ignore');V=S.search('page size of (\\d+) bytes',U);c=int(V.group(1))if V else 4096;d=sum(int(e.group(1))for A in('Pages free','Pages inactive','Pages speculative')if(e:=S.search(rf"{A}:\s+(\d+)",U)));F=max(0,min(100,int(round(1e2*(T-d*c)/max(1,T)))))
				elif hasattr(os,'sysconf'):
					W=os.sysconf('SC_PAGE_SIZE');E=os.sysconf('SC_PHYS_PAGES')*W;I=os.sysconf('SC_AVPHYS_PAGES')*W
					if E>0:F=max(0,min(100,int(round(1e2*(E-I)/E))))
		except Exception:0
		return H,F
	def _tick_3s_loader(A):
		try:
			if not A.root.winfo_exists():return
			B=A._get_palette();C,D=A._get_sys_load();E=B[_T]if C>=85 or D>=90 else B[_b]if C>=60 or D>=75 else B[_P];A.lbl_load_3s.configure(text=f"CPU: {C}% | RAM: {D}%",bg=B[_A],fg=E)
		except Exception:0
		A.root.after(5000,A._tick_3s_loader)
	def _poll_ui(A):
		A4='progress_style';A3='pending';A2='reason';e='pill_ok_bg';d='idle';O='id'
		try:
			if getattr(A.engine,'tray_icon',_B)is not _B:from gui.tray import drain_tray_ui_queue as A5;A5()
			if A.root.state()in(_x,_y):
				if A.engine.modal and A.engine.modal.get(O)!=A.last_modal_id:A.last_modal_id=A.engine.modal[O];A.show_window();A._show_engine_modal(A.engine.modal)
				A.root.after(450,A._poll_ui);return
			D=A.engine.state;J=(D.get(_v)or'').strip();A6=getattr(A,'_last_synced_srv',J)
			if J and J!=A6:
				A._last_synced_srv=J
				if A.root.focus_get()!=A.ent_srv:A.var_srv.set(J)
			f=time.monotonic()
			if f-getattr(A,'_last_disk_t',.0)>=5.5 or not A.engine.is_running:A._last_disk_t=f;A._cached_disk=A.engine.get_storage_stats()
			C=D.get(_U,_V);H=D.get(_r,_Z);P=bool(D.get(_a,_F));g=A.metrics[_L];h,i,Q=getattr(A,'_cached_disk',(0,.0,-1));j=h,i,Q,C
			if getattr(A,'_last_disk_sig',_B)!=j:A._last_disk_sig=j;A7=f" — Вільно: {Q} ГБ"if Q>=0 else'';A.var_disk.set(tr(f"{h} архівів ({i} МБ){A7}",C))
			if hasattr(A,_AQ):
				with A.engine.lock:A8=dict(getattr(A.engine,_A2,{})or{})
				A9={_t:bool(D.get(_l)and(D.get(_j)or'').strip()),_g:bool(D.get(_k))};B=A._get_palette()
				for K in(_t,_g):
					I,AJ,R,S=A.dest_rows[K];k=A9[K];E=A8.get(K);l=k,repr(E),C,H
					if getattr(I,'_dsig',_B)!=l:
						I._dsig=l
						if not k:
							if I.winfo_ismapped():I.pack_forget()
						else:
							if not I.winfo_ismapped():I.pack(anchor=_s,pady=1,before=A.stat_btns)
							if E is _B:S.set(tr('оновлення...',C));R.configure(fg=B[_I])
							elif not E.get(_Q):AA=tr(E.get(A2)or'недоступно',C);S.set(AA);R.configure(fg=B[_b]if E.get(A2)else B[_T])
							else:AB=f" — Вільно: {E[_AA]} ГБ"if E.get(_AA,-1)>=0 else'';AC=f" ({tr("в черзі",C)})"if E.get(A3)else'';S.set(tr(f"{E["count"]} архівів ({E["mb"]} МБ){AB}",C)+AC);R.configure(fg=B[_b]if E.get(A3)else B[_K]if K==_g else B[_P])
			if hasattr(A,'lbl_srv_badge'):
				T=getattr(A.engine,'diag_net','')or'';U=getattr(A.engine,'diag_ping','')or'';AD_L=getattr(A.engine,'diag_adapter','')or'';m=T,U,AD_L,H
				if getattr(A,'_last_srv_b_sig',_B)!=m:
					A._last_srv_b_sig=m;G=A._get_palette()
					if'ОНЛАЙН'in T:bd_p=[x for x in(AD_L,U)if x];A.var_srv_badge.set(tr(f"● {' | '.join(bd_p)}",C)if bd_p else'● Online');A.lbl_srv_badge.configure(bg=G[_A],fg=G[_K])
					elif'ОФЛАЙН'in T:A.var_srv_badge.set('● Offline');A.lbl_srv_badge.configure(bg=G[_A],fg=G[_T])
			if hasattr(A.engine,'get_last_backup_info')and hasattr(A,'t3_val'):
				n,V=A.engine.get_last_backup_info();o=n,V,C,H,P
				if getattr(A,'_last_lb_sig',_B)!=o:
					A._last_lb_sig=o;W=n.split(chr(10));A.var_last_bkp.set(tr(W[0],C));A.var_last_bkp_sub.set(tr(W[1],C)if len(W)>1 else'');B=A._get_palette();p=B[_K]if V==_Q else B[_b]if V==_S else B[_I];A.t3_val.configure(fg=p)
					if hasattr(A,'t3_sub'):A.t3_sub.configure(fg=p)
			if hasattr(A,'lbl_pill'):
				L=getattr(A.engine,'pill_type',d);M=getattr(A.engine,'pill_text','')or _A9
				if' | 'in M and L==d:M=_A9
				q=L,M,C,H,P,g
				if getattr(A,'_last_pill_sig',_B)!=q:A._last_pill_sig=q;B=A._get_palette();AD={_Q:B.get('pill_ok_fg',B[_K]),'run':B[_P],_S:B[_b],_z:B[_T]}.get(L,B[_I]);AE=B.get(e,B[_N])if L in(_Q,d)and e in B else B[_N];AF=0 if e in B else 1;A.lbl_pill.configure(text=tr(M,C),bg=AE,fg=AD,bd=AF,highlightbackground=B[_O],font=(A._base_fam,g,_C))
			if getattr(A,'_last_stage_val',_B)!=A.engine.stage:A._last_stage_val=A.engine.stage;A.var_stage.set(A.engine.stage)
			r=A.engine.indeterminate,A.engine.progress,C
			if getattr(A,'_last_pct_sig',_B)!=r:A._last_pct_sig=r;A.var_pct.set(tr('пошук...',C)if A.engine.indeterminate else f"{A.engine.progress}%")
			s=A.engine.progress,A.engine.indeterminate,A.engine.stage,D.get(A4,'v8'),bool(D.get(_a,_F))
			if getattr(A,'_last_psig',_B)!=s or A.engine.indeterminate:A._last_psig=s;A.pbar.set_state(A.engine.progress,A.engine.indeterminate,D.get(A4,'v8'),bool(D.get(_a,_F)),A._get_palette(),A.engine.stage,D.get(_U,_V))
			X=_W if A.engine.is_running else _Y;Y=_F;t=X,C,H,P
			if getattr(A,'_last_action_btn_sig',_B)!=t:
				A._last_action_btn_sig=t
				for u in(A.btn_scan,A.btn_hist,A.btn_conn,A.btn_open_dir,A.btn_start,A.btn_strat):
					if str(u.cget('state'))!=X:u.configure(state=X);Y=_D
			A._update_mirror_btn();N=getattr(A.engine,_AR,[])or[]
			if hasattr(A,'btn_scan'):
				v=len(N),H,C
				if getattr(A,'_last_lan_sig',_B)!=v:A._last_lan_sig=v;G=A._get_palette();w=tr(_A8,C);A.btn_scan.configure(text=f"{w} ({len(N)})"if N else w,fg=G[_K]if N else G[_P]);Y=_D
			if Y:fix_mac_buttons(A.root,A._get_palette())
			with A.engine.lock:F=list(A.engine.logs)
			if not F and A.last_log_len!=0:A.txt_log.configure(state=_Y);A.txt_log.delete(_c,_M);A.txt_log.configure(state=_W);A.last_log_len=0;A._last_log_item=_B
			elif F and(len(F)!=A.last_log_len or F[-1]is not A._last_log_item):
				A.txt_log.configure(state=_Y)
				if A._last_log_item is _B or A.last_log_len<=0:Z=F;A.txt_log.delete(_c,_M)
				else:
					a=-1
					for x in range(len(F)-1,-1,-1):
						if F[x]is A._last_log_item:a=x;break
					if a!=-1:Z=F[a+1:]
					else:A.txt_log.delete(_c,_M);Z=F
				for b in Z:y=b.get('level',_e);AG={_Q:(' OK ','b_ok'),_S:('WAIT','b_warn'),_z:('ERR ','b_err')};AH,AI=AG.get(y,('INFO','b_info'));A.txt_log.insert(_M,f" {AH} ",AI);A.txt_log.insert(_M,f"  {b["ts"]}   ",'dim');A.txt_log.insert(_M,f"{b["msg"]}\n",y)
				z=int(A.txt_log.index('end-1c').split('.')[0])
				if z>401:A.txt_log.delete(_c,f"{z-400}.0")
				A.txt_log.see(_M);A.txt_log.configure(state=_W);A._center_log_vertically();A.last_log_len=len(F);A._last_log_item=F[-1]
			if getattr(A.engine,'show_hw_notice',_F)and not A.hw_notice_shown:
				A.hw_notice_shown=_D;A.engine.show_hw_notice=_F;c=A.engine.state.get('hw_auto_notice','')
				if c:A.engine.log(c.replace('\n\n',' ').replace('\n',' '),_e);A._show_engine_modal({'type':'alert','title':'Автоматичне налаштування теми',_H:c})
			if A.engine.modal and A.engine.modal.get(O)!=A.last_modal_id:
				A.last_modal_id=A.engine.modal[O]
				if A.root.state()in(_x,_y):A.show_window()
				A._show_engine_modal(A.engine.modal)
		except Exception:0
		A0=bool(A.engine.state.get(_a,_F))
		if A.engine.is_running:A1=650 if A0 else 450
		else:A1=1200 if A0 else 800
		A.root.after(A1,A._poll_ui)
