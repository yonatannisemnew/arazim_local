import os
import sys
import shutil
import subprocess
import platform
import ctypes
from constants import *


def is_admin():
    try:
        # Check for Windows Admin
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        # Check for Linux/Mac Root (UID 0)
        return os.geteuid() == 0


def run_as_admin():
    if is_admin():
        # Already admin, nothing to do
        return

    print("Requesting administrative privileges...")

    if platform.system() == "Windows":
        # Re-run the script with the 'runas' verb (triggers UAC)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    else:
        # Re-run with sudo for Linux/Mac
        subprocess.check_call(["sudo", sys.executable] + sys.argv)

    sys.exit()


def get_platform():
    os_name = platform.system()
    is_64bit = sys.maxsize > 2**32

    if os_name == "Windows":
        return WINDOWS_X64 if is_64bit else WINDOWS_X86
    elif os_name == "Darwin":
        return MAC_OS
    elif os_name == "Linux":
        return LINUX_OS
    else:
        return UNKNOWN_OS


def set_program_dir(platform):
    if platform not in OS_TO_PROGRAM_FILES:
        print("not supported platform")
        exit(1)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    arazim_local_dir = os.path.join(current_dir, "Arazim Local")

    # --- THIS IS THE CRITICAL CHANGE ---
    # We take "C:\Program Files" and turn it into "C:\Program Files\Arazim Local"
    target_dir = os.path.join(OS_TO_PROGRAM_FILES[platform], "Arazim Local")
    # -----------------------------------

    try:
        print(f"Source: {arazim_local_dir}")
        print(f"Target: {target_dir}")

        # Now it will create the "Arazim Local" folder inside Program Files
        shutil.copytree(arazim_local_dir, target_dir, dirs_exist_ok=True)
        print("Copy Successful!")
    except Exception as e:
        print(f"unable to copy ARAZIM LOCAL dir!!! Error: {e}")
        exit(-1)


def add_scheduling(platform_type):
    """
    Directly schedules the manager script to run every X minutes
    without external batch or shell scripts.
    """
    # 1. Resolve the permanent path to the manager
    permanent_dir = os.path.join(OS_TO_PROGRAM_FILES[platform_type], "Arazim Local")
    manager_path = os.path.join(permanent_dir, "manager", "manager.py")

    # Use the current python executable to ensure we use the same environment
    python_exe = sys.executable
    interval = str(DURATION)  # Assuming DURATION is 15

    print(f"Scheduling {manager_path} to run every {interval} minutes...")

    try:
        if platform_type in [WINDOWS_X64, WINDOWS_X86]:
            # --- WINDOWS: schtasks ---
            # /f = force (overwrite), /rl highest = Admin privileges
            # We use triple quotes to handle spaces in Program Files
            cmd = [
                "schtasks",
                "/create",
                "/tn",
                "ArazimLocalTask",
                "/tr",
                f'"{python_exe}" "{manager_path}"',
                "/sc",
                "minute",
                "/mo",
                interval,
                "/rl",
                "highest",
                "/f",
            ]
            subprocess.run(cmd, check=True)

        elif platform_type in [LINUX_OS, MAC_OS]:
            # --- LINUX/MAC: Crontab ---
            # Cron format: */15 * * * * command
            cron_job = f"*/{interval} * * * * {python_exe} {manager_path}\n"

            # Get current crontab, append new job, and reload
            # This avoids overwriting existing user cron jobs
            current_cron = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True
            ).stdout

            if manager_path not in current_cron:
                new_cron = current_cron + cron_job
                process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
                process.communicate(input=new_cron.encode())
            else:
                print("Task already exists in crontab.")

        print("Scheduling successfully established.")

    except Exception as e:
        print(f"CRITICAL ERROR: Could not create scheduled task. {e}")
        sys.exit(1)


def main():
    run_as_admin()
    platform = get_platform()
    if platform == UNKNOWN_OS:
        print("Unsupported operating system.")
        exit(1)
    print(f"Detected platform: {platform}")
    set_program_dir(platform)
    add_scheduling(platform)
    permanent_dir = os.path.join(OS_TO_PROGRAM_FILES[platform], "Arazim Local")
    manager_path = os.path.join(permanent_dir, "manager", "manager.py")
    subprocess.Popen([sys.executable, manager_path])


if __name__ == "__main__":
    main()
