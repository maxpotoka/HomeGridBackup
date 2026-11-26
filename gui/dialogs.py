# patch-id: backup-report-3stage-hbar-3.82
# [\u0424\u0410\u0419\u041b: gui/dialogs.py (v2.45 | 26.11.2026 17:58)
# patch-id: direct-cloud-write-setting-3.76
# [\u0424\u0410\u0419\u041b: gui/dialogs.py (v2.44 | 26.11.2026 14:20)
# patch-id: d1-upload-refresh-true-3.63
# [\u0424\u0410\u0419\u041b: gui/dialogs.py (v2.43 | 26.11.2026 11:26)
# patch-id: d1-manual-upload-btn-3.62
# [\u0424\u0410\u0419\u041b: gui/dialogs.py (v2.42 | 26.11.2026 11:24)
# patch-id: d1-cache-toggle-setting-3.58
# patch-id: stats-full-parent-width-3.55
# [\u0424\u0410\u0419\u041b: gui/dialogs.py (v2.41 | 26.11.2026 10:36)
# patch-id: ubuntu-embedded-dlg-fix-3.57
# [ФАЙЛ: gui/dialogs.py (v2.39 | 25.11.2026 15:45)
_AU='<Double-1>'
_AT='sha_checked_mtime'
_AS='sha_detail'
_AR='<<ComboboxSelected>>'
_AQ='<MouseWheel>'
_AP='<Destroy>'
_AO='<Button-1>'
_AN='alert'
_AM='sha_status'
_AL='128 КБ'
_AK='delete_mode'
_AJ='<Escape>'
_AI='Ubuntu'
_AH='detail'
_AG='op_history'
_AF='device_id'
_AE='warn'
_AD='title'
_AC='MB/s'
_AB='МБ/с'
_AA='file'
_A9='Consolas'
_A8='lite_mode'
_A7='<Return>'
_A6='Скасувати'
_A5='WM_DELETE_WINDOW'
_A4='.sha256'
_A3='server'
_A2='normal'
_A1='trash'
_A0='all'
_z='vertical'
_y='blue'
_x='ts'
_w='Закрити'
_v='green_txt'
_u='sh'
_t='sw'
_s=' ('
_r='size'
_q='status'
_p='backup_dir'
_o='y'
_n='linux'
_m='sha'
_l='#ffffff'
_k='font_sz'
_j='type'
_h='err'
_i='e'
_g='center'
_f='log_bg'
_e='readonly'
_d='<Configure>'
_c='inp_bg'
_b='amber'
_a='k'
_Z='bottom'
_Y='solid'
_X='—'
_W='both'
_V='red'
_U='green'
_T=.0
_S=False
_R='hand2'
_Q='cyan'
_P='border'
_O='muted'
_N='Segoe UI'
_M=None
_L='w'
_K='right'
_J='left'
_I='bold'
_H=True
_G='panel'
_F='lang'
_E='en'
_D='text'
_C='x'
_B='uk'
_A='card'
from gui.widgets import*
import os,re,time,tkinter as tk
from tkinter import ttk
from core.backup import verify_all_archives
from core.config import SCRIPT_VER,commit_state
from core.files import format_duration
from core.gfs import apply_gfs_cleanup,compute_gfs_plan,toggle_keep_tag
from core.i18n import apply_widget_i18n,tr
from core.scheduler import _build_run_cmd,_manage_windows_scheduler,_sync_scheduler_from_windows
from gui.styles import UI_FONT_LABELS,UI_SCALE_LABELS,fix_mac_buttons
_OP_ARCHIVE_RE=re.compile('^homegrid_backup_(DAILY|WEEKLY|MONTHLY|YEARLY|KEEP)_(.+)$',re.IGNORECASE)
def _operation_archive_name(detail):
	value=str(detail or'').strip()
	if _s in value and value.endswith(')')and not value.lower().endswith('.zip'):value=value.rsplit(_s,1)[0].strip()
	name=os.path.basename(value);return name if name.lower().endswith('.zip')else''
def _operation_archive_display(name):
	match=_OP_ARCHIVE_RE.match(name)
	if not match:return'',name
	return match.group(1).upper(),match.group(2)
def _operation_interval_text(item):
	A='%H:%M:%S';from datetime import datetime,timedelta
	try:start=datetime.fromisoformat(str(item.get('started_at','')));end=datetime.fromisoformat(str(item.get('finished_at','')));approximate=_S
	except(TypeError,ValueError):
		try:duration=float(item.get('dur_sec'));end=datetime.strptime(str(item.get(_x,'')),'%d.%m.%Y %H:%M')
		except(TypeError,ValueError):return _M,_S
		start=end-timedelta(seconds=duration);approximate=_H
	return'{} → {}'.format(start.strftime(A),end.strftime(A)),approximate
class _EmbeddedDialog(tk.Frame):
	def __init__(self,root,palette,title_txt,w,h,on_close_cb):self._root=root;self._on_close_cb=on_close_cb;self._del_protocol=_M;super().__init__(root,bg=palette[_G],bd=2,relief=_Y,highlightbackground=palette[_y],highlightthickness=2);hdr=tk.Frame(self,bg=palette[_A],padx=10,pady=6);hdr.pack(side='top',fill=_C);import sys as _s;_fam=_AI if _s.platform.startswith(_n)else _N;self._lbl_t=tk.Label(hdr,text=title_txt,bg=palette[_A],fg=palette[_D],font=(_fam,10,_I));self._lbl_t.pack(side=_J);tk.Button(hdr,text='✖',command=self._handle_wm_delete,bg=palette[_A],fg=palette[_V],bd=0,padx=6,cursor=_R).pack(side=_K);self.place(relx=.5,rely=.5,anchor=_g,width=w,height=h);self.lift()
	def _handle_wm_delete(self):
		if callable(self._del_protocol):self._del_protocol()
		else:self.destroy()
	def title(self,txt=_M):
		if txt is not _M:self._lbl_t.configure(text=txt)
		return self._lbl_t.cget(_D)
	def protocol(self,name,func=_M):
		if name==_A5:self._del_protocol=func
	def transient(self,*_a):0
	def grab_set(self):0
	def deiconify(self):0
	def withdraw(self):0
	def geometry(self,*_a):0
	def maxsize(self,*_a):return 1920,1080
	def minsize(self,*_a):0
	def resizable(self,*_a):0
	def attributes(self,*_a):0
	def destroy(self):
		if callable(self._on_close_cb):self._on_close_cb()
		super().destroy()
def _render_report_3stage_bar(dlg, p, d, fam, fs, lang, k_sc):
    t_srv = sum(float(d.get(k) or 0) for k in ('srv_db_sec', 'srv_copy_sec', 'srv_chk_sec', 'srv_hist_sec', 'srv_proc_sec', 'srv_pack_sec', 'srv_sec', 'srv_prep_sec'))
    t_net = float(d.get('dl_sec') or 0)
    t_loc = sum(float(d.get(k) or 0) for k in ('crc_sec', 'ver_sec', 'sha_sec', 'mir_sec', 'net_sec'))
    t_all = max(0.1, t_srv + t_net + t_loc)
    box = tk.Frame(dlg, bg=p['card'], bd=1, relief='solid', padx=14, pady=8)
    box.pack(fill='x', padx=16, pady=(0, 8))
    cv = tk.Canvas(box, height=max(24, int(26 * k_sc)), bg=p['log_bg'], highlightthickness=1, highlightbackground=p['border'])
    cv.pack(fill='x')
    leg = tk.Frame(box, bg=p['card'])
    leg.pack(fill='x', pady=(5, 0))
    items = [
        ('\u0421\u0435\u0440\u0432\u0435\u0440' if lang == 'uk' else 'Server', t_srv, '#818cf8'),
        ('\u041c\u0435\u0440\u0435\u0436\u0430' if lang == 'uk' else 'Network', t_net, '#38bdf8'),
        ('\u041f\u0435\u0440\u0435\u0432\u0456\u0440\u043a\u0430/\u0434\u0438\u0441\u043a' if lang == 'uk' else 'Verify/Disk', t_loc, '#22c55e'),
    ]
    for name, val, col in items:
        pct = int(round(val / t_all * 100))
        dur_s = format_duration(val, lang).partition(' (').__getitem__(0)
        tk.Label(leg, text='\u25a0', bg=p['card'], fg=col, font=(fam, fs, 'bold')).pack(side='left', padx=(0, 3))
        tk.Label(leg, text=f"{name}: {dur_s} ({pct}%)", bg=p['card'], fg=p['text'], font=(fam, max(8, fs - 1))).pack(side='left', padx=(0, 14))
    def _draw(_e=None):
        if not cv.winfo_exists():
            return
        cv.delete('all')
        w_g = max(200, cv.winfo_width())
        h_g = max(20, cv.winfo_height())
        act = [(n, v, c) for (n, v, c) in items if v > 0]
        if not act:
            return
        raw_w = [max(6.0, w_g * (v / t_all)) for (_, v, _) in act]
        sc_w = w_g / max(1.0, sum(raw_w))
        cx = 0.0
        for idx, ((n, v, c), rw) in enumerate(zip(act, raw_w)):
            sw = (w_g - cx) if idx == len(act) - 1 else (rw * sc_w)
            x2 = cx + sw
            cv.create_rectangle(cx, 0, x2, h_g, fill=c, outline=p['card'], width=1)
            pct = int(round(v / t_all * 100))
            if sw >= 54:
                cv.create_text((cx + x2) / 2, h_g / 2, text=f"{pct}%", fill='#0f172a', font=(fam, max(8, fs - 1), 'bold'))
            cx = x2
    cv.bind('<Configure>', _draw)
    dlg.after(30, _draw)

class DialogsMixin:
	def _ui_fam(self):
		if hasattr(self,'_base_fam')and self._base_fam:return self._base_fam
		import sys as _sf;return'Helvetica Neue'if _sf.platform=='darwin'else _AI if _sf.platform.startswith(_n)else _N
	def _calc_parent_center(self,parent_win,w_box,h_box):
		m=self.metrics
		try:
			pw,ph=parent_win.winfo_width(),parent_win.winfo_height()
			if pw>120 and ph>120:cx=parent_win.winfo_rootx()+(pw-w_box)//2;cy=parent_win.winfo_rooty()+(ph-h_box)//2;x=max(6,min(cx,m[_t]-w_box-6));y=max(6,min(cy,m[_u]-h_box-30));return x,y
		except Exception:0
		return m['wa_x']+max(0,(m[_t]-w_box)//2),m['wa_y']+max(0,(m[_u]-h_box)//2)
	def _finalize_dialog(self,dlg):
		import sys
		try:
			if not dlg.winfo_exists():return
			dlg.update_idletasks();m=self.metrics;req_w,req_h=dlg.winfo_reqwidth(),dlg.winfo_reqheight();cur_w,cur_h=getattr(dlg,'_init_wh',(req_w,req_h))
			if getattr(dlg,'_fit_flag',_S):w_box=min(max(cur_w,req_w),max(360,m[_t]-20));h_box=min(max(cur_h,req_h),max(180,m[_u]-60));mx_w,mx_h=dlg.maxsize();dlg.maxsize(max(w_box,mx_w),max(h_box,mx_h));dlg.minsize(min(w_box,req_w),min(h_box,req_h))
			else:w_box,h_box=max(360,cur_w,req_w),max(160,cur_h,req_h)
			p_ref=getattr(dlg,'_parent_ref',self.root);x,y=self._calc_parent_center(p_ref,w_box,h_box)
			if not sys.platform.startswith(_n):dlg.geometry(f"{w_box}x{h_box}+{x}+{y}");dlg.transient(p_ref);dlg.deiconify();dlg.grab_set()
			else:rw=max(420,self.root.winfo_width()-24);rh=max(220,self.root.winfo_height()-24);dlg.place_configure(width=min(max(w_box,req_w+16),rw),height=min(max(h_box,req_h+16),rh));dlg.update_idletasks();dlg.lift()
			fix_mac_buttons(dlg,self._get_palette())
			if not sys.platform.startswith(_n):dlg.focus_force()
		except Exception:0
	def _make_dialog(self,title,w=640,h=420,scrollable=_S,min_outer_w=0,min_outer_h=0):
		D='win_h';C='outer_h';B='win_w';A='outer_w';import sys
		if not hasattr(self,'_open_dialogs'):self._open_dialogs={}
		dlg_key=str(title).split(_X)[0].strip();prev_dlg=self._open_dialogs.get(dlg_key)
		if prev_dlg is not _M:
			try:
				if prev_dlg.winfo_exists():prev_dlg.destroy()
			except Exception:0
		p=self._get_palette();m=self.metrics;k=m[_a];fw=m.get(A,m[B])-m[B];fh=m.get(C,m[D])-m[D];dlg_w=max(360,min(m.get(A,m[_t]),max(min_outer_w,int(round(w*k))))-fw);dlg_h=max(160,min(m.get(C,m[_u]),max(min_outer_h,int(round(h*k))))-fh);self._ignore_resize_until=time.time()+.7;parent_win=self.root if sys.platform.startswith(_n)else self.root.grab_current()or self.root;px,py=self._calc_parent_center(parent_win,dlg_w,dlg_h)
		if sys.platform.startswith(_n):
			for(_k_old,_d_old)in list(self._open_dialogs.items()):
				try:
					if _d_old.winfo_exists():_d_old.destroy()
				except Exception:0
			self._open_dialogs.clear();rw=max(560,self.root.winfo_width()-24);rh=max(380,self.root.winfo_height()-24);ew,eh=min(dlg_w,rw),min(dlg_h,rh);dlg=_EmbeddedDialog(self.root,p,tr(title,self.engine.state.get(_F,_E)),ew,eh,lambda:self._open_dialogs.pop(dlg_key,_M));self._open_dialogs[dlg_key]=dlg
			if not scrollable:return dlg,p,dlg
			wrap=tk.Frame(dlg,bg=p[_G]);wrap.pack(fill=_W,expand=_H);canvas=tk.Canvas(wrap,bg=p[_G],highlightthickness=0,bd=0);vbar=tk.Scrollbar(wrap,orient=_z,command=canvas.yview);inner=tk.Frame(canvas,bg=p[_G]);inner.bind(_d,lambda e:canvas.configure(scrollregion=canvas.bbox(_A0)));win_id=canvas.create_window((0,0),window=inner,anchor='nw');canvas.bind(_d,lambda e:canvas.itemconfigure(win_id,width=e.width));canvas.configure(yscrollcommand=vbar.set);vbar.pack(side=_K,fill=_o);canvas.pack(side=_J,fill=_W,expand=_H);return dlg,p,inner
		self.root.option_add('*Toplevel.background',p[_G]);dlg=tk.Toplevel(self.root,bg=p[_G])
		if not sys.platform.startswith(_n):dlg.withdraw()
		self._open_dialogs[dlg_key]=dlg
		def _on_dlg_destroy(e):
			if e.widget is dlg:
				self._open_dialogs.pop(dlg_key,_M);self._ignore_resize_until=time.time()+.7
				try:self.root.focus_set()
				except Exception:0
		dlg.bind(_AP,_on_dlg_destroy);dlg.title(tr(title,self.engine.state.get(_F,_E)));dlg.configure(bg=p[_G]);dlg._parent_ref=parent_win;dlg._init_wh=dlg_w,dlg_h;dlg._fit_flag=_S;dlg.geometry(f"{dlg_w}x{dlg_h}+{px}+{py}");dlg.maxsize(min(m[_t],int(round(max(w,760)*k*1.15))),min(m[_u],int(round(max(h,520)*k*1.15))));dlg.after_idle(lambda:self._finalize_dialog(dlg))
		if not scrollable:return dlg,p,dlg
		wrap=tk.Frame(dlg,bg=p[_G]);wrap.pack(fill=_W,expand=_H);canvas=tk.Canvas(wrap,bg=p[_G],highlightthickness=0,bd=0);vbar=tk.Scrollbar(wrap,orient=_z,command=canvas.yview);inner=tk.Frame(canvas,bg=p[_G]);inner.bind(_d,lambda e:canvas.configure(scrollregion=canvas.bbox(_A0)));win_id=canvas.create_window((0,0),window=inner,anchor='nw');canvas.bind(_d,lambda e:canvas.itemconfigure(win_id,width=e.width));canvas.configure(yscrollcommand=vbar.set);vbar.pack(side=_K,fill=_o);canvas.pack(side=_J,fill=_W,expand=_H);dlg.bind(_AQ,lambda ev:canvas.yview_scroll(int(-1*(ev.delta/120)),'units'));return dlg,p,inner
	def _fit_dialog(self,dlg):dlg._fit_flag=_H
	def confirm_exit(self):
		import sys;fs=max(10,self.metrics[_k]);fam=_AI if sys.platform.startswith(_n)else _N;lang=self.engine.state.get(_F,_E);dlg,p,_=self._make_dialog(tr('Підтвердження виходу',lang),520,225);bf=tk.Frame(dlg,bg=p[_G]);bf.pack(side=_Z,fill=_C,padx=16,pady=(6,14));tk.Label(dlg,text=tr('Ви дійсно бажаєте завершити роботу HomeGrid Backup та закрити програму?',lang),bg=p[_G],fg=p[_D],wraplength=int(460*self.metrics[_a]),font=(fam,fs)).pack(pady=(18,10),padx=18,expand=_H);tk.Button(bf,text=tr(_A6,lang),command=dlg.destroy,bg=p[_A],fg=p[_D],font=(fam,fs),padx=16,pady=6,cursor=_R).pack(side=_K,padx=6)
		def _do_exit(_e=_M):
			self._exit_confirm_open=_S
			try:dlg.destroy()
			except Exception:0
			from gui.tray import _force_quit_app;_force_quit_app(self.engine)
		def _cancel_exit(_e=_M):
			self._exit_confirm_open=_S
			try:dlg.destroy()
			except Exception:0
		dlg.protocol(_A5,_cancel_exit);dlg.bind(_AJ,_cancel_exit);dlg.bind(_A7,_do_exit);tk.Button(bf,text=tr('Так, вийти',lang),command=_do_exit,bg=p[_V],fg=_l,font=(fam,fs,_I),padx=16,pady=6,cursor=_R).pack(side=_K,padx=6);apply_widget_i18n(dlg,self.engine.state.get(_F,_E));self._fit_dialog(dlg)
	def _show_engine_modal(self,m):
		try:
			self._show_engine_modal_impl(m)
		except Exception as _mex:
			import traceback;self.engine.log(f'Modal error: {_mex}',_h);print(traceback.format_exc())
	def _show_engine_modal_impl(self,m):
		G='url';F='action';E='pin';D='old_cnt';C='free_gb';B='z_mb';A='z_cnt';import json as _js;fs=self.metrics[_k];lang=self.engine.state.get(_F,_E)
		if m[_j]=='backup_report':
			d=_js.loads(m[_D])if isinstance(m.get(_D),str)else{};fam=_A9 if self.engine.state.get(_A8,_S)else self._get_palette().get('font',_N);dlg,p,_=self._make_dialog('Резервне копіювання успішно завершено'if lang==_B else'Backup Completed Successfully',800,690,min_outer_w=750,min_outer_h=640)
			def _close_rep(_e=_M):
				try:dlg.destroy()
				except Exception:0
				self.engine.submit_modal(_H)
			dlg.protocol(_A5,_close_rep);tot_s=max(.1,float(d.get('total_sec',.1)));tot_disp=format_duration(tot_s,lang).partition(_s).__getitem__(0);fn_s=d.get(_AA,'backup.zip');sz_s=d.get('size_mb',_T);fc_s=d.get('files_cnt',0);ts_a=d.get('ts_start',_X);ts_b=d.get('ts_end',_X);spd_s=d.get('spd_mbs',_T);srv_spd_s=float(d.get('srv_spd_mbs')or 0);top_c=tk.Frame(dlg,bg=p[_A],bd=1,relief=_Y,padx=14,pady=10);top_c.pack(fill=_C,padx=16,pady=(12,8));import ipaddress as _ipa;from urllib.parse import urlparse as _up;srv_raw=str(d.get('srv')or self.engine.state.get(_A3,'')).strip();_h=_up(srv_raw).hostname or srv_raw if srv_raw else''
			try:_is_lan=_ipa.ip_address(_h).is_private or _ipa.ip_address(_h).is_loopback
			except Exception:_is_lan=_h.endswith('.local')or _h in('localhost',)
			net_tag=('Локальна мережа / LAN'if _is_lan else'Інтернет / Зовнішній')if lang==_B else'Local Network / LAN'if _is_lan else'Internet / External';srv_disp=f"{srv_raw}  [{net_tag}]"if srv_raw else _X;tk.Label(top_c,text=f"Файл архіву:  {fn_s}"if lang==_B else f"Archive file:  {fn_s}",bg=p[_A],fg=p[_Q],font=(fam,fs+2,_I),anchor=_g,justify=_g).pack(anchor=_g,pady=(0,6));tk.Label(top_c,text=f"Джерело (сервер):  {srv_disp}"if lang==_B else f"Source server:  {srv_disp}",bg=p[_A],fg=p[_U]if _is_lan else p[_b],font=(fam,fs+2,_I),anchor=_g,justify=_g).pack(anchor=_g,pady=(0,6));_fc_part=(f" ({fc_s} файлів)"if lang==_B else f" ({fc_s} files)")if int(fc_s or 0)>0 else'';tk.Label(top_c,text=f"Розмір:  {sz_s} МБ{_fc_part}   •   CRC32 + SHA-256: Підтверджено"if lang==_B else f"Size:  {sz_s} MB{_fc_part}   •   CRC32 + SHA-256: Verified",bg=p[_A],fg=p[_D],font=(fam,fs+2),anchor=_g,justify=_g).pack(anchor=_g,pady=(0,6));tk.Label(top_c,text=f"Час запуску:  {ts_a}   →   Завершено:  {ts_b}   (Разом: {tot_disp})"if lang==_B else f"Started at:  {ts_a}   →   Finished:  {ts_b}   (Total: {tot_disp})",bg=p[_A],fg=p[_U],font=(fam,fs+2,_I),anchor=_g,justify=_g).pack(anchor=_g);_render_report_3stage_bar(dlg,p,d,fam,fs,lang,self.metrics[_a]);mid_c=tk.Frame(dlg,bg=p[_A],bd=1,relief=_Y,padx=14,pady=10);mid_c.pack(fill=_C,padx=16,pady=(0,8));mid_c.columnconfigure(0,weight=1);raw_stages=([('Підключення до бази даних:'if lang==_B else'Server database connection:',d.get('srv_db_sec',_T),p[_Q])]if float(d.get('srv_db_sec',0)or 0)>0 else[])+[('Збір та копіювання даних на сервері:'if lang==_B else'Server data collection & copy:',d.get('srv_copy_sec',_T),p[_D]),('Перевірка файлів на сервері:'if lang==_B else'Server file verification:',d.get('srv_chk_sec',_T),p[_D])]+([('Копіювання історії розумних пристроїв:'if lang==_B else'Smart devices history copy:',d.get('srv_hist_sec',_T),p[_Q])]if float(d.get('srv_hist_sec',0)or 0)>0 else[])+[('Обробка на сервері:'if lang==_B else'Processing on server:',d.get('srv_proc_sec',_T),p[_D]),(f'Стиснення та пакування TAR.ZST на сервері ({srv_spd_s} {_AB}):'if lang==_B and srv_spd_s>0 else f'Server TAR.ZST packing ({srv_spd_s} {_AC}):'if srv_spd_s>0 else'Стиснення та пакування TAR.ZST на сервері:'if lang==_B else'Server TAR.ZST archive packing:',d.get('srv_pack_sec',d.get('srv_sec',_T)),p[_D]),('Підготовка та аналіз на сервері:'if lang==_B else'Server preparation & scan:',d.get('srv_prep_sec',_T),p[_D]),(f"Скачування по мережі ({spd_s} {_AB if lang==_B else _AC}):"if lang==_B else f"Network download ({spd_s} MB/s):",d.get('dl_sec',_T),p[_Q]),('Перевірка архіву CRC32 (програма):'if lang==_B else'Local CRC32 integrity check:',d.get('crc_sec',d.get('ver_sec',_T)),p[_D]),('Розрахунок та звірка SHA-256:'if lang==_B else'Local SHA-256 hash verification:',d.get('sha_sec',_T),p[_D])]
			if d.get('mir_active'):raw_stages.append(('Дзеркальне копіювання:'if lang==_B else'Mirror folder copy:',d.get('mir_sec',_T),p[_U]))
			if d.get('net_active'):raw_stages.append(('Копіювання у мережеву папку:'if lang==_B else'Network folder copy:',d.get('net_sec',_T),p[_Q]))
			raw_stages=[(t,v,c)for(t,v,c)in raw_stages if float(v or 0)>0];stages=[(f"{i}. {t}",v,c)for(i,(t,v,c))in enumerate(raw_stages,1)]
			for(idx_r,(lbl_st,val_s,col_st))in enumerate(stages):pct_v=min(100,int(round(float(val_s)/tot_s*100)));_pct_s=f"  ({pct_v}%)"if pct_v>0 else'';is_spd_row=('/с' in lbl_st or 'MB/s' in lbl_st);tk.Label(mid_c,text=lbl_st,bg=p[_A],fg=p[_U]if('Скачування'in lbl_st or 'Network download'in lbl_st)else col_st,font=(fam,fs+2,_I)if is_spd_row else(fam,fs+2),anchor=_L).grid(row=idx_r,column=0,sticky=_L,pady=4);tk.Label(mid_c,text=f"{format_duration(val_s,lang).partition(_s).__getitem__(0)}{_pct_s}",bg=p[_A],fg=col_st,font=(fam,fs+2,_I),anchor=_i).grid(row=idx_r,column=1,sticky=_i,padx=(12,0),pady=4)
			bf=tk.Frame(dlg,bg=p[_G]);bf.pack(side=_Z,fill=_C,padx=16,pady=(4,10));bot_c=tk.Frame(dlg,bg=p[_A],bd=1,relief=_Y,padx=14,pady=8);bot_c.pack(side=_Z,fill=_C,padx=16,pady=(0,6));tk.Label(bot_c,text=f"Сховище:  {d.get(A,0)} архівів ({d.get(B,0)} МБ)   •   Вільно:  {d.get(C,0)} ГБ   •   Застарілих GFS:  {d.get(D,0)} шт."if lang==_B else f"Storage:  {d.get(A,0)} archives ({d.get(B,0)} MB)   •   Free:  {d.get(C,0)} GB   •   Outdated GFS:  {d.get(D,0)}",bg=p[_A],fg=p[_O],font=(fam,fs+2),anchor=_L).pack(fill=_C);btn_ok_r=tk.Button(bf,text='ОК'if lang==_B else'OK',command=_close_rep,bg=p[_U],fg=p[_v],font=(fam,fs+2,_I),padx=24,pady=5,cursor=_R);btn_ok_r.pack(side=_K);dlg.after(350,lambda:(dlg.bind(_A7,_close_rep),dlg.bind(_AJ,_close_rep),btn_ok_r.focus_set())if dlg.winfo_exists()else _M);self._fit_dialog(dlg);return
		is_lan_dlg=m[_j]=='lan_found';dlg,p,_=self._make_dialog(m[_AD],660 if is_lan_dlg else 590,340 if is_lan_dlg else 235)
		def _done(val):
			try:dlg.destroy()
			except Exception:0
			self.engine.submit_modal(val)
		dlg.protocol(_A5,lambda:_done(''if m[_j]==E else _S))
		if is_lan_dlg:
			items=m.get('default')or[];hdr_t='Оберіть дію для виявленого сервера в локальній мережі:'if lang==_B else'Choose an action for the discovered LAN server:';tk.Label(dlg,text=hdr_t,bg=p[_G],fg=p[_O],font=(_N,fs)).pack(anchor=_L,padx=16,pady=(14,8));box=tk.Frame(dlg,bg=p[_G]);box.pack(fill=_W,expand=_H,padx=16,pady=(0,6))
			for(url,t_ms,a_ms)in items:row=tk.Frame(box,bg=p[_A],bd=1,relief=_Y,padx=10,pady=8);row.pack(fill=_C,pady=4);info_f=tk.Frame(row,bg=p[_A]);info_f.pack(side=_J,fill=_C,expand=_H);tk.Label(info_f,text=url,bg=p[_A],fg=p[_Q],font=(_N,fs+1,_I)).pack(anchor=_L);ms_unit='мс'if lang==_B else'ms';tk.Label(info_f,text=f"TCP: {t_ms} {ms_unit}  •  API: {a_ms} {ms_unit}",bg=p[_A],fg=p[_O],font=(_N,max(8,fs-1))).pack(anchor=_L);btn_bkp_t='🔌 Підключити та бекап'if lang==_B else'🔌 Connect & Backup';btn_sav_t='⭐ В Історію'if lang==_B else'⭐ Save to History';tk.Button(row,text=btn_bkp_t,command=lambda u=url:_done({F:'backup',G:u}),bg=p[_U],fg=p[_v],font=(_N,fs,_I),padx=10,pady=4,cursor=_R).pack(side=_K,padx=(6,0));tk.Button(row,text=btn_sav_t,command=lambda u=url:_done({F:'save',G:u}),bg=p[_y],fg=_l,font=(_N,fs,_I),padx=10,pady=4,cursor=_R).pack(side=_K,padx=6)
			bf=tk.Frame(dlg,bg=p[_G]);bf.pack(side=_Z,fill=_C,padx=16,pady=12);tk.Button(bf,text=_w if lang==_B else'Close',command=lambda:_done(_S),bg=p[_A],fg=p[_D],font=(_N,fs),padx=14,pady=5).pack(side=_K);self._fit_dialog(dlg);return
		is_list='• 'in m[_D]
		if is_list:
			lines=[ln.strip()for ln in m[_D].splitlines()if ln.strip()];tk.Label(dlg,text=lines[0],bg=p[_G],fg=p[_D],anchor=_L,justify=_J,font=(_N,fs,_I)).pack(pady=(14,6),padx=18,fill=_C);list_box=tk.Frame(dlg,bg=p[_A],bd=1,relief=_Y,padx=10,pady=8);list_box.pack(padx=18,pady=(0,8),fill=_C)
			for ln in lines[1:]:clean_ln=ln.lstrip('• ').strip();prefix='•  'if ln.startswith('•')else'';tk.Label(list_box,text=f"{prefix}{clean_ln}",bg=p[_A],fg=p[_b]if prefix else p[_O],anchor=_L,justify=_J,font=(_A9,max(9,fs-1))).pack(anchor=_L,pady=1)
		else:tk.Label(dlg,text=m[_D],bg=p[_G],fg=p[_D],justify=_g,anchor=_g,wraplength=int(480*self.metrics[_a]),font=(_N,fs)).pack(pady=(16,10),padx=18,fill=_C)
		bf=tk.Frame(dlg,bg=p[_G]);bf.pack(side=_Z,fill=_C,padx=16,pady=12)
		if m[_j]==E:v_pin=tk.StringVar();ent=tk.Entry(dlg,textvariable=v_pin,show='•',bg=p[_c],fg=p[_D],insertbackground=p[_D],font=(_N,fs+2),justify=_g);ent.pack(padx=40,fill=_C,ipady=4);ent.focus_set();ent.bind(_A7,lambda e:_done(v_pin.get().strip()));tk.Button(bf,text=_A6,command=lambda:_done(''),bg=p[_A],fg=p[_D],font=(_N,fs),padx=14,pady=5).pack(side=_K,padx=8);tk.Button(bf,text='Підтвердити',command=lambda:_done(v_pin.get().strip()),bg=p[_U],fg=p[_v],font=(_N,fs,_I),padx=14,pady=5).pack(side=_K,padx=8)
		elif m[_j]=='confirm':tk.Button(bf,text='Ні',command=lambda:_done(_S),bg=p[_A],fg=p[_D],font=(_N,fs),padx=16,pady=5).pack(side=_K,padx=8);tk.Button(bf,text='Так',command=lambda:_done(_H),bg=p[_b],fg=_l,font=(_N,fs,_I),padx=16,pady=5).pack(side=_K,padx=8)
		else:tk.Button(bf,text='ОК',command=lambda:_done(_H),bg=p[_U],fg=p[_v],font=(_N,fs,_I),padx=18,pady=5).pack(side=_K,padx=8)
		self._fit_dialog(dlg)
	def open_history_modal(self):
		D='server_history';C='_render_fav_servers';B='favorite_servers';A='/';fs=self.metrics[_k];dlg,p,_=self._make_dialog('Історія адрес серверів',560,380);tk.Label(dlg,text='Оберіть раніше збережену адресу або видаліть зайву:',bg=p[_G],fg=p[_O],font=(_N,fs)).pack(anchor=_L,padx=14,pady=(10,6));box=tk.Frame(dlg,bg=p[_G]);box.pack(fill=_W,expand=_H,padx=14)
		def _pick(url):
			self.var_srv.set(url);self.engine.state[_A3]=url;self._last_synced_srv=url;commit_state(self.engine.state)
			if hasattr(self,C):self._render_fav_servers()
			dlg.destroy()
		def _toggle_fav(url):
			norm_u=(url or'').strip().rstrip(A);favs=[x.strip().rstrip(A)for x in self.engine.state.get(B)or[]if x.strip()];favs=[x for x in favs if x!=norm_u]if norm_u in favs else favs+[norm_u];self.engine.state[B]=favs[:8];commit_state(self.engine.state)
			if hasattr(self,C):self._render_fav_servers()
			_render()
		def _render():
			for ch in box.winfo_children():ch.destroy()
			hist=self.engine.state.get(D)or[];favs={x.strip().rstrip(A)for x in self.engine.state.get(B)or[]}
			if not hist:tk.Label(box,text='Історія адрес порожня.',bg=p[_G],fg=p[_O],font=(_N,fs)).pack(pady=20);return
			for(i,u)in enumerate(hist):is_f=u.strip().rstrip(A)in favs;row=tk.Frame(box,bg=p[_A],padx=8,pady=5,bd=1,relief=_Y);row.pack(fill=_C,pady=3);tk.Button(row,text='★'if is_f else'☆',bg=p[_A],fg=p[_b]if is_f else p[_O],bd=0,font=(_N,fs+1,_I),padx=6,cursor=_R,command=lambda url=u:_toggle_fav(url)).pack(side=_J,padx=(0,4));tk.Label(row,text=f"#{i+1}  {u}",bg=p[_A],fg=p[_Q],font=(_N,fs,_I)).pack(side=_J);tk.Button(row,text='✖',bg=p[_A],fg=p[_V],font=(_N,fs),padx=8,command=lambda url=u:_del(url)).pack(side=_K,padx=4);tk.Button(row,text='Обрати',bg=p[_y],fg=_l,font=(_N,fs),padx=10,command=lambda url=u:_pick(url)).pack(side=_K,padx=6)
		def _del(url):
			norm_u=(url or'').strip().rstrip(A);self.engine.state[D]=[x for x in self.engine.state.get(D)or[]if x.strip().rstrip(A)!=norm_u];self.engine.state[B]=[x for x in self.engine.state.get(B)or[]if x.strip().rstrip(A)!=norm_u]
			if(self.engine.state.get(_A3)or'').strip().rstrip(A)==norm_u:self.engine.state[_A3]='';self.var_srv.set('');self._last_synced_srv=''
			commit_state(self.engine.state)
			if hasattr(self,C):self._render_fav_servers()
			_render()
		_render();tk.Button(dlg,text=_w,command=dlg.destroy,bg=p[_A],fg=p[_D],font=(_N,fs),padx=14,pady=5).pack(side=_Z,anchor=_i,padx=14,pady=12);apply_widget_i18n(dlg,self.engine.state.get(_F,_E))
	def open_settings(self,initial_tab=0):
		A5='Світла тема';A4='Українська';A3='storage_backend';A2='editor_pin';A1='login_pin';A0='session_token';z='client_token';y='*.json';x='JSON';w='--silent';v='network';u='Авто (pCloud → Мережа при наявності)';t='Трей та безпека';s='Інтерфейс';r='Розклад та запуск';q='Зберігання та GFS';o='shield';n='sched_time';m='journal_sync_target';l='cloud_fit_free_space';k='cloud_max_size_gb';j='cloud_max_archives';i='HomeGridBackup';h='cloud_path';g='cloud_save_logs';f='cloud_save_archives';e='pCloud';d='cloud_enabled';c='progress_style';b='download_buf_kb';a='net_fit_free_space';Z='net_max_size_gb';Y='net_max_archives';X='tray_backend';W='minimize_to_tray';V='ui_font';U='theme';T='silent_cleanup';S='yearly_count';R='monthly_count';Q='weekly_count';P='today_max';O='daily_days';N='keep_last_count';M='Темна тема';L='English (Default)';K='sched_wake';J='sched_missed';I='sched_prio';H='--hidden';G='sched_mode';F='ui_scale';E='logs_dir';D='dark';C='idx';B='pcloud';A='auto';_sync_scheduler_from_windows(self.engine.state);st=self.engine.state;fs=self.metrics[_k];dlg,p,host=self._make_dialog('Налаштування програми, тем, масштабу, GFS та Планувальника',1040,700,scrollable=_S,min_outer_w=960,min_outer_h=650);v_keep_n=tk.IntVar(value=st.get(N,5));v_daily=tk.IntVar(value=st.get(O,7));v_today=tk.IntVar(value=st.get(P,2));v_week=tk.IntVar(value=st.get(Q,4));v_month=tk.IntVar(value=st.get(R,12));v_year=tk.IntVar(value=st.get(S,3));v_trash=tk.BooleanVar(value=st.get(_AK,_A1)==_A1);v_sclean=tk.BooleanVar(value=bool(st.get(T,_S)));v_theme=tk.StringVar(value=st.get(U,D));v_scale=tk.StringVar(value=st.get(F,A));v_font=tk.IntVar(value=int(st.get(V,0)));v_lang=tk.StringVar(value=st.get(_F,_E));v_tray_min=tk.BooleanVar(value=bool(st.get(W,_H)));v_tray_backend=tk.StringVar(value=str(st.get(X,A)));v_logs_dir=tk.StringVar(value=st.get(E,''));v_net_cnt=tk.IntVar(value=int(st.get(Y,0)or 0));v_net_gb=tk.DoubleVar(value=float(st.get(Z,_T)or _T));v_net_free=tk.BooleanVar(value=bool(st.get(a,_H)));v_dl_buf=tk.StringVar(value=f"{int(st.get(b,64)or 64)} КБ");v_pstyle=tk.StringVar(value=st.get(c,'v8'));v_cloud_enabled=tk.BooleanVar(value=bool(st.get(d,_S)));v_cloud_provider=tk.StringVar(value=e);v_cloud_new_remote=tk.StringVar(value=B);v_cloud_remote=tk.StringVar(value=B);v_cloud_save_archives=tk.BooleanVar(value=bool(st.get(f,_H)));v_cloud_save_logs=tk.BooleanVar(value=bool(st.get(g,_H)));v_cloud_path=tk.StringVar(value=st.get(h,i));v_cloud_max_cnt=tk.IntVar(value=int(st.get(j,0)or 0));v_cloud_max_gb=tk.DoubleVar(value=float(st.get(k,_T)or _T));v_cloud_fit_free=tk.BooleanVar(value=bool(st.get(l,_H)));v_journal_target=tk.StringVar(value=st.get(m,A));sch_parts=(st.get(n)or'03:00').split(':');v_sh=tk.StringVar(value=sch_parts[0]if len(sch_parts)>0 else'03');v_sm=tk.StringVar(value=sch_parts[1]if len(sch_parts)>1 else'00');v_smode=tk.StringVar(value=st.get(G,H));v_sprio=tk.IntVar(value=int(st.get(I,6)));v_smissed=tk.BooleanVar(value=bool(st.get(J,_H)));v_swake=tk.BooleanVar(value=bool(st.get(K,_S)));v_gsi=tk.BooleanVar(value=bool(st.get('global_speed_optin',_S)));v_bn=tk.BooleanVar(value=bool(st.get('show_bottleneck',_H)));v_d1c=tk.BooleanVar(value=bool(st.get('d1_use_cache',_H)));v_dcw=tk.BooleanVar(value=bool(st.get('direct_cloud_write',_S)));bf=tk.Frame(dlg,bg=p[_G],bd=1,relief=_Y);bf.pack(side=_Z,fill=_C,padx=12,pady=(4,8));from gui.widgets import SidebarNavItem,make_ui_icons;split_wrap=tk.Frame(host,bg=p[_G]);split_wrap.pack(fill=_W,expand=_H);sb_w=max(255,int(round(fs*25)));sidebar=tk.Frame(split_wrap,bg=p[_G],width=sb_w,padx=10,pady=10);sidebar.pack(side=_J,fill=_o);sidebar.pack_propagate(_S);v_sep=tk.Frame(split_wrap,bg=p[_P],width=1);v_sep.pack(side=_J,fill=_o);right_wrap=tk.Frame(split_wrap,bg=p[_G]);right_wrap.pack(side=_J,fill=_W,expand=_H);_r_cv=tk.Canvas(right_wrap,bg=p[_G],highlightthickness=0,bd=0);_r_vsb=tk.Scrollbar(right_wrap,orient=_z,command=_r_cv.yview);content_area=tk.Frame(_r_cv,bg=p[_G],padx=8,pady=6);content_area.bind(_d,lambda _e:_r_cv.configure(scrollregion=_r_cv.bbox(_A0)));_r_win=_r_cv.create_window((0,0),window=content_area,anchor='nw');_r_cv.bind(_d,lambda e:_r_cv.itemconfigure(_r_win,width=e.width));_r_cv.configure(yscrollcommand=_r_vsb.set);_r_vsb.pack(side=_K,fill=_o);_r_cv.pack(side=_J,fill=_W,expand=_H);dlg.bind(_AQ,lambda ev:_r_cv.yview_scroll(int(-1*(ev.delta/120)),'units'));tab_bkp=tk.Frame(content_area,bg=p[_G]);tab_sched=tk.Frame(content_area,bg=p[_G]);tab_cloud=tk.Frame(content_area,bg=p[_G]);tab_ui=tk.Frame(content_area,bg=p[_G]);tab_sys=tk.Frame(content_area,bg=p[_G]);_pages=[tab_bkp,tab_sched,tab_ui,tab_sys];_nav_items=[];_grp_lbls=[];_s_icons={}if self.engine.state.get(_A8,_S)else make_ui_icons(max(15,fs+4),p[_D],p[_Q]);_nav_specs=[('ПРОГРАМА ТА КОПІЇ',o,'🛡',q,_S),(_M,'hist','🕒',r,_H),('СИСТЕМА ТА ХМАРА','gear','⚙',s,_S),(_M,o,'🔒',t,_S)];_init_map={0:0,1:2,2:0};_start_idx=_init_map.get(int(initial_tab),int(initial_tab))if int(initial_tab)in(0,1,2,3)else 0;_cur_tab={C:_start_idx}
		def _select_pill_tab(idx):
			_cur_tab[C]=idx
			for(i_p,pg)in enumerate(_pages):
				if i_p==idx:pg.pack(fill=_W,expand=_H)
				else:pg.pack_forget()
			for(i_n,nav_w)in enumerate(_nav_items):nav_w.set_active(i_n==idx)
			try:_r_cv.yview_moveto(_T)
			except Exception:0
		row_h=max(38,int(round(40*self.metrics[_a])))
		for(i_n,(grp_k,ico_k,fb_s,cap_k,add_gap))in enumerate(_nav_specs):
			if grp_k:gl=tk.Label(sidebar,text=tr(grp_k,st.get(_F,_E)),bg=p[_G],fg=p[_O],anchor=_L,font=(self._ui_fam(),max(8,fs-2),_I));gl.pack(fill=_C,padx=10,pady=(4 if i_n==0 else 8,5));_grp_lbls.append((gl,grp_k))
			nav_w=SidebarNavItem(sidebar,_s_icons.get(ico_k),fb_s,tr(cap_k,st.get(_F,_E)),on_click=lambda ix=i_n:_select_pill_tab(ix),palette=p,font_fam=self._ui_fam(),font_sz=fs,height_px=row_h);nav_w.pack(fill=_C,pady=(0,8 if add_gap else 3));_nav_items.append(nav_w)
		_select_pill_tab(_cur_tab[C]);f_gfs=tk.Frame(tab_bkp,bg=p[_A],bd=0,highlightthickness=1,highlightbackground=p[_P],padx=16,pady=12);f_gfs.pack(fill=_C,padx=12,pady=(8,8));tk.Label(f_gfs,text=tr('Кільцева стратегія (останні N архівів)',st.get(_F,_E)),bg=p[_A],fg=p[_Q],font=(self._ui_fam(),fs+1,_I)).pack(anchor=_L,pady=(0,8));g_r1=tk.Frame(f_gfs,bg=p[_A]);g_r1.pack(fill=_C,pady=4);tk.Label(g_r1,text=tr('Зберігати останніх архівів (шт.):',st.get(_F,_E)),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);tk.Spinbox(g_r1,from_=1,to=50,textvariable=v_keep_n,width=5,bg=p[_c],fg=p[_D],bd=0,highlightthickness=1,highlightbackground=p[_P],font=(self._ui_fam(),fs,_I)).pack(side=_K);tk.Frame(f_gfs,height=1,bg=p[_P]).pack(fill=_C,pady=6);g_r2=tk.Frame(f_gfs,bg=p[_A]);g_r2.pack(fill=_C,pady=2);tk.Label(g_r2,text=tr('У Кошик (замість видалення)',st.get(_F,_E)),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(g_r2,variable=v_trash,compact=_H,palette=p,font_sz=fs).pack(side=_K);tk.Frame(f_gfs,height=1,bg=p[_P]).pack(fill=_C,pady=6);g_r3=tk.Frame(f_gfs,bg=p[_A]);g_r3.pack(fill=_C,pady=2);tk.Label(g_r3,text=tr('Автоочищення у фоні (GFS)',st.get(_F,_E)),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(g_r3,variable=v_sclean,compact=_H,palette=p,font_sz=fs).pack(side=_K);f_netr=tk.Frame(tab_bkp,bg=p[_A],bd=0,highlightthickness=1,highlightbackground=p[_P],padx=16,pady=12);tk.Label(f_netr,text='Авторотація мережевої папки (від старих до нових)'if st.get(_F,_E)==_B else'Network Folder Auto-Rotation (oldest first)',bg=p[_A],fg=p[_Q],font=(self._ui_fam(),fs+1,_I)).pack(anchor=_L,pady=(0,6));nr0=tk.Frame(f_netr,bg=p[_A]);nr0.pack(fill=_C,pady=3);tk.Label(nr0,text='Контроль вільного місця на мережевому диску:'if st.get(_F,_E)==_B else'Auto-free space on network drive:',bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(nr0,variable=v_net_free,compact=_H,palette=p,font_sz=fs).pack(side=_K);nr1=tk.Frame(f_netr,bg=p[_A]);nr1.pack(fill=_C,pady=3);tk.Label(nr1,text='Зберігати останніх архівів у мережі (0 = без ліміту):'if st.get(_F,_E)==_B else'Keep last archives in network (0 = unlimited):',bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);tk.Spinbox(nr1,from_=0,to=500,textvariable=v_net_cnt,width=6,bg=p[_c],fg=p[_D],bd=0,highlightthickness=1,highlightbackground=p[_P],font=(self._ui_fam(),fs,_I)).pack(side=_K);nr2=tk.Frame(f_netr,bg=p[_A]);nr2.pack(fill=_C,pady=3);tk.Label(nr2,text='Макс. розмір папки у мережі, ГБ (0 = без ліміту):'if st.get(_F,_E)==_B else'Max network folder size, GB (0 = unlimited):',bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);tk.Spinbox(nr2,from_=_T,to=2e3,increment=.5,format='%.1f',textvariable=v_net_gb,width=6,bg=p[_c],fg=p[_D],bd=0,highlightthickness=1,highlightbackground=p[_P],font=(self._ui_fam(),fs,_I)).pack(side=_K);f_buf=tk.Frame(tab_bkp,bg=p[_A],bd=0,highlightthickness=1,highlightbackground=p[_P],padx=16,pady=12);f_buf.pack(fill=_C,padx=12,pady=(0,8));br1=tk.Frame(f_buf,bg=p[_A]);br1.pack(fill=_C,pady=2);tk.Label(br1,text='Розмір буфера завантаження (КБ):'if st.get(_F,_E)==_B else'Download buffer size (KB):',bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs,_I)).pack(side=_J);ttk.Combobox(br1,textvariable=v_dl_buf,values=['16 КБ','32 КБ','64 КБ',_AL,'256 КБ','512 КБ','1024 КБ'],width=10,state=_e,font=(self._ui_fam(),fs)).pack(side=_K);tk.Frame(f_buf,height=1,bg=p[_P]).pack(fill=_C,pady=6);br2=tk.Frame(f_buf,bg=p[_A]);br2.pack(fill=_C,pady=2);tk.Label(br2,text='\u041f\u0438\u0441\u0430\u0442\u0438 \u043d\u0430\u043f\u0440\u044f\u043c\u0443 \u0432 \u0445\u043c\u0430\u0440\u043d\u0443/\u043c\u0435\u0440\u0435\u0436\u0435\u0432\u0443 \u043f\u0430\u043f\u043a\u0443 (\u0431\u0435\u0437 \u0442\u0438\u043c\u0447\u0430\u0441\u043e\u0432\u043e\u0457):'if st.get(_F,_E)==_B else'Write directly to cloud/network folder (skip temp):',bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(br2,variable=v_dcw,compact=_H,palette=p,font_sz=fs).pack(side=_K);f_logs=tk.Frame(tab_bkp,bg=p[_A],bd=0,highlightthickness=1,highlightbackground=p[_P],padx=16,pady=12);f_logs.pack(fill=_C,padx=12,pady=(0,8));tk.Label(f_logs,text=tr('Папка файлів протоколів (backup.log та звіти)',st.get(_F,_E)),bg=p[_A],fg=p[_Q],font=(self._ui_fam(),fs+1,_I)).pack(anchor=_L,pady=(0,6));lg_r1=tk.Frame(f_logs,bg=p[_A]);lg_r1.pack(fill=_C,pady=2);ent_ld=tk.Entry(lg_r1,textvariable=v_logs_dir,bg=p[_c],fg=p[_D],insertbackground=p[_D],bd=0,highlightthickness=1,highlightbackground=p[_P],font=(self._ui_fam(),fs));ent_ld.pack(side=_J,fill=_C,expand=_H,ipady=4,padx=(0,6))
		def _pick_logs_d():
			from core.files import choose_folder_native;ch=choose_folder_native(v_logs_dir.get().strip()or st.get(_p,''))
			if ch:v_logs_dir.set(ch)
		tk.Button(lg_r1,text='📂',command=_pick_logs_d,bg=p[_c],fg=p[_D],bd=0,padx=10,pady=3,cursor=_R).pack(side=_J,padx=(0,6));tk.Button(lg_r1,text=tr('Як папка архівів',st.get(_F,_E)),command=lambda:v_logs_dir.set(''),bg=p[_c],fg=p[_O],bd=0,padx=10,pady=3,cursor=_R).pack(side=_J);tk.Label(f_logs,text=tr('Порожньо = зберігати поруч із ZIP-архівами (у папці «Архіви»).',st.get(_F,_E)),bg=p[_A],fg=p[_O],font=(self._ui_fam(),max(8,fs-1))).pack(anchor=_L,pady=(4,6));tk.Frame(f_logs,height=1,bg=p[_P]).pack(fill=_C,pady=4);f_sch=tk.Frame(tab_sched,bg=p[_A],bd=0,highlightthickness=1,highlightbackground=p[_P],padx=16,pady=12);f_sch.pack(fill=_C,padx=12,pady=(8,8));tk.Label(f_sch,text=tr('Автозапуск за розкладом',st.get(_F,_E)),bg=p[_A],fg=p[_Q],font=(self._ui_fam(),fs+1,_I)).pack(anchor=_L,pady=(0,8));sr1=tk.Frame(f_sch,bg=p[_A]);sr1.pack(fill=_C,pady=4);tk.Label(sr1,text=tr('Час щодня:',st.get(_F,_E)),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs,_I)).pack(side=_J);t_box=tk.Frame(sr1,bg=p[_A]);t_box.pack(side=_K);ttk.Combobox(t_box,textvariable=v_sh,values=[f"{i:02d}"for i in range(24)],width=4,state=_e,font=(self._ui_fam(),fs)).pack(side=_J);tk.Label(t_box,text=':',bg=p[_A],fg=p[_Q],font=(self._ui_fam(),fs,_I)).pack(side=_J,padx=4);ttk.Combobox(t_box,textvariable=v_sm,values=[f"{i:02d}"for i in range(60)],width=4,state=_e,font=(self._ui_fam(),fs)).pack(side=_J);tk.Frame(f_sch,height=1,bg=p[_P]).pack(fill=_C,pady=6);sr_m=tk.Frame(f_sch,bg=p[_A]);sr_m.pack(fill=_C,pady=2);tk.Radiobutton(sr_m,text=tr('У фоні (з іконкою в треї)',st.get(_F,_E)),variable=v_smode,value=H,bg=p[_A],fg=p[_D],selectcolor=p[_c],activebackground=p[_A],activeforeground=p[_D],font=(self._ui_fam(),fs)).pack(side=_J,padx=(0,16));tk.Radiobutton(sr_m,text=tr('З вікном консолі',st.get(_F,_E)),variable=v_smode,value=w,bg=p[_A],fg=p[_D],selectcolor=p[_c],activebackground=p[_A],activeforeground=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);from core.config import IS_MAC as _IS_MAC_S,IS_WINDOWS as _IS_WIN_S,IS_WSL as _IS_WSL_S
		if _IS_WIN_S:tk.Frame(f_sch,height=1,bg=p[_P]).pack(fill=_C,pady=6);sr2=tk.Frame(f_sch,bg=p[_A]);sr2.pack(fill=_C,pady=2);tk.Label(sr2,text=tr('Пріоритет (2-9):',st.get(_F,_E)),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);tk.Spinbox(sr2,from_=2,to=9,textvariable=v_sprio,width=4,bg=p[_c],fg=p[_D],bd=0,highlightthickness=1,highlightbackground=p[_P],font=(self._ui_fam(),fs)).pack(side=_K);tk.Frame(f_sch,height=1,bg=p[_P]).pack(fill=_C,pady=6);sr2b=tk.Frame(f_sch,bg=p[_A]);sr2b.pack(fill=_C,pady=2);tk.Label(sr2b,text=tr('Запускати пропущене',st.get(_F,_E)),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(sr2b,variable=v_smissed,compact=_H,palette=p,font_sz=fs).pack(side=_K);tk.Frame(f_sch,height=1,bg=p[_P]).pack(fill=_C,pady=6);sr2c=tk.Frame(f_sch,bg=p[_A]);sr2c.pack(fill=_C,pady=2);tk.Label(sr2c,text=tr('Розбудити ПК зі сну',st.get(_F,_E)),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(sr2c,variable=v_swake,compact=_H,palette=p,font_sz=fs).pack(side=_K)
		else:lng_n=st.get(_F,_E);os_note=('WSL: розклад реєструється у Планувальнику Windows (schtasks.exe).'if lng_n==_B else'WSL: schedule uses Windows Task Scheduler (schtasks.exe).')if _IS_WSL_S else('macOS: розклад працює через системний агент LaunchAgent.'if lng_n==_B else'macOS: schedule runs via native LaunchAgent.')if _IS_MAC_S else'Linux: розклад працює через crontab та ~/.config/autostart.'if lng_n==_B else'Linux: schedule runs via crontab & ~/.config/autostart.';tk.Label(f_sch,text=os_note,bg=p[_A],fg=p[_O],font=(self._ui_fam(),max(8,fs-1))).pack(anchor=_L,pady=(2,3))
		lbl_sch_msg=tk.Label(f_sch,text='',bg=p[_A],fg=p[_U],font=(_N,fs,_I));lbl_sch_msg.pack(side=_J,padx=8);sr3=tk.Frame(f_sch,bg=p[_A]);sr3.pack(fill=_C,pady=(2,0))
		def _create_task():t_str=f"{v_sh.get()}:{v_sm.get()}";st[n]=t_str;st[G]=v_smode.get();st[J]=v_smissed.get();st[K]=v_swake.get();st[I]=int(v_sprio.get());commit_state(st);ok_s,msg_s=_manage_windows_scheduler('create',t_str,st[G],st[J],st[K],st[I]);lbl_sch_msg.configure(text=msg_s,fg=p[_U]if ok_s else p[_V]);self.engine.log(msg_s,'ok'if ok_s else _h)
		def _del_task():ok_s,msg_s=_manage_windows_scheduler('delete');lbl_sch_msg.configure(text=msg_s,fg=p[_b]if ok_s else p[_V]);self.engine.log(msg_s,_AE if ok_s else _h)
		def _copy_cmd(flag):cmd=_build_run_cmd(flag);self.root.clipboard_clear();self.root.clipboard_append(cmd);lbl_sch_msg.configure(text=tr(f"✓ Скопійовано у буфер: {cmd}",st.get(_F,_E)),fg=p[_Q])
		def _export_cfg():
			import json as _j;from tkinter import filedialog;fp=filedialog.asksaveasfilename(defaultextension='.json',initialfile='homegrid_backup_settings.json',filetypes=[(x,y)])
			if not fp:return
			skip_k={z,A0,A1,A2,'_jar','dirty',A3,_AF};data={k:v for(k,v)in st.items()if k not in skip_k}
			with open(fp,_L,encoding='utf-8')as fo:_j.dump(data,fo,indent=2,ensure_ascii=_S)
			lbl_sch_msg.configure(text=tr('✓ Налаштування експортовано у JSON',st.get(_F,_E)),fg=p[_U])
		def _import_cfg():
			import json as _j;from tkinter import filedialog;fp=filedialog.askopenfilename(filetypes=[(x,y)])
			if not fp:return
			with open(fp,'r',encoding='utf-8')as fi:data=_j.load(fi)
			skip_k={z,A0,A1,A2,'_jar','dirty',A3,_AF}
			for(k,v)in data.items():
				if k in st and k not in skip_k:st[k]=v
			commit_state(st);self.var_srv.set(st.get(_A3,''));self.var_dir.set(st.get(_p,''));self.apply_theme_and_mode(resize_win=_H);dlg.destroy();self.open_settings()
		tk.Button(sr3,text='Додати в Планувальник',command=_create_task,bg=p[_U],fg=p[_v],font=(_N,fs,_I),padx=12,pady=4,cursor=_R).pack(side=_J,padx=(0,10));tk.Button(sr3,text=tr('Видалити задачу',st.get(_F,_E)),command=_del_task,bg=p[_A],fg=p[_V],bd=0,highlightthickness=0,font=(self._ui_fam(),fs),padx=10,pady=4,cursor=_R).pack(side=_J,padx=6)
		def _open_adv_sched():lng_m=st.get(_F,_E);m_adv=tk.Menu(dlg,tearoff=0,bg=p[_G],fg=p[_D],font=(_N,fs));m_adv.add_command(label=tr('Копіювати команду фонового запуску',lng_m),command=lambda:_copy_cmd(H));m_adv.add_command(label=tr('Копіювати команду консольного запуску',lng_m),command=lambda:_copy_cmd(w));m_adv.tk_popup(btn_adv.winfo_rootx(),btn_adv.winfo_rooty()+btn_adv.winfo_height())
		btn_adv=tk.Button(sr3,text=tr('Додатково ▾',st.get(_F,_E)),command=_open_adv_sched,bg=p[_A],fg=p[_Q],bd=0,highlightthickness=0,font=(self._ui_fam(),fs),padx=10,pady=4,cursor=_R);btn_adv.pack(side=_K);bot_col=tk.Frame(tab_ui,bg=p[_G]);bot_col.pack(fill=_W,expand=_H,padx=12,pady=(8,4));f_thm=tk.Frame(bot_col,bg=p[_A],bd=0,highlightthickness=1,highlightbackground=p[_P],padx=16,pady=12);f_thm.pack(fill=_C,pady=(0,8));tk.Label(f_thm,text=tr('Оформлення, мова та масштаб екрана',st.get(_F,_E)),bg=p[_A],fg=p[_Q],font=(self._ui_fam(),fs+1,_I)).pack(anchor=_L,pady=(0,10));ug=tk.Frame(f_thm,bg=p[_A]);ug.pack(fill=_C);c00=tk.Frame(ug,bg=p[_A]);c00.pack(fill=_C,pady=4);tk.Label(c00,text=tr('Мова інтерфейсу:',st.get(_F,_E)),anchor=_L,bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);lang_map={L:_E,A4:_B};rev_lang={_E:L,_B:A4};cb_lang=ttk.Combobox(c00,values=list(lang_map.keys()),state=_e,width=26,font=(self._ui_fam(),fs));cb_lang.set(rev_lang.get(v_lang.get(),L));cb_lang.pack(side=_K);tk.Frame(ug,height=1,bg=p[_P]).pack(fill=_C,pady=5);c01=tk.Frame(ug,bg=p[_A]);c01.pack(fill=_C,pady=4);tk.Label(c01,text=tr('Тема оформлення:',st.get(_F,_E)),anchor=_L,bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);lng_t=st.get(_F,_E);thm_map={tr(M,lng_t):D,tr(A5,lng_t):'light'};rev_thm={D:tr(M,lng_t),'light':tr(A5,lng_t)};cb_theme=ttk.Combobox(c01,values=list(thm_map.keys()),state=_e,width=26,font=(self._ui_fam(),fs));cb_theme.set(rev_thm.get(v_theme.get(),tr(M,lng_t)));cb_theme.pack(side=_K);tk.Frame(ug,height=1,bg=p[_P]).pack(fill=_C,pady=5);c10=tk.Frame(ug,bg=p[_A]);c10.pack(fill=_C,pady=4);tk.Label(c10,text=tr('Роздільна здатність:',st.get(_F,_E)),anchor=_L,bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);lng_cur=st.get(_F,_E);scale_map={tr(lbl,lng_cur):code for(code,lbl)in UI_SCALE_LABELS};rev_scale={code:tr(lbl,lng_cur)for(code,lbl)in UI_SCALE_LABELS};cb_scale=ttk.Combobox(c10,values=[tr(lbl,lng_cur)for(_,lbl)in UI_SCALE_LABELS],state=_e,width=26,font=(self._ui_fam(),fs));cb_scale.set(rev_scale.get(v_scale.get(),tr(UI_SCALE_LABELS[0][1],lng_cur)));cb_scale.pack(side=_K);tk.Frame(ug,height=1,bg=p[_P]).pack(fill=_C,pady=5);c11=tk.Frame(ug,bg=p[_A]);c11.pack(fill=_C,pady=4);tk.Label(c11,text=tr('Розмір шрифту:',st.get(_F,_E)),anchor=_L,bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);font_map={tr(lbl,lng_cur):code for(code,lbl)in UI_FONT_LABELS};rev_font={code:tr(lbl,lng_cur)for(code,lbl)in UI_FONT_LABELS};cb_font=ttk.Combobox(c11,values=[tr(lbl,lng_cur)for(_,lbl)in UI_FONT_LABELS],state=_e,width=26,font=(self._ui_fam(),fs));cb_font.set(rev_font.get(v_font.get(),tr(UI_FONT_LABELS[0][1],lng_cur)));cb_font.pack(side=_K);tk.Frame(ug,height=1,bg=p[_P]).pack(fill=_C,pady=5);c12=tk.Frame(ug,bg=p[_A]);c12.pack(fill=_C,pady=4);tk.Label(c12,text='Показувати вузьке місце у статистиці швидкості:'if lng_cur==_B else'Show bottleneck in speed statistics:',anchor=_L,bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(c12,variable=v_bn,compact=_H,palette=p,font_sz=fs).pack(side=_K);tk.Frame(ug,height=1,bg=p[_P]).pack(fill=_C,pady=5);c13=tk.Frame(ug,bg=p[_A]);c13.pack(fill=_C,pady=4);tk.Label(c13,text='Брати участь у глобальному рейтингу D1:'if lng_cur==_B else'Participate in Global D1 speed ranking:',anchor=_L,bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(c13,variable=v_gsi,compact=_H,palette=p,font_sz=fs).pack(side=_K);tk.Frame(ug,height=1,bg=p[_P]).pack(fill=_C,pady=5);c14=tk.Frame(ug,bg=p[_A]);c14.pack(fill=_C,pady=4);tk.Label(c14,text='\u0412\u0438\u043a\u043e\u0440\u0438\u0441\u0442\u043e\u0432\u0443\u0432\u0430\u0442\u0438 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u0438\u0439 \u043a\u0435\u0448 D1:'if lng_cur==_B else'Use local D1 cache:',anchor=_L,bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(c14,variable=v_d1c,compact=_H,palette=p,font_sz=fs).pack(side=_K);tk.Frame(ug,height=1,bg=p[_P]).pack(fill=_C,pady=5);c15=tk.Frame(ug,bg=p[_A]);c15.pack(fill=_C,pady=4);lbl_d1_u=tk.Label(c15,text='',bg=p[_A],fg=p[_Q],font=(self._ui_fam(),max(8,fs-1)));btn_d1_u=tk.Button(c15,text='\u2601 \u0412\u0438\u0432\u0430\u043d\u0442\u0430\u0436\u0438\u0442\u0438 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u0456 \u0434\u0430\u043d\u0456 \u0443 D1'if lng_cur==_B else'\u2601 Upload local data to D1',command=lambda:(btn_d1_u.configure(state='disabled'),lbl_d1_u.configure(text='...'if lng_cur==_B else'...',fg=p[_Q]),__import__('core.speed_bench',fromlist=['sync_local_history_to_d1']).sync_local_history_to_d1(self.engine.state,__import__('core.cloud',fromlist=['fetch_cloud_speed_stats']).fetch_cloud_speed_stats(self.engine,refresh=_H).get('ops',[]),log_fn=self.engine.log,force=_H,on_done=lambda c:dlg.winfo_exists()and dlg.after(0,lambda:(btn_d1_u.configure(state=_A2),lbl_d1_u.configure(text=(f'\u2714 {c} \u0437\u0430\u043f.'if lng_cur==_B else f'\u2714 {c} sent')if c>0 else('0'if c==0 else'Busy'),fg=p[_U]if c>0 else p[_b]))))),bg=p[_c],fg=p[_Q],bd=0,highlightthickness=1,highlightbackground=p[_P],font=(self._ui_fam(),fs,_I),padx=12,pady=4,cursor=_R);btn_d1_u.pack(side=_J);lbl_d1_u.pack(side=_K,padx=(8,0));f_sec=tk.Frame(tab_sys,bg=p[_A],bd=0,highlightthickness=1,highlightbackground=p[_P],padx=16,pady=12);f_sec.pack(fill=_C,padx=12,pady=(8,8));tk.Label(f_sec,text=tr('Системний трей, профіль та PIN',st.get(_F,_E)),bg=p[_A],fg=p[_Q],font=(self._ui_fam(),fs+1,_I)).pack(anchor=_L,pady=(0,8));tr_row=tk.Frame(f_sec,bg=p[_A]);tr_row.pack(fill=_C,pady=(0,6));tk.Label(tr_row,text=tr('Згортати у трей при закритті',st.get(_F,_E)),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);HomeGridToggle(tr_row,variable=v_tray_min,compact=_H,palette=p,font_sz=fs).pack(side=_K);import sys as _sys_tray;_lng_tray=st.get(_F,_E);from gui.tray import _LINUX_TRAY_MODES,_MAC_TRAY_MODES,TRAY_MODE_HINTS;_modes_t=_MAC_TRAY_MODES if _sys_tray.platform=='darwin'else _LINUX_TRAY_MODES;_tray_labels={A:tr('Авто (рекомендовано)',_lng_tray),'appindicator':'AppIndicator (Ubuntu, GNOME, XFCE)','sni-bridge':'StatusNotifier bridge (Wayland)','gtk':'X11 Tkinter-меню (запасний)','xorg':'XEmbed (класичний X11 трей)','none':tr('Вимкнено',_lng_tray),'pystray':'pystray (верхнє меню macOS)'};_tray_rev={v:k for(k,v)in _tray_labels.items()};tr_mode_row=tk.Frame(f_sec,bg=p[_A]);tr_mode_row.pack(fill=_C,pady=(0,4));tk.Label(tr_mode_row,text=tr('Режим трею (для тесту)',_lng_tray),bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs)).pack(side=_J);cb_tray_mode=ttk.Combobox(tr_mode_row,values=[_tray_labels[m]for m in _modes_t],state=_e,width=34,font=(self._ui_fam(),fs));cb_tray_mode.set(_tray_labels.get(v_tray_backend.get(),_tray_labels[A]));cb_tray_mode.pack(side=_K);lbl_tray_hint=tk.Label(f_sec,text='',justify=_J,wraplength=520,anchor=_L,bg=p[_A],fg=p[_b],font=(self._ui_fam(),max(8,fs-1)));lbl_tray_hint.pack(fill=_C,pady=(0,6))
		def _refresh_tray_hint(_e=_M):key=_tray_rev.get(cb_tray_mode.get(),A);hint=TRAY_MODE_HINTS.get(key,'');note=tr('Після зміни режиму перезапустіть застосунок. Результат дивіться в журналі: рядок [TRAY MODE] і «Значок системного трею активовано».',_lng_tray);lbl_tray_hint.configure(text=(hint+'\n'if hint else'')+note)
		cb_tray_mode.bind(_AR,_refresh_tray_hint);_refresh_tray_hint();tk.Frame(f_sec,height=1,bg=p[_P]).pack(fill=_C,pady=6);sec_r=tk.Frame(f_sec,bg=p[_A]);sec_r.pack(fill=_C);tk.Button(sec_r,text=tr('Зберегти налаштування',st.get(_F,_E)),command=_export_cfg,bg=p[_c],fg=p[_Q],bd=0,highlightthickness=0,font=(self._ui_fam(),fs),padx=12,pady=5,cursor=_R).pack(side=_J,padx=(0,8));tk.Button(sec_r,text=tr('Відновити налаштування',st.get(_F,_E)),command=_import_cfg,bg=p[_c],fg=p[_Q],bd=0,highlightthickness=0,font=(self._ui_fam(),fs),padx=12,pady=5,cursor=_R).pack(side=_J,padx=(0,8));tk.Button(sec_r,text=tr('Скинути PIN',st.get(_F,_E)),command=lambda:(self.reset_pins(),lbl_sch_msg.configure(text='✓ Збережені PIN-коди очищено',fg=p[_b])),bg=p[_c],fg=p[_V],bd=0,highlightthickness=0,font=(self._ui_fam(),fs),padx=12,pady=5,cursor=_R).pack(side=_K)
		def _commit_settings(close_after):
			selected_tab=_cur_tab[C];cloud_remote=B;cloud_path=v_cloud_path.get().strip()
			if v_cloud_enabled.get():
				if not v_cloud_save_archives.get()and not v_cloud_save_logs.get():lbl_sch_msg.configure(text=tr('Оберіть хоча б один пункт: зберігати архів або журнал.',lang_map.get(cb_lang.get(),_E)),fg=p[_V]);_select_pill_tab(2);return
				try:from core.cloud import validate_cloud_settings;cloud_path=validate_cloud_settings(cloud_remote,cloud_path)
				except ValueError as exc:lbl_sch_msg.configure(text=tr(str(exc),lang_map.get(cb_lang.get(),_E)),fg=p[_V]);_select_pill_tab(2);return
			else:cloud_path=cloud_path or i
			raw_ld=v_logs_dir.get().strip();st[E]=os.path.normpath(os.path.expanduser(raw_ld))if raw_ld else''
			if st[E]:os.makedirs(st[E],exist_ok=_H)
			st[N]=max(1,int(v_keep_n.get()));st[Y]=max(0,int(v_net_cnt.get()or 0));st[Z]=max(_T,round(float(v_net_gb.get()or _T),2));st[a]=bool(v_net_free.get());st[b]=int(v_dl_buf.get().split()[0]);st[O]=max(1,int(v_daily.get()));st[P]=max(1,int(v_today.get()));st[Q]=max(0,int(v_week.get()));st[R]=max(0,int(v_month.get()));st[S]=max(0,int(v_year.get()));st[_F]=lang_map.get(cb_lang.get(),_E);st[U]=thm_map.get(cb_theme.get(),D);st[_AK]=_A1 if v_trash.get()else'direct';st[W]=bool(v_tray_min.get());st[X]=_tray_rev.get(cb_tray_mode.get(),A);st[T]=bool(v_sclean.get());st[d]=bool(v_cloud_enabled.get());st['cloud_remote']=B;st[f]=bool(v_cloud_save_archives.get());st[g]=bool(v_cloud_save_logs.get());st[h]=cloud_path
			if hasattr(self,'var_cloud_path'):self.var_cloud_path.set(cloud_path)
			st[j]=max(0,int(v_cloud_max_cnt.get()or 0));st[k]=max(_T,round(float(v_cloud_max_gb.get()or _T),2));st[l]=bool(v_cloud_fit_free.get());st[m]=A;old_sc=st.get(F,A);new_sc=scale_map.get(cb_scale.get(),A);st[F]=new_sc;st[V]=font_map.get(cb_font.get(),0);st[c]='v8';st['global_speed_optin']=bool(v_gsi.get());st['show_bottleneck']=bool(v_bn.get());st['d1_use_cache']=bool(v_d1c.get());st['direct_cloud_write']=bool(v_dcw.get());commit_state(st);self.apply_theme_and_mode(resize_win=new_sc!=old_sc);self.engine.log('Налаштування програми, теми, шрифту та стратегії GFS застосовано.','ok');dlg.destroy()
			if not close_after:self.open_settings(initial_tab=selected_tab)
		bf.configure(bd=0,highlightthickness=1,highlightbackground=p[_P]);tk.Button(bf,text=tr(_A6,st.get(_F,_E)),command=dlg.destroy,bg=p[_G],fg=p[_Q],bd=0,highlightthickness=0,font=(self._ui_fam(),fs),padx=12,pady=6,cursor=_R).pack(side=_K,padx=(4,6),pady=4);tk.Button(bf,text=tr('Зберегти та закрити',st.get(_F,_E)),command=lambda:_commit_settings(_H),bg=p[_U],fg=p[_v],bd=0,highlightthickness=0,font=(self._ui_fam(),fs,_I),padx=16,pady=6,cursor=_R).pack(side=_K,padx=6,pady=4);tk.Button(bf,text=tr('Застосувати',st.get(_F,_E)),command=lambda:_commit_settings(_S),bg=p[_y],fg=_l,bd=0,highlightthickness=0,font=(self._ui_fam(),fs,_I),padx=16,pady=6,cursor=_R).pack(side=_K,padx=6,pady=4)
		def _i18n_settings():
			lng=st.get(_F,_E)
			for(_gl,_gk)in _grp_lbls:_gl.configure(text=tr(_gk,lng))
			for(_ib,_tc)in enumerate((q,r,s,t)):_nav_items[_ib].set_active(_ib==_cur_tab[C],text_override=tr(_tc,lng))
			apply_widget_i18n(dlg,lng)
		_i18n_settings()
	def open_analyze(self):
		M='Перевірити SHA-256 + CRC32';L='🗑 Пошкоджених: 0';K='HGB.Horizontal.TProgressbar';J='value';I='btn_txt';H='stage';G='stop';F='disabled';E='res';D='pct';C='running';B='name';A='status_map';import threading;fs=self.metrics[_k];bpx,bpy=self.metrics['btn_px'],self.metrics['btn_py'];fam=_A9 if self.engine.state.get(_A8,_S)else self._get_palette().get('font',_N);dlg,p,_=self._make_dialog('Аналіз локального сховища (GFS та SHA-256)',880,540);lbl_sum=tk.Label(dlg,text='',bg=p[_G],fg=p[_Q],font=(fam,fs,_I));lbl_sum.pack(anchor=_L,padx=14,pady=(10,4));bf=tk.Frame(dlg,bg=p[_G]);bf.pack(side=_Z,fill=_C,padx=14,pady=(4,10));_v_st=ttk.Style()
		try:_v_st.theme_use('clam')
		except Exception:0
		_v_st.configure(K,troughcolor=p[_f],background=p[_U],bordercolor=p[_P],lightcolor=p[_U],darkcolor=p[_U]);verify_bar=ttk.Progressbar(dlg,mode='determinate',maximum=100,style=K);verify_bar.pack(side=_Z,fill=_C,padx=14,pady=(2,4));verify_status=tk.Label(dlg,text='Перевірка не запущена',bg=p[_G],fg=p[_O],anchor=_L,font=(fam,max(8,fs-1)));verify_status.pack(side=_Z,fill=_C,padx=14,pady=(2,0));lbl_ver=tk.Label(dlg,text='',bg=p[_G],fg=p[_O],anchor=_L,font=(fam,max(8,fs-1),_I));lbl_ver.pack(side=_Z,fill=_C,padx=14,pady=(4,0));wrap=tk.Frame(dlg,bg=p[_f],bd=1,relief=_Y);wrap.pack(fill=_W,expand=_H,padx=14,pady=(2,4));cv=tk.Canvas(wrap,bg=p[_f],highlightthickness=0,bd=0);vsb=tk.Scrollbar(wrap,orient=_z,command=cv.yview);list_box=tk.Frame(cv,bg=p[_f]);list_box.bind(_d,lambda _e:cv.configure(scrollregion=cv.bbox(_A0)));win_id=cv.create_window((0,0),window=list_box,anchor='nw');cv.bind(_d,lambda e:cv.itemconfigure(win_id,width=e.width));cv.configure(yscrollcommand=vsb.set);vsb.pack(side=_K,fill=_o);cv.pack(side=_J,fill=_W,expand=_H);from core.files import remove_backup_file
		def remove_file_smart(path_to_del,use_trash=_H):remove_backup_file(path_to_del,_A1 if use_trash else'direct')
		_lng_a=self.engine.state.get(_F,_E);buf_options={tr(k,_lng_a):v for(k,v)in(('4 КБ',4096),('16 КБ',16384),(_AL,131072),('256 КБ',262144),('1 МБ',1048576),('4 МБ',4194304),('8 МБ',8388608))};v_buf=tk.StringVar(value=tr(_AL,_lng_a));verify_state={C:_S,G:_S,D:0,H:'',E:_M,_h:_M,A:{}}
		def _delete_archive_pair(fname):
			bdir=self.engine.state.get(_p,'')
			if not bdir:return
			use_trash=self.engine.state.get(_AK,_A1)==_A1;z_path=os.path.join(bdir,fname)
			if os.path.exists(z_path):remove_file_smart(z_path,use_trash)
			if os.path.exists(z_path+_A4):remove_file_smart(z_path+_A4,use_trash)
			verify_state[A].pop(fname,_M);self.engine.log(f"Видалено пошкоджений архів: {fname}",_AE)
		def _upd_del_bad_btn():
			bdir=self.engine.state.get(_p,'');bad_names=[fn for(fn,st_i)in verify_state[A].items()if st_i.get(_q)==_h and os.path.exists(os.path.join(bdir,fn))]
			if bad_names:btn_del_bad.configure(text=tr(f"🗑 Видалити пошкоджені ({len(bad_names)})",self.engine.state.get(_F,_E)),state=_A2,bg=p[_V],fg=_l)
			else:btn_del_bad.configure(text=tr(L,self.engine.state.get(_F,_E)),state=F,bg=p[_A],fg=p[_O])
		def _verify_progress(pct,stage):verify_state[D]=pct;verify_state[H]=stage
		def _poll_verify():
			I='cancelled';F='err_cnt'
			if not dlg.winfo_exists():verify_state[G]=_H;return
			if verify_state[C]:verify_bar[J]=verify_state[D];_st_tr=tr(verify_state[H],self.engine.state.get(_F,_E));verify_status.configure(text=f"{verify_state[D]}% — {_st_tr}",fg=p[_Q]);dlg.after(120,_poll_verify);return
			btn_verify.configure(text=tr(M,self.engine.state.get(_F,_E)),state=_A2);cb_buf.configure(state=_e);lng_v=self.engine.state.get(_F,_E)
			if verify_state[_h]:verify_status.configure(text=tr(f"Помилка перевірки: {verify_state[_h]}",lng_v),fg=p[_V])
			elif verify_state[E]:
				res=verify_state[E];verify_state[A]={it[B]:it for it in res.get('items',[])};history_changed=_S;history=getattr(self.engine,_AG,[])or[]
				for history_item in history:
					archive_name=_operation_archive_name(history_item.get(_AH,''));result_item=verify_state[A].get(archive_name);archive_path=os.path.join(self.engine.state.get(_p,''),archive_name)
					if not result_item or not archive_name or not os.path.isfile(archive_path):continue
					history_item[_AM]=result_item.get(_q,'');history_item[_AS]=result_item.get(_AH,'');history_item[_AT]=os.path.getmtime(archive_path);history_changed=_H
				if history_changed:self.engine.state[_AG]=history;commit_state(self.engine.state)
				ok_all=res[F]==0 and not res.get(I);perf_txt=f"Час: {res.get('elapsed',0):.2f} с | Швидкість: {res.get('speed_mbs',0)} МБ/с (буфер {v_buf.get()})";prefix='Зупинено! 'if res.get(I)else'';msg=tr(f"{prefix}SHA-256 + CRC32: справних {res['ok_cnt']} | без .sha256: {res['warn_cnt']} | пошкоджених: {res[F]} | {perf_txt}",lng_v);lbl_ver.configure(text=msg,fg=p[_U]if ok_all else p[_b]);verify_status.configure(text=tr(f"100% — Усі {res['total']} архівів ({res.get('total_mb',0)} МБ) | {perf_txt}",lng_v));verify_bar[J]=100;self.engine.log(msg,'ok'if ok_all else _AE);_refresh()
		def _verify():
			lng_v=self.engine.state.get(_F,_E)
			if verify_state[C]:verify_state[G]=_H;btn_verify.configure(text=tr('Зупинка...',lng_v),state=F);return
			verify_state.update({C:_H,G:_S,D:0,H:tr('Запуск...',lng_v),E:_M,_h:_M});btn_verify.configure(text=tr('Зупинити',lng_v));cb_buf.configure(state=F);chosen_buf=buf_options.get(v_buf.get(),131072);lbl_ver.configure(text=tr(f"Перевірка архівів (буфер {v_buf.get()})…",lng_v),fg=p[_Q]);verify_bar[J]=0
			def _worker():
				try:verify_state[E]=verify_all_archives(self.engine.state,_verify_progress,buf_size=chosen_buf,cancel_flag=verify_state)
				except Exception as exc:verify_state[_h]=str(exc)
				finally:verify_state[C]=_S
			threading.Thread(target=_worker,daemon=_H).start();dlg.after(120,_poll_verify)
		def _refresh():
			C='new_tag';lng_r=self.engine.state.get(_F,_E)
			for w in list_box.winfo_children():w.destroy()
			all_items,keep_items,del_items=compute_gfs_plan(self.engine.state);tot_mb=round(sum(x[_r]for x in all_items)/1048576.,1);del_mb=round(sum(x[_r]for x in del_items)/1048576.,1);no_sha=sum(1 for x in all_items if not os.path.exists(x['path']+_A4));lbl_sum.configure(text=tr(f"Всього: {len(all_items)} ({tot_mb} МБ) | Залишиться: {len(keep_items)} | Застарілих: {len(del_items)} ({del_mb} МБ) | Без .sha256: {no_sha}",lng_r));_upd_del_bad_btn()
			if'btn_clean_exp'in locals():btn_clean_exp.configure(state=_A2 if del_items else F,bg=p[_b]if del_items else p[_A],fg=p[I]if del_items else p[_O],disabledforeground=p[_O])
			if not all_items:tk.Label(list_box,text=tr('У папці поки немає ZIP-архівів.',lng_r),bg=p[_f],fg=p[_O],font=(fam,fs)).pack(pady=16);return
			for it in all_items:
				row=tk.Frame(list_box,bg=p[_A],bd=1,relief=_Y,padx=8,pady=4);row.pack(fill=_C,pady=2,padx=4);v_info=verify_state[A].get(it[B]);is_bad=bool(v_info and v_info.get(_q)==_h);is_keep=it[C]!='DELETE';is_pin=it[C]=='KEEP'
				if is_bad:st_c,st_t=p[_V],'БИТИЙ!'
				else:st_c=p[_Q]if is_pin else p[_U]if is_keep else p[_V];st_t='ЗАХИЩЕНО'if is_pin else'ЗБЕРЕГТИ'if is_keep else'ВИДАЛИТИ'
				row.columnconfigure(1,weight=1);tk.Label(row,text=tr(st_t,lng_r),width=10,bg=p[_A],fg=st_c,font=(fam,max(8,fs-1),_I)).grid(row=0,column=0,sticky=_L);sz_m=round(it[_r]/1048576.,1);det_s=f" — {tr(v_info.get(_AH,''),lng_r)}"if is_bad else'';disp_n=it[B]if len(it[B])<=46 else it[B][:43]+'...';tk.Label(row,text=tr(f"{disp_n}  ({sz_m} МБ){det_s}",lng_r),anchor=_L,bg=p[_A],fg=p[_V]if is_bad else p[_D],font=(fam,max(8,fs-1))).grid(row=0,column=1,sticky='ew',padx=6)
				def _ask_del_arc(n=it[B]):lng_d=self.engine.state.get(_F,_E);t_c='Видалення архіву'if lng_d==_B else'Delete Archive';q_c=f"Видалити архів та .sha256?\n\n{n}"if lng_d==_B else f"Delete archive and .sha256?\n\n{n}";cdlg,cp,_=self._make_dialog(t_c,500,210);cbf=tk.Frame(cdlg,bg=cp[_G]);cbf.pack(side=_Z,fill=_C,padx=14,pady=10);tk.Label(cdlg,text=q_c,bg=cp[_G],fg=cp[_D],wraplength=450,font=(fam,fs)).pack(pady=(16,8),padx=16,expand=_H);tk.Button(cbf,text=tr(_A6,lng_d),command=cdlg.destroy,bg=cp[_A],fg=cp[_D],font=(fam,fs),padx=12,pady=4).pack(side=_K,padx=6);tk.Button(cbf,text=tr('Видалити',lng_d),command=lambda:(cdlg.destroy(),_delete_archive_pair(n),_refresh()),bg=cp[_V],fg=_l,font=(fam,fs,_I),padx=12,pady=4).pack(side=_K,padx=6);self._fit_dialog(cdlg)
				tk.Button(row,text=tr('🔒 Захист'if is_pin else'Немає захисту',lng_r),width=15,command=lambda n=it[B]:(toggle_keep_tag(self.engine.state,n),_refresh()),bg=p[_y]if is_pin else p[_G],fg=p[I]if is_pin else p[_O],activebackground=p[_P],activeforeground=p[_D],font=(fam,max(8,fs-1),_I if is_pin else _A2),padx=8,pady=1,cursor=_R).grid(row=0,column=2,sticky=_i);tk.Button(row,text='✖',width=3,command=_ask_del_arc,bg=p[_V]if is_bad else p[_G],fg=p[I]if is_bad else p[_V],activebackground=p[_V],activeforeground=_l,font=(fam,max(8,fs-1),_I),padx=4,pady=1,cursor=_R).grid(row=0,column=3,sticky=_i,padx=(6,0))
		def _clean():apply_gfs_cleanup(self.engine,skip_prompt=_H);_refresh()
		def _clean_corrupted():
			bdir=self.engine.state.get(_p,'');bad_names=[fn for(fn,st_i)in list(verify_state[A].items())if st_i.get(_q)==_h and os.path.exists(os.path.join(bdir,fn))]
			for fn in bad_names:_delete_archive_pair(fn)
			if bad_names:lbl_ver.configure(text=tr(f"✓ Видалено пошкоджених архівів: {len(bad_names)} шт.",self.engine.state.get(_F,_E)),fg=p[_U])
			_refresh()
		btn_verify=tk.Button(bf,text=M,command=_verify,bg=p[_A],fg=p[_Q],font=(fam,fs,_I),padx=bpx,pady=bpy,cursor=_R);btn_verify.pack(side=_J,padx=(0,6));tk.Label(bf,text='Буфер:',bg=p[_G],fg=p[_O],font=(fam,fs)).pack(side=_J,padx=(4,4));cb_buf=ttk.Combobox(bf,textvariable=v_buf,values=list(buf_options.keys()),width=7,state=_e,font=(fam,fs));cb_buf.pack(side=_J,padx=(0,8));btn_del_bad=tk.Button(bf,text=L,command=_clean_corrupted,state=F,bg=p[_A],fg=p[_O],font=(fam,fs,_I),padx=bpx,pady=bpy,cursor=_R);btn_del_bad.pack(side=_J,padx=4);btn_clean_exp=tk.Button(bf,text='Очистити застарілі зараз',command=_clean,bg=p[_b],fg=p[I],disabledforeground=p[_O],font=(fam,fs,_I),padx=bpx,pady=bpy,cursor=_R);btn_clean_exp.pack(side=_J,padx=4);tk.Button(bf,text=_w,command=dlg.destroy,bg=p[_A],fg=p[_D],font=(fam,fs),padx=bpx,pady=bpy,cursor=_R).pack(side=_K);_refresh();apply_widget_i18n(dlg,self.engine.state.get(_F,_E));self._fit_dialog(dlg)
	def open_cloud_stats_modal(self):
		fs, k, lang, fam = self.metrics[_k], self.metrics[_a], self.engine.state.get(_F, _E), self._ui_fam()
		_rw, _rh = max(680, self.root.winfo_width()), max(480, self.root.winfo_height())
		dlg, p, _ = self._make_dialog('⚡ Статистика швидкості роботи' if lang == _B else '⚡ Work Speed Statistics', int((_rw - 16) / max(.5, k)), min(640, int((_rh - 24) / max(.5, k))))
		dlg.maxsize(_rw, _rh)
		from gui.stats_view import show_three_tab_stats
		try:
			show_three_tab_stats(dlg, self.root, self.engine, p, k, fs, fam, lang, _w, _p)
		except Exception as _sex:
			tk.Label(dlg,text=str(_sex),bg=p[_G],fg=p[_V],wraplength=500).pack(pady=20)
		dlg.update_idletasks();dlg.lift()
	def open_stats_modal(self):
		F='dur_cnt';E='total_dur_sec';D='avg_dur_sec';C='month_cnt';B='week_cnt';A='today_cnt';fs=self.metrics[_k];lng_c=self.engine.state.get(_F,_E);dlg,p,_=self._make_dialog('Статистика резервного копіювання',820,690);st=self.engine.get_detailed_stats()if hasattr(self.engine,'get_detailed_stats')else{};tk.Button(dlg,text=tr(_w,lng_c),command=dlg.destroy,bg=p[_A],fg=p[_D],font=(self._ui_fam(),fs,_I),padx=int(24*self.metrics[_a]),pady=int(6*self.metrics[_a])).pack(side=_Z,anchor=_i,padx=16,pady=(6,12));tk.Label(dlg,text=tr('Зведена аналітика за періодами та станом локального сховища:',lng_c),bg=p[_G],fg=p[_O],font=(self._ui_fam(),fs)).pack(anchor=_L,padx=14,pady=(10,6));grid_f=tk.Frame(dlg,bg=p[_G]);grid_f.pack(fill=_C,padx=14,pady=4)
		for c_i in range(4):grid_f.columnconfigure(c_i,weight=1)
		tot_c=st.get('total_cnt',0);disk_c=st.get('disk_cnt',tot_c);sha_c=st.get('sha_cnt',0);sha_pct=int(round(sha_c/disk_c*100))if disk_c>0 else 100;sha_col=p[_U]if disk_c==0 or sha_c==disk_c else p[_b];lng_c=self.engine.state.get(_F,_E);span_d=st.get('span_days',0);depth_val=tr('1 день',lng_c)if span_d==1 else tr(f"{span_d} дн.",lng_c);sha_sub=tr('натисніть для списку',lng_c)if sha_c<disk_c else tr('усі захищені',lng_c)if disk_c>0 else tr('папка порожня',lng_c);cards=[(tr('СЬОГОДНІ',lng_c),tr(f"{st.get(A,0)} шт.",lng_c),tr(f"{st.get('today_mb',_T)} МБ",lng_c),p[_O]if st.get(A,0)==0 else p[_Q],_M),(tr('ЗА ТИЖДЕНЬ',lng_c),tr(f"{st.get(B,0)} шт.",lng_c),tr(f"{st.get('week_mb',_T)} МБ",lng_c),p[_O]if st.get(B,0)==0 else p[_Q],_M),(tr('ЗА МІСЯЦЬ',lng_c),tr(f"{st.get(C,0)} шт.",lng_c),tr(f"{st.get('month_mb',_T)} МБ",lng_c),p[_O]if st.get(C,0)==0 else p[_Q],_M),(tr('ЗА ВЕСЬ ЧАС',lng_c),tr(f"{tot_c} шт.",lng_c),tr(f"{st.get('total_mb',_T)} МБ",lng_c),p[_O]if tot_c==0 else p[_Q],_M),(tr('СЕР. РОЗМІР',lng_c),tr(f"{st.get('avg_mb',_T)} МБ",lng_c),tr('на один архів',lng_c),p[_D],_M),(tr('ЗАХИСТ SHA-256',lng_c),f"{sha_c} / {disk_c} ({sha_pct}%)",sha_sub,sha_col,_m),(tr('УСПІШНІСТЬ',lng_c),f"{st.get('success_rate',100)}%",tr('останніх запусків',lng_c),p[_D],_M),(tr('ГЛИБИНА',lng_c),depth_val,tr('діапазон копій',lng_c),p[_D],_M)]
		def _show_missing_sha():
			bdir=self.engine.state.get(_p,'');miss=[f for f in os.listdir(bdir)if f.lower().endswith('.zip')and not os.path.exists(os.path.join(bdir,f+_A4))]if os.path.isdir(bdir)else[]
			if not miss:dlg.destroy();self.open_analyze();return
			miss.sort(reverse=_H);shown=miss[:12];msg_m=tr('Архіви без файлу .sha256:',lng_c)+'\n\n• '+'\n• '.join(shown)
			if len(miss)>len(shown):msg_m+='\n'+(f"… та ще {len(miss)-len(shown)} шт."if lng_c==_B else f"… and {len(miss)-len(shown)} more")
			self._show_engine_modal({_j:_AN,_AD:tr('Перевірка захисту SHA-256',lng_c),_D:msg_m})
		for(idx,(cap,v_main,v_sub,col,act))in enumerate(cards):
			r_i,c_i=divmod(idx,4);is_warn_sha=act==_m and sha_c<disk_c;c=tk.Frame(grid_f,bg=p[_A],bd=2 if is_warn_sha else 1,relief=_Y,highlightbackground=p[_b]if is_warn_sha else p[_P],highlightthickness=2 if is_warn_sha else 0,padx=8,pady=4,cursor=_R if act else'');c.grid(row=r_i,column=c_i,sticky='nsew',padx=(0 if c_i==0 else 6,0),pady=(0 if r_i==0 else 6,0));w1=tk.Label(c,text=cap,bg=p[_A],fg=p[_O],font=(_N,max(7,fs-3),_I));w2=tk.Label(c,text=v_main,bg=p[_A],fg=col,font=(_N,fs+1,_I));w3=tk.Label(c,text=v_sub,bg=p[_A],fg=p[_O],font=(_N,max(7,fs-2)))
			for w_it in(w1,w2,w3):
				w_it.pack(anchor=_L)
				if act==_m:w_it.bind(_AO,lambda _e:_show_missing_sha())
			if act==_m:c.bind(_AO,lambda _e:_show_missing_sha())
		lng_s=self.engine.state.get(_F,_E);avg_t_s=format_duration(st.get(D,_T),lng_s)if float(st.get(D)or 0)>0 else _X;tot_t_s=format_duration(st.get(E,_T),lng_s)if float(st.get(E)or 0)>0 else _X;mid_f=tk.Frame(dlg,bg=p[_A],bd=1,relief=_Y,padx=12,pady=8);mid_f.pack(fill=_C,padx=14,pady=(6,6));wt_txt=f"Час роботи:   Середній: {avg_t_s}   •   Загальний ({st.get(F,0)} оп.): {tot_t_s}"if lng_s==_B else f"Work time:   Average: {avg_t_s}   •   Total ({st.get(F,0)} runs): {tot_t_s}";tk.Label(mid_f,text=wt_txt,bg=p[_A],fg=p[_Q],font=(_N,fs,_I)).pack(anchor=_L);chart_card=tk.Frame(dlg,bg=p[_A],bd=1,relief=_Y,padx=12,pady=8);chart_card.pack(fill=_W,expand=_H,padx=14,pady=(4,6));tk.Label(chart_card,text=tr('ДИНАМІКА СТВОРЕННЯ АРХІВІВ ЗА ОСТАННІ 6 МІСЯЦІВ',lng_c),bg=p[_A],fg=p[_O],font=(self._ui_fam(),max(7,fs-3),_I)).pack(anchor=_L,pady=(0,6));cv=tk.Canvas(chart_card,height=int(225*self.metrics[_a]),bg=p[_f],highlightthickness=1,highlightbackground=p[_P]);cv.pack(fill=_W,expand=_H);months=st.get('months',[])
		def _draw_chart(_e=_M):
			cv.delete(_A0);w,h=max(300,cv.winfo_width()),max(180,cv.winfo_height())
			if not months:return
			max_v=max([v for(_,v)in months]+[1]);k=self.metrics[_a];pad_x,top_y,bot_y=int(42*k),int(34*k),h-int(42*k)
			for g_i in range(1,5):gy=bot_y-int((bot_y-top_y)*g_i/4);cv.create_line(pad_x-8,gy,w-pad_x+12,gy,fill=p[_P],dash=(2,4))
			slot_w=(w-pad_x*2)/len(months);bar_w=min(56,max(24,slot_w*.48));dx,dy=int(9*k),int(7*k);cv.create_line(pad_x-8,bot_y,w-pad_x+12,bot_y,fill=p[_P],width=2)
			for(i,(m_lbl,val))in enumerate(months):
				cx=pad_x+slot_w*(i+.5);x1,x2=cx-bar_w/2,cx+bar_w/2
				if val>0:bh=max(int(12*k),int((bot_y-top_y)*val/max_v));y1=bot_y-bh;cv.create_polygon(x2,bot_y,x2+dx+5,bot_y-dy+3,x2+dx+5,y1-dy+5,x2,y1+3,fill='#05080f',outline='');cv.create_polygon(x2,y1,x2+dx,y1-dy,x2+dx,bot_y-dy,x2,bot_y,fill='#0d7a53',outline='');cv.create_polygon(x1,y1,x1+dx,y1-dy,x2+dx,y1-dy,x2,y1,fill='#34d399',outline='');cv.create_rectangle(x1,y1,x2,bot_y,fill=p[_U],outline='');cv.create_line(x1+1,y1+1,x2-1,y1+1,fill='#a7f3d0');cv.create_text(cx+dx//2,y1-dy-int(11*k),text=str(val),fill=p[_D],font=(self._ui_fam(),fs,_I))
				else:cv.create_polygon(x1,bot_y-3,x1+dx,bot_y-3-dy,x2+dx,bot_y-3-dy,x2,bot_y-3,fill=p[_P],outline='')
				cv.create_text(cx,bot_y+int(16*k),text=tr(m_lbl,lng_c),fill=p[_O],font=(self._ui_fam(),max(8,fs-1),_I if val>0 else _A2))
		cv.bind(_d,_draw_chart);dlg.after(40,_draw_chart);apply_widget_i18n(dlg,self.engine.state.get(_F,_E));self._fit_dialog(dlg)
	def open_ops_history(self):
		Q='interval';P='item';O='tone_warning';N='tone_error';M='stripe_odd';L='stripe_even';K='date';J='HGB.Treeview.Heading';I='selected';H='duration';G='file_type';F='cloud';E='HGB.Treeview';D='cloud_tooltip';C='sha_tooltip';B='full_name';A='window';fs=self.metrics[_k];lang=self.engine.state.get(_F,_E);dlg,p,_=self._make_dialog('Журнал останніх операцій архівування',1000,600)
		if isinstance(dlg,_EmbeddedDialog):
			def _resize_embedded_history(_event=_M):
				if not dlg.winfo_exists():return
				width=min(int(1000*self.metrics[_a]),max(360,self.root.winfo_width()-24));height=min(int(600*self.metrics[_a]),max(160,self.root.winfo_height()-24));dlg.place_configure(width=width,height=height)
			resize_binding=self.root.bind(_d,_resize_embedded_history,add='+');dlg.bind(_AP,lambda event:self.root.unbind(_d,resize_binding)if event.widget is dlg else _M);_resize_embedded_history()
		else:dlg.resizable(_H,_H);dlg._fit_flag=_H;dlg.minsize(min(760,max(360,self.metrics[_t]-24)),min(440,max(160,self.metrics[_u]-48)))
		hdr_txt='Останні 25 операцій створення резервних копій (подвійний клік по рядку — деталі):'if lang==_B else'Last 25 backup operations (double-click a row for details):';tk.Label(dlg,text=hdr_txt,bg=p[_G],fg=p[_O],font=(_N,fs)).pack(anchor=_L,padx=14,pady=(10,6));bf=tk.Frame(dlg,bg=p[_G]);bf.pack(side=_Z,fill=_C,padx=14,pady=(6,12));wrap=tk.Frame(dlg,bg=p[_G]);wrap.pack(fill=_W,expand=_H,padx=14,pady=(0,4));style=ttk.Style()
		try:style.theme_use('clam')
		except Exception:0
		style.map(E,background=[(I,p[_y])],foreground=[(I,_l)]);style.map(J,background=[('active',p[_G])]);style.configure(E,background=p[_f],foreground=p[_D],fieldbackground=p[_f],rowheight=max(26,int((fs+16)*self.metrics[_a])),font=(_N,max(8,fs-1)));style.configure(J,background=p[_A],foreground=p[_Q],font=(_N,max(8,fs-1),_I));cols=K,_q,_j,_AA,_r,'dur',_m,F;tree=ttk.Treeview(wrap,columns=cols,show='headings',style=E);heads=[(K,'Дата'if lang==_B else'Date',142,106,_g),(_q,'Статус'if lang==_B else'Status',86,66,_g),(_j,'Тип'if lang==_B else'Type',72,58,_g),(_AA,'Файл'if lang==_B else'File',300,130,_L),(_r,'Розмір'if lang==_B else'Size',78,60,_i),('dur','Час'if lang==_B else'Duration',88,70,_g),(_m,'SHA',56,48,_g)]
		for(cid,title_h,w_col,min_w_col,anc)in heads:tree.heading(cid,text=title_h);tree.column(cid,width=int(w_col*self.metrics[_a]),minwidth=int(min_w_col*self.metrics[_a]),anchor=anc,stretch=cid==_AA)
		vsb=ttk.Scrollbar(wrap,orient=_z,command=tree.yview);hsb=ttk.Scrollbar(wrap,orient='horizontal',command=tree.xview);tree.configure(yscrollcommand=vsb.set,xscrollcommand=hsb.set);vsb.pack(side=_K,fill=_o);tree.pack(side='top',fill=_W,expand=_H);hsb.pack(side=_Z,fill=_C);tree.tag_configure(L,background=p[_f]);tree.tag_configure(M,background=p[_A]);tree.tag_configure(N,foreground=p[_V]);tree.tag_configure(O,foreground=p[_b]);row_items={}
		def _populate():
			T='Cloud status is unknown.';S='Статус хмари невідомий.';R='uploaded';K='unknown';J='verified';I='present';F='queued';E='absent';A='error'
			for rid in tree.get_children():tree.delete(rid)
			row_items.clear();bdir=self.engine.state.get(_p,'');ops=getattr(self.engine,_AG,[])or[];from core.cloud import cloud_archive_sync_status
			for(idx_o,item)in enumerate(ops):
				st_lbl=item.get(_q,'');detail=str(item.get(_AH,''));full_name=_operation_archive_name(detail);file_type,short_name=_operation_archive_display(full_name);file_label=short_name or detail;dur_v=item.get('dur_sec',_M)
				if dur_v is not _M:
					try:dur_txt=format_duration(float(dur_v),lang)
					except(TypeError,ValueError,OverflowError):dur_txt=_X
				else:duration_match=re.search('\\(([^()]*)\\)\\s*$',detail);dur_txt=duration_match.group(1).strip()if duration_match else _X
				archive_path=os.path.join(bdir,full_name)if bdir and full_name else'';sha_path=archive_path+_A4 if archive_path else'';has_sidecar=bool(sha_path and os.path.isfile(sha_path));sha_status=E;sha_tooltip='Контрольної суми немає.'if lang==_B else'Checksum is absent.'
				if has_sidecar:
					sha_status=I;sha_tooltip='Файл контрольної суми є; відповідність ще не перевірялась.'if lang==_B else'Checksum file exists; it has not been verified against the archive.'
					try:archive_mtime=os.path.getmtime(archive_path)
					except OSError:archive_mtime=_M
					if archive_mtime is not _M and item.get(_AT)==archive_mtime:
						if item.get(_AM)==_h:sha_status=A;sha_tooltip=item.get(_AS)or('Контрольна сума не збігається.'if lang==_B else'Checksum does not match.')
						elif item.get(_AM)=='ok':sha_status=J;sha_tooltip='Контрольна сума збігається.'if lang==_B else'Checksum matches.'
				sha_mark={E:_X,I:'✔',J:'✔',A:'✖'}[sha_status]
				try:cloud_status=cloud_archive_sync_status(self.engine,full_name)if full_name else K;cloud_tooltip={R:'Завантажено до хмари.'if lang==_B else'Uploaded to cloud.',F:'Очікує синхронізації.'if lang==_B else'Waiting in sync queue.',A:'Помилка синхронізації.'if lang==_B else'Cloud sync failed.',K:S if lang==_B else T}.get(cloud_status,S if lang==_B else T)
				except(OSError,ValueError,TypeError)as exc:cloud_status=A;cloud_tooltip=f"Помилка читання статусу хмари: {exc}"if lang==_B else f"Could not read cloud status: {exc}"
				cloud_mark={R:'☁✔',F:'⏳',A:'✖'}.get(cloud_status,_X);is_success=st_lbl=='Успішно';mb_txt=f"{item.get('size_mb',0)} {'МБ'if lang==_B else'MB'}"if is_success else _X;status_lower=st_lbl.lower()
				if any(word in status_lower for word in('помил',A,'failed'))or sha_status==A or cloud_status==A:tone=N
				elif any(word in status_lower for word in('поперед',_AE))or sha_status==E or cloud_status==F:tone=O
				else:tone=''
				iid=f"op_{idx_o}";row_items[iid]={P:item,B:full_name or detail,G:file_type,_r:mb_txt,H:dur_txt,_m:sha_mark,C:sha_tooltip,D:cloud_tooltip,Q:_operation_interval_text(item)};tags=[L if idx_o%2==0 else M]
				if tone:tags.append(tone)
				tree.insert('','end',iid=iid,values=(item.get(_x,''),tr(st_lbl,lang),file_type,file_label,mb_txt,dur_txt,sha_mark,cloud_mark),tags=tuple(tags))
		def _on_double_click(_ev=_M):
			sel=tree.selection()
			if not sel or sel[0]not in row_items:return
			row=row_items[sel[0]];item=row[P];st_tr=tr(item.get(_q,''),lang);interval,approximate=row[Q]
			if interval:interval_line=('Інтервал (приблизно): 'if approximate else'Інтервал: ')+interval if lang==_B else('Interval (approx.): 'if approximate else'Interval: ')+interval
			else:interval_line=''
			details_lines=[f"Дата та час: {item.get(_x,'')}"if lang==_B else f"Date & Time: {item.get(_x,'')}",f"Статус: {st_tr}"if lang==_B else f"Status: {st_tr}",f"Тип: {row[G]or _X}"if lang==_B else f"Type: {row[G]or _X}",f"Розмір: {row[_r]}"if lang==_B else f"Size: {row[_r]}",f"Тривалість: {row[H]}"if lang==_B else f"Duration: {row[H]}",f"SHA-256: {row[_m]} — {row[C]}"if lang==_B else f"SHA-256: {row[_m]} — {row[C]}",f"Хмара: {row[F]} — {row[D]}"if lang==_B else f"Cloud: {row[F]} — {row[D]}"]
			if interval_line:details_lines.append(interval_line)
			if lang==_B:info_msg='\n'.join(details_lines)+f"\n\nПовне ім'я файлу:\n{row[B]}";t_dlg='Деталі операції'
			else:info_msg='\n'.join(details_lines)+f"\n\nFull file name:\n{row[B]}";t_dlg='Operation Details'
			self._show_engine_modal({_j:_AN,_AD:t_dlg,_D:info_msg})
		tree.bind(_AU,_on_double_click);tooltip_state={A:_M,_D:''}
		def _hide_history_tooltip(_event=_M):
			window=tooltip_state[A];tooltip_state[A]=_M;tooltip_state[_D]=''
			if window is not _M:window.destroy()
		def _show_history_tooltip(event):
			row_id=tree.identify_row(event.y);column_id=tree.identify_column(event.x);row=row_items.get(row_id)
			if not row:_hide_history_tooltip();return
			tooltip_text={'#4':row[B],'#7':row[C],'#8':row[D]}.get(column_id)
			if not tooltip_text:_hide_history_tooltip();return
			if tooltip_text==tooltip_state[_D]and tooltip_state[A]is not _M:return
			_hide_history_tooltip();tip=tk.Toplevel(self.root);tip.wm_overrideredirect(_H);tk.Label(tip,text=tooltip_text,bg=p[_A],fg=p[_D],bd=1,relief=_Y,justify=_J,wraplength=560,font=(_N,max(8,fs-1)),padx=6,pady=4).pack();tip.update_idletasks();x=min(event.x_root+12,max(4,self.metrics[_t]-tip.winfo_reqwidth()-6));y=min(event.y_root+16,max(4,self.metrics[_u]-tip.winfo_reqheight()-6));tip.geometry(f"+{x}+{y}");tooltip_state.update({A:tip,_D:tooltip_text})
		tree.bind('<Motion>',_show_history_tooltip);tree.bind('<Leave>',_hide_history_tooltip);tree.bind('<ButtonPress-1>',_hide_history_tooltip);_populate()
		def _clear_ops():
			from tkinter import messagebox;title='Очистити журнал?'if lang==_B else'Clear history?';prompt='Видалити всі записи журналу операцій?'if lang==_B else'Delete all operation history entries?'
			if not messagebox.askyesno(title,prompt,parent=self.root):return
			self.engine.op_history=[];self.engine.state[_AG]=[];commit_state(self.engine.state);_populate()
		tk.Button(bf,text='🗑 Очистити журнал'if lang==_B else'🗑 Clear History',command=_clear_ops,bg=p[_A],fg=p[_V],font=(_N,fs),padx=12,pady=5,cursor=_R).pack(side=_J);tk.Button(bf,text=tr(_w,lang),command=dlg.destroy,bg=p[_A],fg=p[_D],font=(_N,fs),padx=14,pady=5,cursor=_R).pack(side=_K)
	def open_about(self):
		A='https://github.com';import webbrowser;from core.config import BUILD_DATE;fs=self.metrics[_k];k=self.metrics[_a];lang=self.engine.state.get(_F,_E);fam=_A9 if self.engine.state.get(_A8,_S)else self._get_palette().get('font',_N);dlg,p,_=self._make_dialog(f"{tr('Про програму',lang)} — HomeGrid Backup v{SCRIPT_VER}",560,320)
		if lang==_B:info=f"HomeGrid Backup  •  Версія v{SCRIPT_VER} (збірка від {BUILD_DATE})\n\n• Нативне резервне копіювання даних та налаштувань інвертора без браузера.\n• Перевірка цілісності архівів за CRC32 + SHA-256 та дзеркалювання.\n• Автоматична GFS-ротація копій та запуск за розкладом.";repo_lbl='Репозиторій проєкту:'
		else:info=f"HomeGrid Backup  •  Version v{SCRIPT_VER} (build {BUILD_DATE})\n\n• Native backup of inverter data and settings without a browser.\n• Archive integrity verification via CRC32 + SHA-256 and mirroring.\n• Automatic GFS backup rotation and scheduled execution.";repo_lbl='Project repository:'
		tk.Label(dlg,text=info,bg=p[_G],fg=p[_D],justify=_J,wraplength=int(510*k),font=(fam,fs)).pack(padx=18,pady=(16,8),anchor=_L,fill=_C);rf=tk.Frame(dlg,bg=p[_G]);rf.pack(fill=_C,padx=18,pady=(0,8));tk.Label(rf,text=repo_lbl,bg=p[_G],fg=p[_O],font=(fam,fs)).pack(side=_J);lnk=tk.Label(rf,text=A,bg=p[_G],fg=p[_Q],font=(fam,fs,'underline'),cursor=_R);lnk.pack(side=_J,padx=(6,0));lnk.bind(_AO,lambda _e:webbrowser.open(A));dlg.bind(_AJ,lambda _e:dlg.destroy());dlg.bind(_A7,lambda _e:dlg.destroy());tk.Button(dlg,text=tr(_w,lang),command=dlg.destroy,bg=p[_U],fg=p[_v],font=(fam,fs,_I),padx=int(22*k),pady=int(7*k),cursor=_R).pack(side=_Z,anchor=_i,padx=18,pady=14);self._fit_dialog(dlg)
