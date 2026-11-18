# ==============================================================================
# [ФАЙЛ: gui/tray.py (v1.002 | 18.11.2026 17:14) — СИСТЕМНЫЙ ТРЕЙ WINDOWS (PYSTRAY) И СЛУШАТЕЛЬ ОКНА]
# ==============================================================================
import os
import time
import ctypes
import threading

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except Exception:
    pystray = None
    Image = None
    ImageDraw = None
    HAS_TRAY = False

def create_tray_image(pct=0, spin_idx=0):
    img = Image.new("RGBA", (64, 64), (11, 18, 32, 255))
    drw = ImageDraw.Draw(img)
    drw.ellipse([4, 4, 60, 60], outline=(43, 127, 255, 255), width=5)
    if pct > 0:
        end_ang = -90 + int(360 * min(100, pct) / 100.0)
        drw.arc([4, 4, 60, 60], start=-90, end=end_ang, fill=(16, 185, 129, 255), width=6)
    drw.text((14, 24), f"{int(pct)}%" if pct > 0 else "HGB", fill=(255, 255, 255, 255))
    return img

def _get_tray_img_safe(pct, is_run, pill_type, spin_idx=0):
    try:
        return create_tray_image(pct, spin_idx)
    except Exception:
        img = Image.new("RGBA", (64, 64), (16, 185, 129, 255) if pill_type == "ok" else (43, 127, 255, 255))
        drw = ImageDraw.Draw(img)
        drw.rectangle((4, 4, 60, 60), outline=(255, 255, 255, 220), width=3)
        drw.text((12, 22), f"{int(pct)}%" if is_run else "HGB", fill=(255, 255, 255, 255))
        return img

def _force_quit_app(engine):
    try:
        if engine.tray_icon is not None:
            engine.tray_icon.stop()
    except Exception:
        pass
    try:
        if engine.app_ref is not None:
            engine.app_ref.root.quit()
            engine.app_ref.root.destroy()
    except Exception:
        pass
    os._exit(0)

def _start_tray_thread(engine):
    if not HAS_TRAY:
        return
    from core.backup import run_backup_task

    def _on_open(icon, item):
        if engine.app_ref is not None:
            engine.app_ref.root.after(0, engine.app_ref.show_window)

    def _on_backup(icon, item):
        if engine.is_running:
            return
        threading.Thread(
            target=run_backup_task,
            args=(engine, engine.state.get("server", ""), False, False, False),
            daemon=True
        ).start()

    def _on_exit(icon, item):
        _force_quit_app(engine)

    menu = pystray.Menu(
        pystray.MenuItem("Відкрити HomeGrid Backup", _on_open, default=True),
        pystray.MenuItem("▶ Запустити резервне копіювання", _on_backup),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("✖ Вихід", _on_exit)
    )
    icon = pystray.Icon("HomeGridBackup", _get_tray_img_safe(0, False, "idle", 0), "HomeGrid Backup", menu)
    engine.tray_icon = icon

    def _anim_loop():
        while True:
            time.sleep(1.2 if engine.state.get("lite_mode", False) else 0.7)
            try:
                if engine.tray_icon is None:
                    break
                if engine.is_running:
                    engine.tray_spin_idx = (engine.tray_spin_idx + 1) % 8
                engine.tray_icon.icon = _get_tray_img_safe(engine.progress, engine.is_running, engine.pill_type, engine.tray_spin_idx)
                engine.tray_icon.title = f"HomeGrid Backup ({engine.progress}%): {(engine.stage or 'Готовий')[:45]}"
            except Exception:
                pass

    threading.Thread(target=_anim_loop, daemon=True).start()
    threading.Thread(target=icon.run, daemon=True).start()

def _start_show_window_listener(engine, event_name=r"Global\HomeGridBackup_ShowWindow_v1"):
    if os.name != "nt":
        return
    def _wait_loop():
        try:
            k32 = ctypes.windll.kernel32
            h_ev = k32.CreateEventW(None, False, False, event_name)
            while h_ev:
                if k32.WaitForSingleObject(h_ev, 1000) == 0 and engine.app_ref is not None:
                    engine.app_ref.root.after(0, engine.app_ref.show_window)
        except Exception:
            pass
    threading.Thread(target=_wait_loop, daemon=True).start()
