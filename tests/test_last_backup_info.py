import os
import tempfile
import unittest
from unittest import mock

from core.engine import BackupEngine
from core.i18n import tr


class LastBackupInfoTests(unittest.TestCase):
    def _engine_with_last_archive(self, lang, duration_sec):
        temp_dir = tempfile.TemporaryDirectory()
        archive_path = os.path.join(temp_dir.name, "homegrid_backup_DAILY_test.zip")
        with open(archive_path, "wb") as archive:
            archive.truncate(1048576)
        with open(archive_path + ".sha256", "w", encoding="utf-8"):
            pass

        engine = BackupEngine.__new__(BackupEngine)
        engine.state = {
            "backup_dir": temp_dir.name,
            "lang": lang,
            "op_history": [{
                "status": "Успішно",
                "detail": os.path.basename(archive_path),
                "dur_sec": duration_sec,
            }],
        }
        engine._last_backup_cache = None
        engine._last_backup_cache_time = 0.0
        engine._last_backup_cache_dir = None
        engine.get_archive_snapshot = mock.Mock(return_value=[{
            "path": archive_path,
            "mtime": 1700000000,
            "size": os.path.getsize(archive_path),
        }])
        return temp_dir, engine

    def test_last_archive_creation_duration_is_shown_in_ukrainian(self):
        temp_dir, engine = self._engine_with_last_archive("uk", 125.4)
        try:
            text, status = engine.get_last_backup_info()
            self.assertEqual(status, "ok")
            self.assertIn("Час створення: 2 хв 05 с", text)
        finally:
            temp_dir.cleanup()

    def test_last_archive_creation_duration_is_shown_in_english(self):
        temp_dir, engine = self._engine_with_last_archive("en", 125.4)
        try:
            text, status = engine.get_last_backup_info()
            self.assertEqual(status, "ok")
            self.assertIn("Creation time: 2 min 05 sec", tr(text, "en"))
        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
