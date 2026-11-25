_B='__compiled__'
_A='icon.ico'
import os,tempfile,unittest
from types import SimpleNamespace
from unittest import mock
from core import files
class AppIconPathTests(unittest.TestCase):
	def test_finds_icon_next_to_nuitka_containing_directory(C):
		with tempfile.TemporaryDirectory()as A:
			B=os.path.join(A,_A)
			with open(B,'wb')as D:D.write(b'icon')
			with mock.patch.dict(files.__dict__,{_B:SimpleNamespace(containing_dir=A)}):C.assertEqual(files.get_app_icon_path(),B)
	def test_finds_icon_in_macos_app_resources(F):
		E='Contents'
		with tempfile.TemporaryDirectory()as A:
			B=os.path.join(A,E,'MacOS');C=os.path.join(A,E,'Resources');os.makedirs(B);os.makedirs(C);D=os.path.join(C,_A)
			with open(D,'wb')as G:G.write(b'icon')
			with mock.patch.dict(files.__dict__,{_B:SimpleNamespace(containing_dir=B)}):F.assertEqual(files.get_app_icon_path(),D)
if __name__=='__main__':unittest.main()
