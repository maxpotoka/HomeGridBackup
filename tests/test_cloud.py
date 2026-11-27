# patch-id: sync-tests-with-current-api-4.04.2
import json, os, tempfile, unittest
from types import SimpleNamespace
from unittest import mock
from core import cloud

class CloudAndJournalTests(unittest.TestCase):
    def test_cloud_queue_translation_keeps_format_placeholders(self):
        from core.i18n import tr
        s = '\u0427\u0435\u0440\u0433\u0430 \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0456\u0437\u0430\u0446\u0456\u0457: \u0430\u0440\u0445\u0456\u0432\u0438 {archives}, \u0437\u0432\u0456\u0442\u0438 {reports}'
        self.assertEqual(tr(s, 'uk').format(archives=2, reports=3), '\u0427\u0435\u0440\u0433\u0430 \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0456\u0437\u0430\u0446\u0456\u0457: \u0430\u0440\u0445\u0456\u0432\u0438 2, \u0437\u0432\u0456\u0442\u0438 3')
        self.assertEqual(tr(s, 'en').format(archives=2, reports=3), 'Cloud sync queue: archives 2, reports 3')

    def test_validate_cloud_settings_normalizes_path(self):
        self.assertEqual(cloud.validate_cloud_settings('drive', ''), 'HomeGridBackup')
        self.assertEqual(cloud.validate_cloud_settings('drive', '/HomeGridBackup/backups/'), 'HomeGridBackup/backups')

    def test_device_id_validation(self):
        self.assertEqual(cloud._device_id({'device_id': 'a' * 32}), 'a' * 32)
        with self.assertRaises(ValueError):
            cloud._device_id({'device_id': 'invalid'})

    def test_record_operation_event_writes_local_jsonl(self):
        dev = 'a' * 32
        with tempfile.TemporaryDirectory() as tmp:
            eng = SimpleNamespace(state={'device_id': dev, 'all_time_cnt': 3})
            with mock.patch.object(cloud, '_reports_base_dir', return_value=tmp):
                cloud.record_operation_event(eng, 'op-1', 'success', stage='done', archive='backup.tar.zst', size_mb=15.5, duration_sec=4.2, download_speed_mbps=6.8)
            fp = os.path.join(tmp, dev, 'operations.jsonl')
            self.assertTrue(os.path.isfile(fp))
            with open(fp, encoding='utf-8') as f: rec = json.loads(f.readline())
            self.assertEqual(rec['device_id'], dev)
            self.assertEqual(rec['operation_id'], 'op-1')
            self.assertEqual(rec['archives_total'], 3)
            self.assertEqual(rec['download_speed_mbps'], 6.8)

    def test_sync_network_shared_journal_merges_and_renders_reports(self):
        dev1, dev2 = '1' * 32, '2' * 32
        with tempfile.TemporaryDirectory() as rep_dir, tempfile.TemporaryDirectory() as net_dir:
            os.makedirs(os.path.join(rep_dir, dev1), exist_ok=True)
            with open(os.path.join(rep_dir, dev1, 'operations.jsonl'), 'w', encoding='utf-8') as f:
                f.write(json.dumps({'timestamp': '2026-11-27T01:00:00+00:00', 'device_id': dev1, 'operation_id': 'op-1', 'event': 'success', 'platform': 'Windows', 'platform_version': '10', 'size_mb': 10.0, 'duration_sec': 2.0}) + '\n')
            src_dir = os.path.join(net_dir, '.HomeGridBackup-sources')
            os.makedirs(src_dir, exist_ok=True)
            with open(os.path.join(src_dir, f'{dev2}.jsonl'), 'w', encoding='utf-8') as f:
                f.write(json.dumps({'timestamp': '2026-11-27T02:00:00+00:00', 'device_id': dev2, 'operation_id': 'op-2', 'event': 'success', 'platform': 'Linux', 'platform_version': '6.8', 'size_mb': 20.0, 'duration_sec': 4.0}) + '\n')
            eng = SimpleNamespace(state={'device_id': dev1, 'net_dir': net_dir})
            with mock.patch.object(cloud, '_reports_base_dir', return_value=rep_dir), mock.patch.object(cloud, 'SECURE_DIR', rep_dir):
                self.assertTrue(cloud.sync_network_shared_journal(eng))
            self.assertTrue(os.path.isfile(os.path.join(net_dir, 'HomeGridBackup.log')))
            self.assertTrue(os.path.isfile(os.path.join(net_dir, 'speed_journal.csv')))
            with open(os.path.join(net_dir, 'HomeGridBackup.log'), encoding='utf-8') as f: log_txt = f.read()
            self.assertIn('OS=Windows 10', log_txt)
            self.assertIn('OS=Linux 6.8', log_txt)

    def test_fetch_cloud_speed_stats_aggregates_devices(self):
        dev = 'b' * 32
        with tempfile.TemporaryDirectory() as rep_dir:
            os.makedirs(os.path.join(rep_dir, dev), exist_ok=True)
            with open(os.path.join(rep_dir, dev, 'operations.jsonl'), 'w', encoding='utf-8') as f:
                f.write(json.dumps({'timestamp': '2026-11-27T01:00:00+00:00', 'device_id': dev, 'operation_id': 'op-1', 'event': 'success', 'platform': 'Windows', 'platform_version': '10', 'archive': 'backup.tar.zst', 'size_mb': 50.0, 'duration_sec': 5.0, 'download_speed_mbps': 10.0, 'download_duration_sec': 5.0}) + '\n')
            eng = SimpleNamespace(state={'device_id': dev})
            with mock.patch.object(cloud, '_reports_base_dir', return_value=rep_dir), mock.patch.object(cloud, 'SECURE_DIR', rep_dir):
                res = cloud.fetch_cloud_speed_stats(eng, refresh=False)
            self.assertEqual(len(res['ops']), 1)
            self.assertEqual(len(res['devices']), 1)
            self.assertEqual(next(iter(res['devices']))['avg_spd'], 10.0)

if __name__ == '__main__':
    unittest.main()
