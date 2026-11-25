# [ФАЙЛ: mobile/android_app.py (v2.00 | 21.11.2026 03:24) — МОБИЛЬНЫЙ ИНТЕРФЕЙС ANDROID (KIVY)]
_G='vertical'
_F='server'
_E='middle'
_D='text_size'
_C=False
_B=True
_A=None
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from core.backup import run_backup_task,verify_all_archives
from core.config import BUILD_DATE,SCRIPT_VER,commit_state
from core.i18n import tr
from core.network import normalize_server_url,run_connect_task,run_scan_task
Window.clearcolor=.04,.06,.1,1
class HomeGridAndroidApp(App):
	def __init__(A,engine,**B):super().__init__(**B);A.engine=engine;A.last_log_len=0;A.last_modal_id=_A;A.active_popup=_A
	def _tr(A,text):return tr(text,A.engine.state.get('lang','en'))
	def build(A):C='left';A.title=f"HomeGrid Backup v{SCRIPT_VER}";B=BoxLayout(orientation=_G,padding=14,spacing=10);D=Label(text=A._tr(f"[b]HomeGrid Backup v{SCRIPT_VER}[/b]\n[size=13sp][color=#94a3b8]Оновлено: {BUILD_DATE}[/color][/size]"),markup=_B,size_hint_y=_A,height=58,halign=C,valign=_E);D.bind(size=D.setter(_D));B.add_widget(D);A.inp_srv=TextInput(text=A.engine.state.get(_F,''),hint_text=A._tr('Адреса сервера (напр. 192.168.1.246)'),multiline=_C,size_hint_y=_A,height=48,background_color=(.08,.12,.2,1),foreground_color=(1,1,1,1));B.add_widget(A.inp_srv);E=BoxLayout(size_hint_y=_A,height=48,spacing=8);G=Button(text=A._tr('Підключити'),background_color=(.17,.5,1.,1),bold=_B);G.bind(on_release=A.on_connect);H=Button(text=A._tr('Пошук по LAN'),background_color=(.12,.18,.3,1),bold=_B);H.bind(on_release=A.on_scan);E.add_widget(G);E.add_widget(H);B.add_widget(E);A.lbl_disk=Label(text=A._tr('Сховище: завантаження...'),size_hint_y=_A,height=30,color=(.06,.73,.51,1),halign=C,valign=_E);A.lbl_disk.bind(size=A.lbl_disk.setter(_D));B.add_widget(A.lbl_disk);A.lbl_stage=Label(text=A._tr(A.engine.stage),size_hint_y=_A,height=34,halign=C,valign=_E,bold=_B);A.lbl_stage.bind(size=A.lbl_stage.setter(_D));B.add_widget(A.lbl_stage);A.pbar=ProgressBar(max=100,value=0,size_hint_y=_A,height=22);B.add_widget(A.pbar);I=ScrollView(size_hint=(1,1));A.lbl_log=Label(text='',size_hint_y=_A,halign=C,valign='top',font_size='13sp',color=(.88,.92,.96,1));A.lbl_log.bind(texture_size=lambda inst,val:setattr(inst,'height',max(val[1],100)));A.lbl_log.bind(width=lambda inst,val:setattr(inst,_D,(val-12,_A)));I.add_widget(A.lbl_log);B.add_widget(I);F=BoxLayout(size_hint_y=_A,height=54,spacing=8);A.btn_start=Button(text=A._tr('ЗАПУСТИТИ БЕКАП'),background_color=(.06,.73,.51,1),bold=_B);A.btn_start.bind(on_release=A.on_backup);J=Button(text=A._tr('Перевірити SHA-256'),background_color=(.15,.22,.35,1));J.bind(on_release=A.on_verify);F.add_widget(A.btn_start);F.add_widget(J);B.add_widget(F);Clock.schedule_interval(A._poll_state,.35);return B
	def _sync_url(A):
		C=A.inp_srv.text.strip()
		if C:
			B,D=normalize_server_url(C)
			if B:A.inp_srv.text=f"{B}!"if D else B;A.engine.state[_F]=B;commit_state(A.engine.state)
	def on_connect(A,*B):
		if not A.engine.is_running:A._sync_url();threading.Thread(target=run_connect_task,args=(A.engine,A.inp_srv.text,_C),daemon=_B).start()
	def on_scan(A,*B):
		if not A.engine.is_running:threading.Thread(target=run_scan_task,args=(A.engine,),daemon=_B).start()
	def on_backup(A,*B):
		if not A.engine.is_running:A._sync_url();threading.Thread(target=run_backup_task,args=(A.engine,A.inp_srv.text,_C,_C,_C),daemon=_B).start()
	def on_verify(A,*C):
		if A.engine.is_running:return
		def B():C='err_cnt';A.engine.log('Запуск перевірки цілісності CRC32 + SHA-256...','info');B=verify_all_archives(A.engine.state);A.engine.log(f"Перевірку завершено: справних {B['ok_cnt']}, без .sha256: {B['warn_cnt']}, пошкоджених: {B[C]}",'ok'if B[C]==0 else'err')
		threading.Thread(target=B,daemon=_B).start()
	def _open_modal(A,m):
		K='type'
		if A.active_popup:
			try:A.active_popup.dismiss()
			except Exception:0
		C=BoxLayout(orientation=_G,padding=12,spacing=10);F=Label(text=A._tr(m['text']),halign='center',valign=_E);F.bind(size=F.setter(_D));C.add_widget(F)
		def D(val):
			if A.active_popup:A.active_popup.dismiss();A.active_popup=_A
			A.engine.submit_modal(val)
		if m[K]=='pin':G=TextInput(password=_B,multiline=_C,size_hint_y=_A,height=44,input_filter='int');C.add_widget(G);B=BoxLayout(size_hint_y=_A,height=44,spacing=8);H=Button(text=A._tr('Скасувати'));H.bind(on_release=lambda*A:D(''));E=Button(text=A._tr('Підтвердити'),background_color=(.06,.73,.51,1));E.bind(on_release=lambda*A:D(G.text.strip()));B.add_widget(H);B.add_widget(E);C.add_widget(B)
		elif m[K]=='confirm':B=BoxLayout(size_hint_y=_A,height=44,spacing=8);I=Button(text=A._tr('Ні'));I.bind(on_release=lambda*A:D(_C));J=Button(text=A._tr('Так'),background_color=(.95,.62,.05,1));J.bind(on_release=lambda*A:D(_B));B.add_widget(I);B.add_widget(J);C.add_widget(B)
		else:E=Button(text=A._tr('ОК'),size_hint_y=_A,height=44,background_color=(.06,.73,.51,1));E.bind(on_release=lambda*A:D(_B));C.add_widget(E)
		A.active_popup=Popup(title=A._tr(m['title']),content=C,size_hint=(.9,.45),auto_dismiss=_C);A.active_popup.open()
	def _poll_state(A,_dt):
		B=(A.engine.state.get(_F)or'').strip()
		if B and not A.inp_srv.focus and A.inp_srv.text!=B:A.inp_srv.text=B
		E,F,D=A.engine.get_storage_stats();G=f" | Вільно: {D} ГБ"if D>=0 else'';A.lbl_disk.text=A._tr(f"Архівів: {E} шт. ({F} МБ){G}");A.lbl_stage.text=A._tr(f"{A.engine.stage} ({A.engine.progress}%)");A.pbar.value=A.engine.progress;A.btn_start.disabled=A.engine.is_running;C=A.engine.logs
		if len(C)!=A.last_log_len:A.last_log_len=len(C);A.lbl_log.text='\n'.join(f"[{A['ts']}] {A['msg']}"for A in C[-60:])
		if A.engine.modal and A.engine.modal.get('id')!=A.last_modal_id:A.last_modal_id=A.engine.modal['id'];A._open_modal(A.engine.modal)
def run_android_ui(engine):HomeGridAndroidApp(engine).run()
