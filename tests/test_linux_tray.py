import os
import unittest
from unittest import mock

from gui import tray


class LinuxTrayBackendTests(unittest.TestCase):
    def detect(self, *, display=":0", wayland=None, has_sni=False, has_appindicator=False, has_gtk=False, has_x11=False):
        env = {"DISPLAY": display} if display else {}
        if wayland:
            env["WAYLAND_DISPLAY"] = wayland
        with mock.patch("sys.platform", "linux"), \
                mock.patch.dict(os.environ, env, clear=True), \
                mock.patch("core.config.IS_WSL", False), \
                mock.patch.object(tray, "_clean_sys_env", return_value={}), \
                mock.patch.object(tray, "_has_sni_watcher", return_value=has_sni), \
                mock.patch.object(tray, "_has_appindicator_gi", return_value=has_appindicator), \
                mock.patch.object(tray, "_has_gtk_gi", return_value=has_gtk), \
                mock.patch.object(tray, "_has_x11_tray_manager", return_value=has_x11):
            return tray._detect_linux_tray_backend()

    def test_prefers_appindicator_when_status_notifier_is_available(self):
        self.assertEqual(self.detect(has_sni=True, has_appindicator=True), "appindicator")

    def test_uses_automatic_backend_when_status_notifier_is_available(self):
        self.assertEqual(self.detect(has_sni=True), "auto")

    def test_uses_xembed_backend_when_an_x11_tray_manager_is_available(self):
        self.assertEqual(self.detect(has_x11=True, has_gtk=True), "gtk")

    def test_falls_back_to_xorg_when_gtk_is_unavailable(self):
        self.assertEqual(self.detect(has_x11=True), "xorg")

    def test_does_not_claim_a_tray_without_a_supported_protocol(self):
        self.assertEqual(self.detect(has_x11=False), "")

    def test_wayland_session_is_checked_for_status_notifier(self):
        self.assertEqual(self.detect(display="", wayland="wayland-0", has_sni=True), "auto")

    def test_x11_tray_detection_checks_selection_owner(self):
        x11 = mock.Mock()
        x11.XOpenDisplay.return_value = 123
        x11.XDefaultScreen.return_value = 0
        x11.XInternAtom.return_value = 456
        x11.XGetSelectionOwner.return_value = 789
        with mock.patch.dict(os.environ, {"DISPLAY": ":0"}), \
                mock.patch("ctypes.util.find_library", return_value="libX11.so.6"), \
                mock.patch("gui.tray.ctypes.CDLL", return_value=x11):
            self.assertTrue(tray._has_x11_tray_manager())
        x11.XGetSelectionOwner.assert_called_once_with(123, 456)
        x11.XCloseDisplay.assert_called_once_with(123)

    def test_x11_tray_detection_rejects_an_unowned_selection(self):
        x11 = mock.Mock()
        x11.XOpenDisplay.return_value = 123
        x11.XDefaultScreen.return_value = 0
        x11.XInternAtom.return_value = 456
        x11.XGetSelectionOwner.return_value = 0
        with mock.patch.dict(os.environ, {"DISPLAY": ":0"}), \
                mock.patch("ctypes.util.find_library", return_value="libX11.so.6"), \
                mock.patch("gui.tray.ctypes.CDLL", return_value=x11):
            self.assertFalse(tray._has_x11_tray_manager())

    def test_tray_menu_status_includes_progress_stage_and_elapsed_time(self):
        engine = mock.Mock(
            is_running=True,
            progress=42.8,
            stage="Копіювання бази та файлів",
        )
        text = tray._tray_status_text(engine, "en", 61)
        self.assertIn("Backing up...", text)
        self.assertIn("42%", text)
        self.assertIn("Copying DB & files", text)
        self.assertIn("1m 1s", text)

    def test_tray_menu_status_shows_idle_state(self):
        engine = mock.Mock(is_running=False)
        self.assertEqual(
            tray._tray_status_text(engine, "en"),
            "Ready for backup",
        )


if __name__ == "__main__":
    unittest.main()
