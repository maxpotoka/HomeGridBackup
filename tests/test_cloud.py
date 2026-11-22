import os
import tempfile
import unittest
from unittest import mock

from core import cloud


class RcloneExecutableTests(unittest.TestCase):
    def test_prefers_bundled_rclone(self):
        executable_name = "rclone.exe" if os.name == "nt" else "rclone"
        with tempfile.TemporaryDirectory() as app_dir:
            bundled = os.path.join(app_dir, executable_name)
            with open(bundled, "wb") as executable:
                executable.write(b"rclone")
            with mock.patch.object(cloud.sys, "executable", os.path.join(app_dir, "HomeGridBackup.exe")), \
                 mock.patch.object(cloud.shutil, "which", return_value="system-rclone"):
                self.assertEqual(cloud._rclone_executable(), bundled)

    def test_falls_back_to_path_when_no_bundled_rclone_exists(self):
        with tempfile.TemporaryDirectory() as app_dir:
            with mock.patch.object(cloud.sys, "executable", os.path.join(app_dir, "HomeGridBackup.exe")), \
                 mock.patch.object(cloud.shutil, "which", return_value="system-rclone"):
                self.assertEqual(cloud._rclone_executable(), "system-rclone")


if __name__ == "__main__":
    unittest.main()
