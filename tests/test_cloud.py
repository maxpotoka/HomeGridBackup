_A2='core.gfs.compute_gfs_plan'
_A1='rate limited'
_A0='stage_started'
_z='.jsonl'
_y='HomeGridBackup.exe'
_x='executable'
_w='{"reason":"RATE_LIMIT_EXCEEDED","status":"rateLimitExceeded"}'
_v='creationflags'
_u='password'
_t='uploaded'
_s='.cloud-archives.pending'
_r='2025-01-02T10:00:00+00:00'
_q='server_duration_sec'
_p='download_speed_mbps'
_o='system_info'
_n='files_count'
_m='Windows 7 64-bit'
_l='operation-1'
_k='system-rclone'
_j='create'
_i='config'
_h='summary'
_g='platform'
_f='drive:HomeGridBackup/archive.zip'
_e='archive.zip'
_d=False
_c=None
_b='event'
_a='operation_id'
_Z='timestamp'
_Y='2025-01-02.jsonl'
_X='.pending'
_W='user'
_V='koofr'
_U='\n'
_T='_run'
_S='list_rclone_remotes'
_R='reports'
_Q='_rclone'
_P='secret'
_O='HomeGridBackup'
_N='cloud_path'
_M='_rclone_executable'
_L='cloud_remote'
_K='cloud_enabled'
_J='copyto'
_I='backup_dir'
_H='w'
_G='utf-8'
_F='mega'
_E='rclone'
_D='drive'
_C='device_id'
_B='WINDOWS7_CLOUD_SYNC_PREVIEW'
_A=True
import json,os,tempfile,threading,unittest
from types import SimpleNamespace
from unittest import mock
from core import cloud
class RcloneExecutableTests(unittest.TestCase):
	def test_windows7_preview_exposes_only_mega_and_koofr(A):
		with mock.patch.object(cloud,_B,_A):A.assertEqual([A[1]for A in cloud.available_rclone_providers()],[_F,_V])
		with mock.patch.object(cloud,_B,_d):A.assertEqual([A[1]for A in cloud.available_rclone_providers()],[_D,'onedrive','dropbox','box','pcloud',_F,_V])
	def test_preview_credential_setup_creates_mega_and_koofr_without_prompts(A):
		E='mycloud';C='user@example.com';F=mock.Mock(returncode=0,stdout='',stderr='');G=(_F,[_W,C,'pass',_P]),(_V,[_W,C,_u,_P,'provider',_V])
		for(B,H)in G:
			with A.subTest(backend=B),mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_S,return_value=[]),mock.patch.object(cloud,_M,return_value=_E),mock.patch.object(cloud,_T,return_value=F)as D:cloud.create_rclone_remote(E,B,C,_P)
			A.assertEqual(D.call_args.args[0],[_E,_i,_j,E,B,*H,'--obscure','--non-interactive']);A.assertEqual(D.call_args.args[1],60)
	def test_preview_credential_setup_rejects_providers_other_than_mega_and_koofr(A):
		with mock.patch.object(cloud,_B,_A):
			with A.assertRaisesRegex(ValueError,'Unsupported cloud provider'):cloud.create_rclone_remote(_D,_D,_W,_u)
	def test_preview_credential_setup_redacts_password_from_errors(A):
		B=mock.Mock(returncode=1,stdout='',stderr='failed secret')
		with mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_S,return_value=[]),mock.patch.object(cloud,_M,return_value=_E),mock.patch.object(cloud,_T,return_value=B):
			with A.assertRaisesRegex(RuntimeError,'failed \\[redacted\\]'):cloud.create_rclone_remote(_F,_F,_W,_P)
	def test_preview_credential_setup_redacts_password_from_process_errors(A):
		B=cloud.subprocess.TimeoutExpired([_E,_P],60)
		with mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_S,return_value=[]),mock.patch.object(cloud,_M,return_value=_E),mock.patch.object(cloud,_T,side_effect=B):
			with A.assertRaises(RuntimeError)as C:cloud.create_rclone_remote(_F,_F,_W,_P)
		A.assertNotIn(_P,str(C.exception))
	def test_cloud_queue_translation_keeps_format_placeholders(A):from core.i18n import tr;B='Черга синхронізації: архіви {archives}, звіти {reports}';A.assertEqual(tr(B,'uk').format(archives=2,reports=3),'Черга синхронізації: архіви 2, звіти 3');A.assertEqual(tr(B,'en').format(archives=2,reports=3),'Cloud sync queue: archives 2, reports 3')
	def test_cloud_settings_reject_a_blank_folder_or_remote_root(A):
		for B in('',' / ','///'):
			with A.subTest(path=B),A.assertRaisesRegex(ValueError,'корінь'):cloud.validate_cloud_settings(_D,B)
	def test_cloud_settings_accept_a_relative_folder(A):A.assertEqual(cloud.validate_cloud_settings(_D,'/HomeGridBackup/backups/'),'HomeGridBackup/backups')
	def test_run_disables_stdin_and_console_window(A):
		B=mock.Mock(returncode=0,stdout='',stderr='')
		with mock.patch.object(cloud,'_NO_WINDOW',134217728),mock.patch.object(cloud.subprocess,'run',return_value=B)as C:D=cloud._run([_E,'listremotes'],15)
		A.assertIs(D,B);A.assertIs(C.call_args.kwargs['stdin'],cloud.subprocess.DEVNULL);A.assertEqual(C.call_args.kwargs[_v],134217728)
	def test_rclone_uses_retries_and_a_request_rate_limit(A):
		with mock.patch.object(cloud,_M,return_value=_E),mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_T,return_value=mock.Mock(returncode=0,stdout='',stderr=''))as B:cloud._rclone(_J,_e,_f,timeout=60)
		A.assertEqual(B.call_args.args,([_E,'--retries','3','--low-level-retries','10','--tpslimit','2','--stats','0',_J,_e,_f],60))
	def test_non_preview_rclone_preserves_provider_error(A):
		B=mock.Mock(returncode=1,stdout='',stderr=_w)
		with mock.patch.object(cloud,_M,return_value=_E),mock.patch.object(cloud,_B,_d),mock.patch.object(cloud,_T,return_value=B):
			with A.assertRaises(RuntimeError):cloud._rclone(_J,_e,_f)
	def test_preview_shortens_rate_limit_errors(A):
		B=mock.Mock(returncode=1,stdout='',stderr=_w)
		with mock.patch.object(cloud,_M,return_value=_E),mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_T,return_value=B):
			with A.assertRaisesRegex(RuntimeError,'personal OAuth client'):cloud._rclone(_J,_e,_f)
	def test_prefers_bundled_rclone(C):
		D='rclone.exe'if os.name=='nt'else _E
		with tempfile.TemporaryDirectory()as A:
			B=os.path.join(A,D)
			with open(B,'wb')as E:E.write(b'rclone')
			with mock.patch.object(cloud.sys,_x,os.path.join(A,_y)),mock.patch.object(cloud.shutil,'which',return_value=_k):C.assertEqual(cloud._rclone_executable(),B)
	def test_falls_back_to_path_when_no_bundled_rclone_exists(A):
		with tempfile.TemporaryDirectory()as B:
			with mock.patch.object(cloud.sys,_x,os.path.join(B,_y)),mock.patch.object(cloud.shutil,'which',return_value=_k):A.assertEqual(cloud._rclone_executable(),_k)
	def test_setup_starts_interactive_rclone_without_a_console_window(A):
		D='mydrive';C=mock.Mock()
		with mock.patch.object(cloud,_S,return_value=[]),mock.patch.object(cloud,_M,return_value=_E),mock.patch.object(cloud.subprocess,'Popen',return_value=C)as B:A.assertIs(cloud.start_rclone_remote_setup(D,_D),C)
		A.assertEqual(B.call_args.args[0],[_E,_i,_j,D,_D]);A.assertIs(B.call_args.kwargs['stdin'],cloud.subprocess.PIPE);A.assertIs(B.call_args.kwargs['stderr'],cloud.subprocess.STDOUT);A.assertEqual(B.call_args.kwargs[_v],cloud._NO_WINDOW)
	def test_mega_uses_the_supported_rclone_backend_and_remote_path(A):
		C=mock.Mock();B={_L:_F,_N:_O,_C:'a'*32}
		with mock.patch.object(cloud,_S,return_value=[]),mock.patch.object(cloud,_M,return_value=_E),mock.patch.object(cloud.subprocess,'Popen',return_value=C)as D:A.assertIs(cloud.start_rclone_remote_setup(_F,_F),C)
		A.assertEqual(D.call_args.args[0],[_E,_i,_j,_F,_F]);A.assertEqual(cloud._remote_path(B,'backups',B[_C]),'mega:HomeGridBackup/backups/{}'.format(B[_C]))
	def test_setup_rejects_invalid_remote_and_backend(A):
		B='valid'
		with A.assertRaises(ValueError):cloud.start_rclone_remote_setup('../bad',_D)
		with A.assertRaises(ValueError):cloud.start_rclone_remote_setup(B,'unsupported')
		with mock.patch.object(cloud,_S,return_value=[B]):
			with A.assertRaises(ValueError):cloud.start_rclone_remote_setup(B,_D)
	def test_remote_test_falls_back_to_listing_when_about_is_unsupported(B):
		A='mydrive:'
		with mock.patch.object(cloud,_Q,side_effect=[RuntimeError('no about'),''])as C:cloud.test_rclone_remote(A)
		B.assertEqual(C.call_args_list,[mock.call('about',A),mock.call('lsd',A,'--max-depth','1')])
	def test_operation_reports_are_local_and_include_comparison_metadata(A):
		F='rclone v1.76.0';C='a'*32;D={_I:tempfile.mkdtemp(),_C:C,'all_time_cnt':4,_K:_d};G=SimpleNamespace(state=D)
		try:
			with mock.patch.object(cloud,'_rclone_version',return_value=F):cloud.record_operation_event(G,_l,'stage_completed',stage='archive_download',archive='backup.zip',size_mb=12.5,size_bytes=13107200,duration_sec=2.34567,files_count=9,archive_sequence=5,speed_mbps=5.34,download_speed_mbps=7.3,download_duration_sec=29.9,server_duration_sec=219.6,system_info=_m,summary='v2.25 | Windows 7 64-bit | download 7.3 MB/s (29.9 s)')
			H=os.path.join(D[_I],_R,C);E=os.path.join(H,cloud.datetime.now().strftime('%Y-%m-%d')+_z)
			with open(E,encoding=_G)as I:B=json.loads(I.readline())
			A.assertEqual(B[_C],C);A.assertEqual(B['archives_total'],4);A.assertEqual(B['archive_sequence'],5);A.assertEqual(B[_n],9);A.assertEqual(B['duration_ms'],2346);A.assertEqual(B['rclone_version'],F);A.assertTrue(B[_g]);A.assertEqual(B[_o],_m);A.assertEqual(B[_p],7.3);A.assertEqual(B[_q],219.6);A.assertIn('download 7.3 MB/s',B[_h]);A.assertTrue(os.path.isfile(E+_X))
		finally:import shutil as J;J.rmtree(D[_I])
	def test_sync_reports_uploads_local_reports_and_clears_pending_marker(F):
		A='b'*32
		with tempfile.TemporaryDirectory()as C:
			D=os.path.join(C,_R,A);os.makedirs(D);B=os.path.join(D,_Y)
			with open(B,_H,encoding=_G)as G:G.write('{}\n')
			E=B+_X;open(E,_H).close();H=SimpleNamespace(state={_I:C,_C:A,_K:_A,_L:_D,_N:_O})
			with mock.patch.object(cloud,_Q)as I:cloud.sync_cloud_reports(H)
			I.assert_called_once_with(_J,B,f"drive:HomeGridBackup/operations/{A}/2025-01-02.jsonl");F.assertFalse(os.path.exists(E))
	def test_preview_sync_merges_all_devices_into_one_plain_text_root_log(A):
		E='success';D='platform_version';C='1'*32;F='2'*32
		with tempfile.TemporaryDirectory()as G:
			H=os.path.join(G,_R,C);os.makedirs(H);I=os.path.join(H,_Y);L={_Z:_r,_C:C,_a:'operation-win7',_b:E,_g:'Windows',D:'7',_o:_m,_h:'download 7.3 MB/s (29.9 s) | server 219.6 s | total 260.9 s | files 4',_p:7.3,_q:219.6,_n:4};M={_Z:'2025-01-02T11:00:00+00:00',_C:F,_a:'operation-linux',_b:E,_g:'Linux',D:'6.8',_o:'Linux 64-bit',_h:'download 6.2 MB/s | server 180 s | total 190 s | files 3',_p:6.2,_q:180,_n:3};N={_Z:'2025-01-02T12:00:00+00:00',_C:'3'*32,_a:'operation-macos',_b:E,_g:'Darwin',D:'24.0',_h:'download 5 MB/s | server 120 s | total 130 s | files 2'}
			with open(I,_H,encoding=_G)as O:O.write(json.dumps(L)+_U)
			J=I+_X;open(J,_H).close();P=SimpleNamespace(state={_I:G,_C:C,_K:_A,_L:_D,_N:_O});K=[];B=[]
			def Q(*A):
				G='copy'
				if A[0]==G and A[1]=='drive:HomeGridBackup/.HomeGridBackup-sources':
					with open(os.path.join(A[2],F+_z),_H,encoding=_G)as D:D.write(json.dumps(M)+_U)
				elif A[0]==G and A[1]=='drive:HomeGridBackup/operations':
					E=os.path.join(A[2],'legacy','2025-01-02');os.makedirs(E)
					with open(os.path.join(E,_Y),_H,encoding=_G)as D:D.write(json.dumps(N)+_U)
				elif A[0]==_J and A[2]==f"drive:HomeGridBackup/.HomeGridBackup-sources/{C}.jsonl":
					with open(A[1],encoding=_G)as D:K.extend(json.loads(A)for A in D)
				elif A[0]==_J and A[2]=='drive:HomeGridBackup/HomeGridBackup.log':
					with open(A[1],encoding=_G)as H:B.extend(H.readlines())
			with mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_Q,side_effect=Q):A.assertTrue(cloud.sync_cloud_reports(P))
			A.assertEqual({A[_C]for A in K},{C});A.assertEqual(len(B),3);A.assertTrue(any('OS=Windows 7'in A for A in B));A.assertTrue(any('OS=Linux 6.8'in A for A in B));A.assertTrue(any('OS=Darwin 24.0'in A for A in B));A.assertTrue(any('server_duration_sec=219.6'in A for A in B));A.assertTrue(any('server_duration_sec=180'in A for A in B));A.assertFalse(any(A.lstrip().startswith('{')for A in B));A.assertFalse(os.path.exists(J))
	def test_failed_report_upload_keeps_the_pending_marker_for_retry(B):
		A='c'*32
		with tempfile.TemporaryDirectory()as C:
			D=os.path.join(C,_R,A);os.makedirs(D);E=os.path.join(D,_Y)
			with open(E,_H,encoding=_G)as G:G.write(json.dumps({_Z:_r,_C:A,_a:_l,_b:_A0})+_U)
			F=E+_X;open(F,_H).close();H=SimpleNamespace(state={_I:C,_C:A,_K:_A,_L:_D,_N:_O})
			with mock.patch.object(cloud,_Q,side_effect=cloud.CloudRateLimitError(_A1)):
				with B.assertRaises(cloud.CloudRateLimitError):cloud.sync_cloud_reports(H)
			B.assertTrue(os.path.isfile(F))
	def test_report_sync_preserves_a_new_append_during_upload(C):
		A='d'*32
		with tempfile.TemporaryDirectory()as D:
			E=os.path.join(D,_R,A);os.makedirs(E);F=os.path.join(E,_Y)
			with open(F,_H,encoding=_G)as H:H.write(json.dumps({_Z:_r,_C:A,_a:_l,_b:_A0})+_U)
			B=F+_X;open(B,_H).close();G=SimpleNamespace(state={_I:D,_C:A,_K:_A,_L:_D,_N:_O})
			def I(*C):
				if C[0]==_J and C[2]==f"drive:HomeGridBackup/.HomeGridBackup-sources/{A}.jsonl":
					with open(B,'a',encoding=_G):0
			with mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_Q,side_effect=I):cloud.sync_cloud_reports(G)
			C.assertTrue(os.path.isfile(B))
			with mock.patch.object(cloud,_B,_A):C.assertEqual(cloud.cloud_sync_queue_state(G)[_R],1)
	def test_archive_sync_failure_leaves_a_persistent_queue_marker(A):
		with tempfile.TemporaryDirectory()as B:
			C=os.path.join(B,'backup_DAILY_test.zip')
			with open(C,'wb')as E:E.write(b'archive')
			D=SimpleNamespace(state={_I:B,_C:'e'*32,_K:_A,_L:_D,_N:_O})
			with mock.patch(_A2,return_value=(_c,[{'path':C}],_c)),mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_Q,side_effect=cloud.CloudRateLimitError(_A1)):
				with A.assertRaises(cloud.CloudRateLimitError):cloud.sync_cloud_backups(D)
			A.assertTrue(os.path.isfile(os.path.join(B,_s)))
			with mock.patch.object(cloud,_B,_A):A.assertEqual(cloud.cloud_sync_queue_state(D)['archives'],1);A.assertEqual(cloud.cloud_archive_sync_status(D,os.path.basename(C)),'error')
	def test_cloud_archive_status_tracks_queue_and_target_remote(C):
		E='unknown'
		with tempfile.TemporaryDirectory()as D:
			A=SimpleNamespace(state={_I:D,_K:_A,_L:_F,_N:_O});B='homegrid_backup_DAILY_test.zip'
			with mock.patch.object(cloud,_B,_A):C.assertEqual(cloud.cloud_archive_sync_status(A,B),E);open(os.path.join(D,_s),_H).close();C.assertEqual(cloud.cloud_archive_sync_status(A,B),'queued');cloud._write_cloud_archive_status(A,B,_t);C.assertEqual(cloud.cloud_archive_sync_status(A,B),_t);A.state[_L]=_V;C.assertEqual(cloud.cloud_archive_sync_status(A,B),E)
	def test_preview_archives_share_one_folder_without_cross_device_pruning(B):
		M='drive:HomeGridBackup/backups';L='_homegrid_backup_DAILY_old.zip';F='.sha256';D='a'*32;N='b'*32;C='homegrid_backup_DAILY_2025-01-02.zip';E=D+L;H=N+L
		with tempfile.TemporaryDirectory()as I:
			A=os.path.join(I,C)
			with open(A,'wb')as O:O.write(b'archive')
			with open(A+F,_H,encoding=_G)as P:P.write('{}  {}\n'.format('a'*64,C))
			J=SimpleNamespace(state={_I:I,_C:D,_K:_A,_L:_D,_N:_O})
			def Q(*A):
				if A[0]=='lsf':B.assertEqual(A[2],M);return _U.join((E,E+F,H,H+F))
				if A[0]==_J and A[1].endswith(F)and'.tmp'not in A[1]:
					with open(A[1],encoding=_G)as G:B.assertEqual(G.read(),f"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  {D}_{C}\n")
			with mock.patch(_A2,return_value=(_c,[{'path':A}],[])),mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,_Q,side_effect=Q)as K:B.assertTrue(cloud.sync_cloud_backups(J,prune=_A))
			B.assertEqual(cloud.cloud_archive_sync_status(J,C),_t);G=M;K.assert_any_call(_J,A,f"{G}/{D}_{C}");R={A.args[1]for A in K.call_args_list if A.args[0]=='deletefile'};B.assertEqual(R,{f"{G}/{E}",f"{G}/{E}.sha256"})
	def test_archive_sync_is_queued_if_another_sync_is_active(A):
		with tempfile.TemporaryDirectory()as B:
			C=SimpleNamespace(state={_I:B,_K:_A});cloud._CLOUD_SYNC_LOCK.acquire()
			try:
				with mock.patch.object(cloud,_B,_A):A.assertFalse(cloud.sync_cloud_backups(C))
			finally:cloud._CLOUD_SYNC_LOCK.release()
			A.assertTrue(os.path.isfile(os.path.join(B,_s)))
	def test_preview_sync_worker_runs_and_notifies_on_completion(A):
		B=threading.Event();C=[];D=SimpleNamespace(state={_K:_A},is_running=_d,cloud_sync_worker_lock=threading.Lock(),log=lambda*A:_c)
		with mock.patch.object(cloud,_B,_A),mock.patch.object(cloud,'sync_pending_cloud_data',return_value={'archives':0,_R:0,'total':0})as E:F=cloud.start_cloud_sync_worker(D,force=_A,on_complete=lambda error:(C.append(error),B.set()));A.assertTrue(F);A.assertTrue(B.wait(2))
		E.assert_called_once_with(D,force=_A);A.assertEqual(C,[_c])
if __name__=='__main__':unittest.main()
