From 10a22000c713d44e697250fb864600ef786f718b Mon Sep 17 00:00:00 2001
From: maxpotoka <maxpotoka@users.noreply.github.com>
Date: Mon, 23 Nov 2026 04:17:01 +0000
Subject: [PATCH] Tray: confirm exit during backup, rebuild menu on change,
 state dot

- Exit from the tray asks for confirmation when a backup is running.
- Tray menu is rebuilt only when the state changes or a backup runs,
  instead of every second.
- Tray icon shows a small dot: green (ok), red (error), blue (working).

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_013N4KvziCbXn3ACUDBS1S9h
---
 gui/tray.py | 31 ++++++++++++++++++++++++++-----
 1 file changed, 26 insertions(+), 5 deletions(-)

diff --git a/gui/tray.py b/gui/tray.py
index de4fab8..e04f22f 100644
--- a/gui/tray.py
+++ b/gui/tray.py
@@ -173,7 +173,21 @@ def _get_tray_font():
     _TRAY_FONT = ImageFont.load_default()
     return _TRAY_FONT
 
-def create_tray_image(pct=0, spin_idx=0):
+_STATE_DOT = {
+    "ok": (16, 185, 129, 255),
+    "err": (239, 68, 68, 255),
+    "work": (43, 127, 255, 255),
+}
+
+def _add_state_dot(img, state):
+    color = _STATE_DOT.get(state)
+    if color is None:
+        return img
+    drw = ImageDraw.Draw(img)
+    drw.ellipse([46, 46, 62, 62], fill=color, outline=(11, 18, 32, 255), width=2)
+    return img
+
+def create_tray_image(pct=0, spin_idx=0, state="idle"):
     from core.files import get_app_icon_path
     ico_p = get_app_icon_path()
     base_img = None
@@ -190,15 +204,15 @@ def create_tray_image(pct=0, spin_idx=0):
             drw.ellipse([36, 36, 62, 62], fill=(11, 18, 32, 235), outline=(16, 185, 129, 255), width=3)
             end_ang = -90 + int(360 * p_val / 100.0)
             drw.arc([38, 38, 60, 60], start=-90, end=end_ang, fill=(16, 185, 129, 255), width=4)
-        return img
+        return _add_state_dot(img, state)
     img = Image.new("RGBA", (64, 64), (11, 18, 32, 255))
     drw = ImageDraw.Draw(img)
     drw.ellipse([3, 3, 61, 61], outline=(43, 127, 255, 255), width=6)
-    return img
+    return _add_state_dot(img, state)
 
 def _get_tray_img_safe(pct, is_run, pill_type, spin_idx=0):
     try:
-        return create_tray_image(pct, spin_idx)
+        return create_tray_image(pct, spin_idx, pill_type)
     except Exception:
         img = Image.new("RGBA", (64, 64), (16, 185, 129, 255) if pill_type == "ok" else (43, 127, 255, 255))
         drw = ImageDraw.Draw(img)
@@ -344,6 +358,13 @@ def _start_tray_thread(engine):
         ).start()
 
     def _on_exit(icon, item):
+        app = engine.app_ref
+        if engine.is_running and app is not None:
+            def _ask():
+                app.show_window()
+                app.confirm_exit()
+            app.root.after(0, _ask)
+            return
         _force_quit_app(engine)
 
     def _on_open_folder(icon, item):
@@ -468,7 +489,7 @@ def _start_tray_thread(engine):
                     if sig_changed:
                         engine.tray_icon.icon = _get_tray_img_safe(cur_pct, engine.is_running, engine.pill_type, 0)
                         last_sig = sig
-                    if os.sys.platform != "darwin" or sig_changed:
+                    if sig_changed or engine.is_running:
                         engine.tray_icon.menu = _build_tray_menu()
                         engine.tray_icon.update_menu()
                     if new_title != last_title:
-- 
2.43.0

