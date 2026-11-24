import os
import json
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

from core import cloud


class RcloneExecutableTests(unittest.TestCase):
    def test_windows7_preview_exposes_only_mega_and_koofr(self):
        with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True):
            self.assertEqual(
                [provider[1] for provider in cloud.available_rclone_providers()],
                ["mega", "koofr"],
            )
        with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", False):
            self.assertEqual(
                [provider[1] for provider in cloud.available_rclone_providers()],
                ["drive", "onedrive", "dropbox", "box", "pcloud", "mega", "koofr"],
            )

    def test_preview_credential_setup_creates_mega_and_koofr_without_prompts(self):
        result = mock.Mock(returncode=0, stdout="", stderr="")
        cases = (
            ("mega", ["user", "user@example.com", "pass", "secret"]),
            ("koofr", ["user", "user@example.com", "password", "secret", "provider", "koofr"]),
        )
        for backend, options in cases:
            with self.subTest(backend=backend), \
                 mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
                 mock.patch.object(cloud, "list_rclone_remotes", return_value=[]), \
                 mock.patch.object(cloud, "_rclone_executable", return_value="rclone"), \
                 mock.patch.object(cloud, "_run", return_value=result) as run:
                cloud.create_rclone_remote("mycloud", backend, "user@example.com", "secret")
            self.assertEqual(
                run.call_args.args[0],
                [
                    "rclone", "config", "create", "mycloud", backend,
                    *options, "--obscure", "--non-interactive",
                ],
            )
            self.assertEqual(run.call_args.args[1], 60)

    def test_preview_credential_setup_rejects_providers_other_than_mega_and_koofr(self):
        with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True):
            with self.assertRaisesRegex(ValueError, "Unsupported cloud provider"):
                cloud.create_rclone_remote("drive", "drive", "user", "password")

    def test_preview_credential_setup_redacts_password_from_errors(self):
        result = mock.Mock(returncode=1, stdout="", stderr="failed secret")
        with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
             mock.patch.object(cloud, "list_rclone_remotes", return_value=[]), \
             mock.patch.object(cloud, "_rclone_executable", return_value="rclone"), \
             mock.patch.object(cloud, "_run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, r"failed \[redacted\]"):
                cloud.create_rclone_remote("mega", "mega", "user", "secret")

    def test_preview_credential_setup_redacts_password_from_process_errors(self):
        error = cloud.subprocess.TimeoutExpired(["rclone", "secret"], 60)
        with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
             mock.patch.object(cloud, "list_rclone_remotes", return_value=[]), \
             mock.patch.object(cloud, "_rclone_executable", return_value="rclone"), \
             mock.patch.object(cloud, "_run", side_effect=error):
            with self.assertRaises(RuntimeError) as raised:
                cloud.create_rclone_remote("mega", "mega", "user", "secret")
        self.assertNotIn("secret", str(raised.exception))

    def test_cloud_queue_translation_keeps_format_placeholders(self):
        from core.i18n import tr

        source = "Черга синхронізації: архіви {archives}, звіти {reports}"
        self.assertEqual(
            tr(source, "uk").format(archives=2, reports=3),
            "Черга синхронізації: архіви 2, звіти 3",
        )
        self.assertEqual(
            tr(source, "en").format(archives=2, reports=3),
            "Cloud sync queue: archives 2, reports 3",
        )

    def test_cloud_settings_reject_a_blank_folder_or_remote_root(self):
        for path in ("", " / ", "///"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "корінь"):
                cloud.validate_cloud_settings("drive", path)

    def test_cloud_settings_accept_a_relative_folder(self):
        self.assertEqual(
            cloud.validate_cloud_settings("drive", "/HomeGridBackup/backups/"),
            "HomeGridBackup/backups",
        )

    def test_run_disables_stdin_and_console_window(self):
        expected = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(cloud, "_NO_WINDOW", 0x08000000), \
             mock.patch.object(cloud.subprocess, "run", return_value=expected) as run:
            result = cloud._run(["rclone", "listremotes"], 15)
        self.assertIs(result, expected)
        self.assertIs(run.call_args.kwargs["stdin"], cloud.subprocess.DEVNULL)
        self.assertEqual(run.call_args.kwargs["creationflags"], 0x08000000)

    def test_rclone_uses_retries_and_a_request_rate_limit(self):
        with mock.patch.object(cloud, "_rclone_executable", return_value="rclone"), \
             mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
             mock.patch.object(cloud, "_run", return_value=mock.Mock(returncode=0, stdout="", stderr="")) as run:
            cloud._rclone("copyto", "archive.zip", "drive:HomeGridBackup/archive.zip", timeout=60)
        self.assertEqual(
            run.call_args.args,
            ([
                "rclone", "--retries", "3", "--low-level-retries", "10",
                "--tpslimit", "2", "--stats", "0", "copyto",
                "archive.zip", "drive:HomeGridBackup/archive.zip",
            ], 60),
        )

    def test_non_preview_rclone_preserves_provider_error(self):
        response = mock.Mock(
            returncode=1, stdout="",
            stderr='{"reason":"RATE_LIMIT_EXCEEDED","status":"rateLimitExceeded"}',
        )
        with mock.patch.object(cloud, "_rclone_executable", return_value="rclone"), \
             mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", False), \
             mock.patch.object(cloud, "_run", return_value=response):
            with self.assertRaises(RuntimeError):
                cloud._rclone("copyto", "archive.zip", "drive:HomeGridBackup/archive.zip")

    def test_preview_shortens_rate_limit_errors(self):
        response = mock.Mock(
            returncode=1, stdout="",
            stderr='{"reason":"RATE_LIMIT_EXCEEDED","status":"rateLimitExceeded"}',
        )
        with mock.patch.object(cloud, "_rclone_executable", return_value="rclone"), \
             mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
             mock.patch.object(cloud, "_run", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "personal OAuth client"):
                cloud._rclone("copyto", "archive.zip", "drive:HomeGridBackup/archive.zip")

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

    def test_setup_starts_interactive_rclone_without_a_console_window(self):
        process = mock.Mock()
        with mock.patch.object(cloud, "list_rclone_remotes", return_value=[]), \
             mock.patch.object(cloud, "_rclone_executable", return_value="rclone"), \
             mock.patch.object(cloud.subprocess, "Popen", return_value=process) as popen:
            self.assertIs(cloud.start_rclone_remote_setup("mydrive", "drive"), process)
        self.assertEqual(popen.call_args.args[0], ["rclone", "config", "create", "mydrive", "drive"])
        self.assertIs(popen.call_args.kwargs["stdin"], cloud.subprocess.PIPE)
        self.assertIs(popen.call_args.kwargs["stderr"], cloud.subprocess.STDOUT)
        self.assertEqual(popen.call_args.kwargs["creationflags"], cloud._NO_WINDOW)

    def test_mega_uses_the_supported_rclone_backend_and_remote_path(self):
        process = mock.Mock()
        state = {
            "cloud_remote": "mega",
            "cloud_path": "HomeGridBackup",
            "device_id": "a" * 32,
        }
        with mock.patch.object(cloud, "list_rclone_remotes", return_value=[]), \
             mock.patch.object(cloud, "_rclone_executable", return_value="rclone"), \
             mock.patch.object(cloud.subprocess, "Popen", return_value=process) as popen:
            self.assertIs(cloud.start_rclone_remote_setup("mega", "mega"), process)
        self.assertEqual(popen.call_args.args[0], ["rclone", "config", "create", "mega", "mega"])
        self.assertEqual(
            cloud._remote_path(state, "backups", state["device_id"]),
            "mega:HomeGridBackup/backups/{}".format(state["device_id"]),
        )

    def test_setup_rejects_invalid_remote_and_backend(self):
        with self.assertRaises(ValueError):
            cloud.start_rclone_remote_setup("../bad", "drive")
        with self.assertRaises(ValueError):
            cloud.start_rclone_remote_setup("valid", "unsupported")
        with mock.patch.object(cloud, "list_rclone_remotes", return_value=["valid"]):
            with self.assertRaises(ValueError):
                cloud.start_rclone_remote_setup("valid", "drive")

    def test_remote_test_falls_back_to_listing_when_about_is_unsupported(self):
        with mock.patch.object(cloud, "_rclone", side_effect=[RuntimeError("no about"), ""] ) as rclone:
            cloud.test_rclone_remote("mydrive:")
        self.assertEqual(rclone.call_args_list, [
            mock.call("about", "mydrive:"),
            mock.call("lsd", "mydrive:", "--max-depth", "1")
        ])

    def test_operation_reports_are_local_and_include_comparison_metadata(self):
        device_id = "a" * 32
        state = {
            "backup_dir": tempfile.mkdtemp(),
            "device_id": device_id,
            "all_time_cnt": 4,
            "cloud_enabled": False,
        }
        engine = SimpleNamespace(state=state)
        try:
            with mock.patch.object(cloud, "_rclone_version", return_value="rclone v1.76.0"):
                cloud.record_operation_event(
                    engine, "operation-1", "stage_completed",
                    stage="archive_download", archive="backup.zip",
                    size_mb=12.5, size_bytes=13107200, duration_sec=2.34567,
                    files_count=9, archive_sequence=5, speed_mbps=5.34,
                    download_speed_mbps=7.3, download_duration_sec=29.9,
                    server_duration_sec=219.6, system_info="Windows 7 64-bit",
                    summary="v2.25 | Windows 7 64-bit | download 7.3 MB/s (29.9 s)",
                )
            report_dir = os.path.join(state["backup_dir"], "reports", device_id)
            report_path = os.path.join(report_dir, cloud.datetime.now().strftime("%Y-%m-%d") + ".jsonl")
            with open(report_path, encoding="utf-8") as report:
                record = json.loads(report.readline())
            self.assertEqual(record["device_id"], device_id)
            self.assertEqual(record["archives_total"], 4)
            self.assertEqual(record["archive_sequence"], 5)
            self.assertEqual(record["files_count"], 9)
            self.assertEqual(record["duration_ms"], 2346)
            self.assertEqual(record["rclone_version"], "rclone v1.76.0")
            self.assertTrue(record["platform"])
            self.assertEqual(record["system_info"], "Windows 7 64-bit")
            self.assertEqual(record["download_speed_mbps"], 7.3)
            self.assertEqual(record["server_duration_sec"], 219.6)
            self.assertIn("download 7.3 MB/s", record["summary"])
            self.assertTrue(os.path.isfile(report_path + ".pending"))
        finally:
            import shutil
            shutil.rmtree(state["backup_dir"])

    def test_sync_reports_uploads_local_reports_and_clears_pending_marker(self):
        device_id = "b" * 32
        with tempfile.TemporaryDirectory() as backup_dir:
            report_dir = os.path.join(backup_dir, "reports", device_id)
            os.makedirs(report_dir)
            report_path = os.path.join(report_dir, "2025-01-02.jsonl")
            with open(report_path, "w", encoding="utf-8") as report:
                report.write("{}\n")
            marker_path = report_path + ".pending"
            open(marker_path, "w").close()
            engine = SimpleNamespace(state={
                "backup_dir": backup_dir, "device_id": device_id,
                "cloud_enabled": True, "cloud_remote": "drive",
                "cloud_path": "HomeGridBackup",
            })
            with mock.patch.object(cloud, "_rclone") as rclone:
                cloud.sync_cloud_reports(engine)
            rclone.assert_called_once_with(
                "copyto", report_path,
                f"drive:HomeGridBackup/operations/{device_id}/2025-01-02.jsonl"
            )
            self.assertFalse(os.path.exists(marker_path))

    def test_preview_sync_merges_all_devices_into_one_plain_text_root_log(self):
        device_id = "1" * 32
        other_device_id = "2" * 32
        with tempfile.TemporaryDirectory() as backup_dir:
            report_dir = os.path.join(backup_dir, "reports", device_id)
            os.makedirs(report_dir)
            report_path = os.path.join(report_dir, "2025-01-02.jsonl")
            own_event = {
                "timestamp": "2025-01-02T10:00:00+00:00",
                "device_id": device_id,
                "operation_id": "operation-win7",
                "event": "success",
                "platform": "Windows",
                "platform_version": "7",
                "system_info": "Windows 7 64-bit",
                "summary": "download 7.3 MB/s (29.9 s) | server 219.6 s | total 260.9 s | files 4",
                "download_speed_mbps": 7.3,
                "server_duration_sec": 219.6,
                "files_count": 4,
            }
            other_event = {
                "timestamp": "2025-01-02T11:00:00+00:00",
                "device_id": other_device_id,
                "operation_id": "operation-linux",
                "event": "success",
                "platform": "Linux",
                "platform_version": "6.8",
                "system_info": "Linux 64-bit",
                "summary": "download 6.2 MB/s | server 180 s | total 190 s | files 3",
                "download_speed_mbps": 6.2,
                "server_duration_sec": 180,
                "files_count": 3,
            }
            legacy_event = {
                "timestamp": "2025-01-02T12:00:00+00:00",
                "device_id": "3" * 32,
                "operation_id": "operation-macos",
                "event": "success",
                "platform": "Darwin",
                "platform_version": "24.0",
                "summary": "download 5 MB/s | server 120 s | total 130 s | files 2",
            }
            with open(report_path, "w", encoding="utf-8") as report:
                report.write(json.dumps(own_event) + "\n")
            marker_path = report_path + ".pending"
            open(marker_path, "w").close()
            engine = SimpleNamespace(state={
                "backup_dir": backup_dir, "device_id": device_id,
                "cloud_enabled": True, "cloud_remote": "drive",
                "cloud_path": "HomeGridBackup",
            })
            own_source_records = []
            shared_log_lines = []

            def rclone(*args):
                if args[0] == "copy" and args[1] == "drive:HomeGridBackup/.HomeGridBackup-sources":
                    with open(os.path.join(args[2], other_device_id + ".jsonl"), "w", encoding="utf-8") as source:
                        source.write(json.dumps(other_event) + "\n")
                elif args[0] == "copy" and args[1] == "drive:HomeGridBackup/operations":
                    legacy_dir = os.path.join(args[2], "legacy", "2025-01-02")
                    os.makedirs(legacy_dir)
                    with open(os.path.join(legacy_dir, "2025-01-02.jsonl"), "w", encoding="utf-8") as source:
                        source.write(json.dumps(legacy_event) + "\n")
                elif args[0] == "copyto" and args[2] == (
                    f"drive:HomeGridBackup/.HomeGridBackup-sources/{device_id}.jsonl"
                ):
                    with open(args[1], encoding="utf-8") as source:
                        own_source_records.extend(json.loads(line) for line in source)
                elif args[0] == "copyto" and args[2] == "drive:HomeGridBackup/HomeGridBackup.log":
                    with open(args[1], encoding="utf-8") as merged:
                        shared_log_lines.extend(merged.readlines())

            with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
                 mock.patch.object(cloud, "_rclone", side_effect=rclone):
                self.assertTrue(cloud.sync_cloud_reports(engine))

            self.assertEqual(
                {record["device_id"] for record in own_source_records},
                {device_id},
            )
            self.assertEqual(len(shared_log_lines), 3)
            self.assertTrue(any("OS=Windows 7" in line for line in shared_log_lines))
            self.assertTrue(any("OS=Linux 6.8" in line for line in shared_log_lines))
            self.assertTrue(any("OS=Darwin 24.0" in line for line in shared_log_lines))
            self.assertTrue(any("server_duration_sec=219.6" in line for line in shared_log_lines))
            self.assertTrue(any("server_duration_sec=180" in line for line in shared_log_lines))
            self.assertFalse(any(line.lstrip().startswith("{") for line in shared_log_lines))
            self.assertFalse(os.path.exists(marker_path))

    def test_failed_report_upload_keeps_the_pending_marker_for_retry(self):
        device_id = "c" * 32
        with tempfile.TemporaryDirectory() as backup_dir:
            report_dir = os.path.join(backup_dir, "reports", device_id)
            os.makedirs(report_dir)
            report_path = os.path.join(report_dir, "2025-01-02.jsonl")
            with open(report_path, "w", encoding="utf-8") as report:
                report.write(json.dumps({
                    "timestamp": "2025-01-02T10:00:00+00:00",
                    "device_id": device_id,
                    "operation_id": "operation-1",
                    "event": "stage_started",
                }) + "\n")
            marker_path = report_path + ".pending"
            open(marker_path, "w").close()
            engine = SimpleNamespace(state={
                "backup_dir": backup_dir, "device_id": device_id,
                "cloud_enabled": True, "cloud_remote": "drive",
                "cloud_path": "HomeGridBackup",
            })
            with mock.patch.object(
                cloud,
                "_rclone",
                side_effect=cloud.CloudRateLimitError("rate limited"),
            ):
                with self.assertRaises(cloud.CloudRateLimitError):
                    cloud.sync_cloud_reports(engine)
            self.assertTrue(os.path.isfile(marker_path))

    def test_report_sync_preserves_a_new_append_during_upload(self):
        device_id = "d" * 32
        with tempfile.TemporaryDirectory() as backup_dir:
            report_dir = os.path.join(backup_dir, "reports", device_id)
            os.makedirs(report_dir)
            report_path = os.path.join(report_dir, "2025-01-02.jsonl")
            with open(report_path, "w", encoding="utf-8") as report:
                report.write(json.dumps({
                    "timestamp": "2025-01-02T10:00:00+00:00",
                    "device_id": device_id,
                    "operation_id": "operation-1",
                    "event": "stage_started",
                }) + "\n")
            marker_path = report_path + ".pending"
            open(marker_path, "w").close()
            engine = SimpleNamespace(state={
                "backup_dir": backup_dir, "device_id": device_id,
                "cloud_enabled": True, "cloud_remote": "drive",
                "cloud_path": "HomeGridBackup",
            })

            def append_during_upload(*args):
                if args[0] == "copyto" and args[2] == (
                    f"drive:HomeGridBackup/.HomeGridBackup-sources/{device_id}.jsonl"
                ):
                    with open(marker_path, "a", encoding="utf-8"):
                        pass

            with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
                 mock.patch.object(cloud, "_rclone", side_effect=append_during_upload):
                cloud.sync_cloud_reports(engine)

            self.assertTrue(os.path.isfile(marker_path))
            with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True):
                self.assertEqual(cloud.cloud_sync_queue_state(engine)["reports"], 1)

    def test_archive_sync_failure_leaves_a_persistent_queue_marker(self):
        with tempfile.TemporaryDirectory() as backup_dir:
            archive_path = os.path.join(backup_dir, "backup_DAILY_test.zip")
            with open(archive_path, "wb") as archive:
                archive.write(b"archive")
            engine = SimpleNamespace(state={
                "backup_dir": backup_dir, "device_id": "e" * 32,
                "cloud_enabled": True, "cloud_remote": "drive",
                "cloud_path": "HomeGridBackup",
            })
            with mock.patch(
                "core.gfs.compute_gfs_plan",
                return_value=(None, [{"path": archive_path}], None),
            ), mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), mock.patch.object(
                cloud, "_rclone", side_effect=cloud.CloudRateLimitError("rate limited")
            ):
                with self.assertRaises(cloud.CloudRateLimitError):
                    cloud.sync_cloud_backups(engine)
            self.assertTrue(os.path.isfile(os.path.join(backup_dir, ".cloud-archives.pending")))
            with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True):
                self.assertEqual(cloud.cloud_sync_queue_state(engine)["archives"], 1)
                self.assertEqual(
                    cloud.cloud_archive_sync_status(engine, os.path.basename(archive_path)),
                    "error",
                )

    def test_cloud_archive_status_tracks_queue_and_target_remote(self):
        with tempfile.TemporaryDirectory() as backup_dir:
            engine = SimpleNamespace(state={
                "backup_dir": backup_dir, "cloud_enabled": True, "cloud_remote": "mega",
                "cloud_path": "HomeGridBackup",
            })
            archive = "homegrid_backup_DAILY_test.zip"
            with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True):
                self.assertEqual(cloud.cloud_archive_sync_status(engine, archive), "unknown")
                open(os.path.join(backup_dir, ".cloud-archives.pending"), "w").close()
                self.assertEqual(cloud.cloud_archive_sync_status(engine, archive), "queued")
                cloud._write_cloud_archive_status(engine, archive, "uploaded")
                self.assertEqual(cloud.cloud_archive_sync_status(engine, archive), "uploaded")
                engine.state["cloud_remote"] = "koofr"
                self.assertEqual(cloud.cloud_archive_sync_status(engine, archive), "unknown")

    def test_preview_archives_share_one_folder_without_cross_device_pruning(self):
        device_id = "a" * 32
        other_device_id = "b" * 32
        archive_name = "homegrid_backup_DAILY_2025-01-02.zip"
        own_stale = device_id + "_homegrid_backup_DAILY_old.zip"
        other_stale = other_device_id + "_homegrid_backup_DAILY_old.zip"
        with tempfile.TemporaryDirectory() as backup_dir:
            archive_path = os.path.join(backup_dir, archive_name)
            with open(archive_path, "wb") as archive:
                archive.write(b"archive")
            with open(archive_path + ".sha256", "w", encoding="utf-8") as sidecar:
                sidecar.write("{}  {}\n".format("a" * 64, archive_name))
            engine = SimpleNamespace(state={
                "backup_dir": backup_dir, "device_id": device_id,
                "cloud_enabled": True, "cloud_remote": "drive",
                "cloud_path": "HomeGridBackup",
            })

            def rclone(*args):
                if args[0] == "lsf":
                    self.assertEqual(args[2], "drive:HomeGridBackup/backups")
                    return "\n".join((
                        own_stale, own_stale + ".sha256",
                        other_stale, other_stale + ".sha256",
                    ))
                if args[0] == "copyto" and args[1].endswith(".sha256") and ".tmp" not in args[1]:
                    with open(args[1], encoding="utf-8") as sidecar:
                        self.assertEqual(
                            sidecar.read(),
                            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  "
                            f"{device_id}_{archive_name}\n",
                        )

            with mock.patch("core.gfs.compute_gfs_plan", return_value=(None, [{"path": archive_path}], [])), \
                 mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
                 mock.patch.object(cloud, "_rclone", side_effect=rclone) as mocked_rclone:
                self.assertTrue(cloud.sync_cloud_backups(engine, prune=True))
            self.assertEqual(cloud.cloud_archive_sync_status(engine, archive_name), "uploaded")

            shared_dir = "drive:HomeGridBackup/backups"
            mocked_rclone.assert_any_call(
                "copyto", archive_path, f"{shared_dir}/{device_id}_{archive_name}"
            )
            delete_targets = {
                call.args[1] for call in mocked_rclone.call_args_list
                if call.args[0] == "deletefile"
            }
            self.assertEqual(delete_targets, {
                f"{shared_dir}/{own_stale}",
                f"{shared_dir}/{own_stale}.sha256",
            })

    def test_archive_sync_is_queued_if_another_sync_is_active(self):
        with tempfile.TemporaryDirectory() as backup_dir:
            engine = SimpleNamespace(state={
                "backup_dir": backup_dir, "cloud_enabled": True,
            })
            cloud._CLOUD_SYNC_LOCK.acquire()
            try:
                with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True):
                    self.assertFalse(cloud.sync_cloud_backups(engine))
            finally:
                cloud._CLOUD_SYNC_LOCK.release()
            self.assertTrue(os.path.isfile(os.path.join(backup_dir, ".cloud-archives.pending")))

    def test_preview_sync_worker_runs_and_notifies_on_completion(self):
        completed = threading.Event()
        errors = []
        engine = SimpleNamespace(
            state={"cloud_enabled": True},
            is_running=False,
            cloud_sync_worker_lock=threading.Lock(),
            log=lambda *_args: None,
        )
        with mock.patch.object(cloud, "WINDOWS7_CLOUD_SYNC_PREVIEW", True), \
             mock.patch.object(
                 cloud, "sync_pending_cloud_data",
                 return_value={"archives": 0, "reports": 0, "total": 0},
             ) as sync:
            started = cloud.start_cloud_sync_worker(
                engine,
                force=True,
                on_complete=lambda error: (errors.append(error), completed.set()),
            )
            self.assertTrue(started)
            self.assertTrue(completed.wait(2))
        sync.assert_called_once_with(engine, force=True)
        self.assertEqual(errors, [None])


if __name__ == "__main__":
    unittest.main()
