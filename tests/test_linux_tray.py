# patch-id: sync-tests-with-current-api-4.04.2
_F='gui.tray.ctypes.CDLL'
_E='libX11.so.6'
_D='ctypes.util.find_library'
_C='DISPLAY'
_B=False
_A=True
import os,unittest
from unittest import mock
from gui import tray
class LinuxTrayBackendTests(unittest.TestCase):
	def detect(D,*,display=':0',wayland=None,has_sni=_B,has_appindicator=_B,has_gtk=_B,has_x11=_B):
		B=wayland;A=display;C={_C:A}if A else{}
		if B:C['WAYLAND_DISPLAY']=B
		with mock.patch('sys.platform','linux'),mock.patch.dict(os.environ,C,clear=_A),mock.patch('core.config.IS_WSL',_B),mock.patch.object(tray,'_clean_sys_env',return_value={}),mock.patch.object(tray,'_has_sni_watcher',return_value=has_sni),mock.patch.object(tray,'_has_appindicator_gi',return_value=has_appindicator),mock.patch.object(tray,'_has_gtk_gi',return_value=has_gtk),mock.patch.object(tray,'_has_x11_tray_manager',return_value=has_x11):return tray._detect_linux_tray_backend()
	def test_prefers_appindicator_when_status_notifier_is_available(A):A.assertEqual(A.detect(has_sni=_A,has_appindicator=_A),'appindicator')
	def test_uses_automatic_backend_when_status_notifier_is_available(A):A.assertEqual(A.detect(has_sni=_A),'sni-bridge')
	def test_uses_xembed_backend_when_an_x11_tray_manager_is_available(A):A.assertEqual(A.detect(has_x11=_A,has_gtk=_A),'gtk')
	def test_falls_back_to_xorg_when_gtk_is_unavailable(A):A.assertEqual(A.detect(has_x11=_A),'xorg')
	def test_does_not_claim_a_tray_without_a_supported_protocol(A):A.assertEqual(A.detect(has_x11=_B),'')
	def test_wayland_session_is_checked_for_status_notifier(A):A.assertEqual(A.detect(display='',wayland='wayland-0',has_sni=_A),'sni-bridge')
	def test_x11_tray_detection_checks_selection_owner(B):
		A=mock.Mock();A.XOpenDisplay.return_value=123;A.XDefaultScreen.return_value=0;A.XInternAtom.return_value=456;A.XGetSelectionOwner.return_value=789
		with mock.patch.dict(os.environ,{_C:':0'}),mock.patch(_D,return_value=_E),mock.patch(_F,return_value=A):B.assertTrue(tray._has_x11_tray_manager())
		A.XGetSelectionOwner.assert_called_once_with(123,456);A.XCloseDisplay.assert_called_once_with(123)
	def test_x11_tray_detection_rejects_an_unowned_selection(B):
		A=mock.Mock();A.XOpenDisplay.return_value=123;A.XDefaultScreen.return_value=0;A.XInternAtom.return_value=456;A.XGetSelectionOwner.return_value=0
		with mock.patch.dict(os.environ,{_C:':0'}),mock.patch(_D,return_value=_E),mock.patch(_F,return_value=A):B.assertFalse(tray._has_x11_tray_manager())
	def test_tray_status_is_compact_and_includes_elapsed_time_and_progress(A):C=mock.Mock(is_running=_A,progress=42.8,stage='Копіювання бази та файлів');B=tray._tray_status_text(C,'en',61);A.assertIn('Backup',B);A.assertIn('42%',B);A.assertIn('1:01',B);A.assertNotIn('Copying DB & files',B);A.assertNotIn('Копіювання',B);A.assertEqual(tray._tray_status_text(C,'uk',61),'Архівація · 1:01 · 42%')
	def test_tray_status_formats_elapsed_hours_compactly(A):B=mock.Mock(is_running=_A,progress=100);A.assertEqual(tray._tray_status_text(B,'en',3661),'Backup · 1:01:01 · 100%')
	def test_tray_menu_status_shows_idle_state(A):B=mock.Mock(is_running=_B);A.assertEqual(tray._tray_status_text(B,'en'),'Ready for backup')
if __name__=='__main__':unittest.main()
