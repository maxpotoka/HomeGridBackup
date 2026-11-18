# ==============================================================================
# [ФАЙЛ: mobile/android_app.py (v1.008 | 18.11.2026 17:51) — МОБИЛЬНЫЙ ИНТЕРФЕЙС ANDROID (KIVY)]
# ==============================================================================
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

from core.config import SCRIPT_VER, BUILD_DATE, commit_state
from core.network import normalize_server_url, run_connect_task, run_scan_task
from core.backup import run_backup_task, verify_all_archives

Window.clearcolor = (0.04, 0.06, 0.10, 1)


class HomeGridAndroidApp(App):
    def __init__(self, engine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self.last_log_len = 0
        self.last_modal_id = None
        self.active_popup = None

    def build(self):
        self.title = f"HomeGrid Backup v{SCRIPT_VER}"
        root = BoxLayout(orientation="vertical", padding=14, spacing=10)

        lbl_hdr = Label(
            text=f"[b]HomeGrid Backup v{SCRIPT_VER}[/b]\n[size=13sp][color=#94a3b8]Оновлено: {BUILD_DATE}[/color][/size]",
            markup=True, size_hint_y=None, height=58, halign="left", valign="middle"
        )
        lbl_hdr.bind(size=lbl_hdr.setter("text_size"))
        root.add_widget(lbl_hdr)

        self.inp_srv = TextInput(
            text=self.engine.state.get("server", ""),
            hint_text="Адреса сервера (напр. 192.168.1.246)",
            multiline=False, size_hint_y=None, height=48,
            background_color=(0.08, 0.12, 0.20, 1), foreground_color=(1, 1, 1, 1)
        )
        root.add_widget(self.inp_srv)

        row_net = BoxLayout(size_hint_y=None, height=48, spacing=8)
        btn_conn = Button(text="Підключити", background_color=(0.17, 0.50, 1.0, 1), bold=True)
        btn_conn.bind(on_release=self.on_connect)
        btn_scan = Button(text="Пошук по LAN", background_color=(0.12, 0.18, 0.30, 1), bold=True)
        btn_scan.bind(on_release=self.on_scan)
        row_net.add_widget(btn_conn)
        row_net.add_widget(btn_scan)
        root.add_widget(row_net)

        self.lbl_disk = Label(
            text="Сховище: завантаження...", size_hint_y=None, height=30,
            color=(0.06, 0.73, 0.51, 1), halign="left", valign="middle"
        )
        self.lbl_disk.bind(size=self.lbl_disk.setter("text_size"))
        root.add_widget(self.lbl_disk)

        self.lbl_stage = Label(
            text=self.engine.stage, size_hint_y=None, height=34,
            halign="left", valign="middle", bold=True
        )
        self.lbl_stage.bind(size=self.lbl_stage.setter("text_size"))
        root.add_widget(self.lbl_stage)

        self.pbar = ProgressBar(max=100, value=0, size_hint_y=None, height=22)
        root.add_widget(self.pbar)

        scroll = ScrollView(size_hint=(1, 1))
        self.lbl_log = Label(
            text="", size_hint_y=None, halign="left", valign="top",
            font_size="13sp", color=(0.88, 0.92, 0.96, 1)
        )
        self.lbl_log.bind(texture_size=lambda inst, val: setattr(inst, "height", max(val[1], 100)))
        self.lbl_log.bind(width=lambda inst, val: setattr(inst, "text_size", (val - 12, None)))
        scroll.add_widget(self.lbl_log)
        root.add_widget(scroll)

        row_bot = BoxLayout(size_hint_y=None, height=54, spacing=8)
        self.btn_start = Button(text="ЗАПУСТИТИ БЕКАП", background_color=(0.06, 0.73, 0.51, 1), bold=True)
        self.btn_start.bind(on_release=self.on_backup)
        btn_ver = Button(text="Перевірити SHA-256", background_color=(0.15, 0.22, 0.35, 1))
        btn_ver.bind(on_release=self.on_verify)
        row_bot.add_widget(self.btn_start)
        row_bot.add_widget(btn_ver)
        root.add_widget(row_bot)

        Clock.schedule_interval(self._poll_state, 0.35)
        return root

    def _sync_url(self):
        raw = self.inp_srv.text.strip()
        if raw:
            norm, has_bang = normalize_server_url(raw)
            if norm:
                self.inp_srv.text = f"{norm}!" if has_bang else norm
                self.engine.state["server"] = norm
                commit_state(self.engine.state)

    def on_connect(self, *_):
        if not self.engine.is_running:
            self._sync_url()
            threading.Thread(target=run_connect_task, args=(self.engine, self.inp_srv.text, False), daemon=True).start()

    def on_scan(self, *_):
        if not self.engine.is_running:
            threading.Thread(target=run_scan_task, args=(self.engine,), daemon=True).start()

    def on_backup(self, *_):
        if not self.engine.is_running:
            self._sync_url()
            threading.Thread(target=run_backup_task, args=(self.engine, self.inp_srv.text, False, False, False), daemon=True).start()

    def on_verify(self, *_):
        if self.engine.is_running:
            return
        def _worker():
            self.engine.log("Запуск перевірки цілісності CRC32 + SHA-256...", "info")
            res = verify_all_archives(self.engine.state)
            self.engine.log(f"Перевірку завершено: справних {res['ok_cnt']}, без .sha256: {res['warn_cnt']}, пошкоджених: {res['err_cnt']}", "ok" if res["err_cnt"] == 0 else "err")
        threading.Thread(target=_worker, daemon=True).start()

    def _open_modal(self, m):
        if self.active_popup:
            try:
                self.active_popup.dismiss()
            except Exception:
                pass
        box = BoxLayout(orientation="vertical", padding=12, spacing=10)
        lbl = Label(text=m["text"], halign="center", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        box.add_widget(lbl)

        def _finish(val):
            if self.active_popup:
                self.active_popup.dismiss()
                self.active_popup = None
            self.engine.submit_modal(val)

        if m["type"] == "pin":
            inp = TextInput(password=True, multiline=False, size_hint_y=None, height=44, input_filter="int")
            box.add_widget(inp)
            btns = BoxLayout(size_hint_y=None, height=44, spacing=8)
            b_cancel = Button(text="Скасувати")
            b_cancel.bind(on_release=lambda *_: _finish(""))
            b_ok = Button(text="Підтвердити", background_color=(0.06, 0.73, 0.51, 1))
            b_ok.bind(on_release=lambda *_: _finish(inp.text.strip()))
            btns.add_widget(b_cancel)
            btns.add_widget(b_ok)
            box.add_widget(btns)
        elif m["type"] == "confirm":
            btns = BoxLayout(size_hint_y=None, height=44, spacing=8)
            b_no = Button(text="Ні")
            b_no.bind(on_release=lambda *_: _finish(False))
            b_yes = Button(text="Так", background_color=(0.95, 0.62, 0.05, 1))
            b_yes.bind(on_release=lambda *_: _finish(True))
            btns.add_widget(b_no)
            btns.add_widget(b_yes)
            box.add_widget(btns)
        else:
            b_ok = Button(text="ОК", size_hint_y=None, height=44, background_color=(0.06, 0.73, 0.51, 1))
            b_ok.bind(on_release=lambda *_: _finish(True))
            box.add_widget(b_ok)

        self.active_popup = Popup(title=m["title"], content=box, size_hint=(0.9, 0.45), auto_dismiss=False)
        self.active_popup.open()

    def _poll_state(self, _dt):
        srv_st = (self.engine.state.get("server") or "").strip()
        if srv_st and not self.inp_srv.focus and self.inp_srv.text != srv_st:
            self.inp_srv.text = srv_st

        z_cnt, z_mb, free_gb = self.engine.get_storage_stats()
        free_t = f" | Вільно: {free_gb} ГБ" if free_gb >= 0 else ""
        self.lbl_disk.text = f"Архівів: {z_cnt} шт. ({z_mb} МБ){free_t}"
        self.lbl_stage.text = f"{self.engine.stage} ({self.engine.progress}%)"
        self.pbar.value = self.engine.progress
        self.btn_start.disabled = self.engine.is_running

        logs = self.engine.logs
        if len(logs) != self.last_log_len:
            self.last_log_len = len(logs)
            self.lbl_log.text = "\n".join(f"[{x['ts']}] {x['msg']}" for x in logs[-60:])

        if self.engine.modal and self.engine.modal.get("id") != self.last_modal_id:
            self.last_modal_id = self.engine.modal["id"]
            self._open_modal(self.engine.modal)


def run_android_ui(engine):
    HomeGridAndroidApp(engine).run()
