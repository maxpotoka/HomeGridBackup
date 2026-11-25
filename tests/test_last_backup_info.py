import os,tempfile,unittest
from unittest import mock
from core.engine import BackupEngine
from core.i18n import tr
class LastBackupInfoTests(unittest.TestCase):
	def _engine_with_last_archive(E,lang,duration_sec):
		C=tempfile.TemporaryDirectory();B=os.path.join(C.name,'homegrid_backup_DAILY_test.zip')
		with open(B,'wb')as D:D.truncate(1048576)
		with open(B+'.sha256','w',encoding='utf-8'):0
		A=BackupEngine.__new__(BackupEngine);A.state={'backup_dir':C.name,'lang':lang,'op_history':[{'status':'Успішно','detail':os.path.basename(B),'dur_sec':duration_sec}]};A._last_backup_cache=None;A._last_backup_cache_time=.0;A._last_backup_cache_dir=None;A.get_archive_snapshot=mock.Mock(return_value=[{'path':B,'mtime':1700000000,'size':os.path.getsize(B)}]);return C,A
	def test_last_archive_creation_duration_is_shown_in_ukrainian(A):
		B,C=A._engine_with_last_archive('uk',125.4)
		try:D,E=C.get_last_backup_info();A.assertEqual(E,'ok');A.assertIn('Час створення: 2 хв 05 с',D)
		finally:B.cleanup()
	def test_last_archive_creation_duration_is_shown_in_english(A):
		B,C=A._engine_with_last_archive('en',125.4)
		try:D,E=C.get_last_backup_info();A.assertEqual(E,'ok');A.assertIn('Creation time: 2 min 05 sec',tr(D,'en'))
		finally:B.cleanup()
if __name__=='__main__':unittest.main()
