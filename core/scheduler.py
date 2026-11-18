# ==============================================================================
# [ФАЙЛ: core/scheduler.py (v1.002 | 18.11.2026 17:14) — ПЛАНИРОВЩИК ЗАДАЧ WINDOWS (SCHTASKS)]
# ==============================================================================
import os
import re
import sys
import tempfile
import subprocess
from datetime import datetime
from core.config import SCHED_TASK_NAME

def is_compiled_app():
    if getattr(sys, "frozen", False) or ("__compiled__" in globals()):
        return True
    exe_name = os.path.basename(sys.executable or "").lower()
    return bool(exe_name.endswith(".exe") and not exe_name.startswith("python"))

def _resolve_exe_path():
    if is_compiled_app():
        argv0 = os.path.abspath(sys.argv if sys.argv else "")
        if argv0.lower().endswith(".exe") and os.path.exists(argv0):
            return argv0
    exe_p = os.path.abspath(sys.executable or "")
    if exe_p.lower().endswith(".exe") and os.path.basename(exe_p).lower() not in ("python.exe", "pythonw.exe"):
        return exe_p
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for cand_name in ("HomeGridBackup.exe", "main.exe", "homegrid_backup1.exe"):
        cand_exe = os.path.join(root_dir, cand_name)
        if os.path.exists(cand_exe):
            return cand_exe
    return os.path.join(root_dir, "HomeGridBackup.exe")

def _sync_scheduler_from_windows(st):
    if os.name != "nt":
        return
    try:
        res = subprocess.run(
            ["schtasks", "/Query", "/TN", SCHED_TASK_NAME, "/XML"],
            stdin=subprocess.DEVNULL, capture_output=True, encoding="cp866", errors="replace", timeout=6, creationflags=0x08000000
        )
        if res.returncode != 0 or not res.stdout:
            return
        xml_txt = res.stdout
        m_t = re.search(r"<StartBoundary>\d{4}-\d{2}-\d{2}T(\d{2}:\d{2})", xml_txt)
        if m_t:
            st["sched_time"] = m_t.group(1)
        m_a = re.search(r"<Arguments>(.*?)</Arguments>", xml_txt)
        if m_a:
            args = m_a.group(1).strip()
            if "--silent" in args:
                st["sched_mode"] = "--silent"
            elif "--hidden" in args:
                st["sched_mode"] = "--hidden"
        m_p = re.search(r"<Priority>(\d+)</Priority>", xml_txt)
        if m_p:
            st["sched_prio"] = int(m_p.group(1))
        st["sched_missed"] = ("<StartWhenAvailable>true</StartWhenAvailable>" in xml_txt)
        st["sched_wake"] = ("<WakeToRun>true</WakeToRun>" in xml_txt)
    except Exception:
        pass

def _manage_windows_scheduler(action, time_str="03:00", mode_flag="--hidden", start_missed=True, wake_pc=False, prio=6):
    if os.name != "nt":
        return False, "Планувальник завдань підтримується лише у Windows."
    if action == "delete":
        try:
            res = subprocess.run(
                ["schtasks", "/Delete", "/TN", SCHED_TASK_NAME, "/F"],
                stdin=subprocess.DEVNULL, capture_output=True, encoding="cp866", errors="replace", timeout=8, creationflags=0x08000000
            )
            if res.returncode == 0:
                return True, f"Завдання '{SCHED_TASK_NAME}' видалено з Планувальника."
            err_msg = (res.stderr or res.stdout or "").strip()
            return False, f"Завдання не знайдено або вже видалено ({err_msg})."
        except Exception as e:
            return False, f"Помилка видалення завдання: {e}"

    exe_path = _resolve_exe_path()
    work_dir = os.path.dirname(exe_path)
    hh, mm = (time_str.split(":") + ["03", "00"])[:2]
    start_dt = f"{datetime.now().strftime('%Y-%m-%d')}T{int(hh):02d}:{int(mm):02d}:00"
    missed_xml = "true" if start_missed else "false"
    wake_xml = "true" if wake_pc else "false"
    prio_val = max(2, min(9, int(prio)))
    sl = chr(47)
    task_ns = f"http:{sl}{sl}schemas" + f".microsoft.com{sl}windows{sl}2004{sl}02{sl}mit{sl}task"
    xml_body = (
        f'<?xml version="1.0" encoding="UTF-16"?>\n'
        f'<Task version="1.2" xmlns="{task_ns}">\n'
        f'  <RegistrationInfo><Description>HomeGrid Backup Scheduled Task</Description></RegistrationInfo>\n'
        f'  <Triggers><CalendarTrigger><StartBoundary>{start_dt}</StartBoundary><Enabled>true</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers>\n'
        f'  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>\n'
        f'  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowHardTerminate>true</AllowHardTerminate><StartWhenAvailable>{missed_xml}</StartWhenAvailable><RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable><AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled><Hidden>false</Hidden><RunOnlyIfIdle>false</RunOnlyIfIdle><WakeToRun>{wake_xml}</WakeToRun><ExecutionTimeLimit>PT2H</ExecutionTimeLimit><Priority>{prio_val}</Priority></Settings>\n'
        f'  <Actions Context="Author"><Exec><Command>{exe_path}</Command><Arguments>{mode_flag}</Arguments><WorkingDirectory>{work_dir}</WorkingDirectory></Exec></Actions>\n'
        f'</Task>'
    )

    tmp_xml = os.path.join(tempfile.gettempdir(), "hgb_sched_task.xml")
    try:
        with open(tmp_xml, "w", encoding="utf-16") as xf:
            xf.write(xml_body)
        res = subprocess.run(
            ["schtasks", "/Create", "/TN", SCHED_TASK_NAME, "/XML", tmp_xml, "/F"],
            stdin=subprocess.DEVNULL, capture_output=True, encoding="cp866", errors="replace", timeout=10, creationflags=0x08000000
        )
        if res.returncode == 0:
            return True, f"Завдання '{SCHED_TASK_NAME}' створено на {int(hh):02d}:{int(mm):02d} ({os.path.basename(exe_path)} {mode_flag})."
        err_msg = (res.stderr or res.stdout or "").strip()
        return False, f"Помилка Планувальника: {err_msg}"
    except Exception as e:
        return False, f"Збій створення завдання: {e}"
    finally:
        try:
            if os.path.exists(tmp_xml):
                os.remove(tmp_xml)
        except Exception:
            pass
