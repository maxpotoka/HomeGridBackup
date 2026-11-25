_C='_LNX_TRAY_BE'
_B='HAS_TRAY'
_A='platform'
import unittest
from unittest import mock
from gui import tray
class TrayPlatformAvailabilityTests(unittest.TestCase):
	def test_windows_uses_native_tray_without_linux_backend(A):
		with mock.patch.object(tray.os.sys,_A,'win32'),mock.patch.object(tray,_B,True),mock.patch.object(tray,_C,''):A.assertTrue(tray._tray_backend_available())
	def test_linux_requires_a_detected_tray_backend(A):
		with mock.patch.object(tray.os.sys,_A,'linux'),mock.patch.object(tray,_B,True),mock.patch.object(tray,_C,''):A.assertFalse(tray._tray_backend_available())
if __name__=='__main__':unittest.main()
