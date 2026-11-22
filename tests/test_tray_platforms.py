import unittest
from unittest import mock

from gui import tray


class TrayPlatformAvailabilityTests(unittest.TestCase):
    def test_windows_uses_native_tray_without_linux_backend(self):
        with mock.patch.object(tray.os.sys, "platform", "win32"), \
             mock.patch.object(tray, "HAS_TRAY", True), \
             mock.patch.object(tray, "_LNX_TRAY_BE", ""):
            self.assertTrue(tray._tray_backend_available())

    def test_linux_requires_a_detected_tray_backend(self):
        with mock.patch.object(tray.os.sys, "platform", "linux"), \
             mock.patch.object(tray, "HAS_TRAY", True), \
             mock.patch.object(tray, "_LNX_TRAY_BE", ""):
            self.assertFalse(tray._tray_backend_available())


if __name__ == "__main__":
    unittest.main()
