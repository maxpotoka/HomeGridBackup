import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from core import files


class AppIconPathTests(unittest.TestCase):
    def test_finds_icon_next_to_nuitka_containing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            icon_path = os.path.join(directory, "icon.ico")
            with open(icon_path, "wb") as icon_file:
                icon_file.write(b"icon")
            with mock.patch.dict(
                files.__dict__,
                {"__compiled__": SimpleNamespace(containing_dir=directory)},
            ):
                self.assertEqual(files.get_app_icon_path(), icon_path)

    def test_finds_icon_in_macos_app_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            compiled_dir = os.path.join(directory, "Contents", "MacOS")
            resources_dir = os.path.join(directory, "Contents", "Resources")
            os.makedirs(compiled_dir)
            os.makedirs(resources_dir)
            icon_path = os.path.join(resources_dir, "icon.ico")
            with open(icon_path, "wb") as icon_file:
                icon_file.write(b"icon")
            with mock.patch.dict(
                files.__dict__,
                {"__compiled__": SimpleNamespace(containing_dir=compiled_dir)},
            ):
                self.assertEqual(files.get_app_icon_path(), icon_path)


if __name__ == "__main__":
    unittest.main()
