import os
import sys
import shutil
import subprocess

# constants
PROGRAM_FILES_X86 = os.environ.get("PROGRAMFILES(X86)") or "C:\\Program Files (x86)"
PROGRAM_FILES_X64 = os.environ.get("PROGRAMFILES") or "C:\\Program Files"
PROGRAM_FILES_MAC = "/Applications"
PROGRAM_FILES_LINUX = "/usr/bin"
WINDOWS_X64 = "windows_x64"
WINDOWS_X86 = "windows_x86"
MAC_OS = "macos"
LINUX_OS = "linux"
UNKNOWN_OS = "unknown"
SRC_MANAGER_PATH = os.path.join(os.path.dirname(os.path.abspath("manager")))
OS_TO_PROGRAM_FILES_DICT = {
    WINDOWS_X64: PROGRAM_FILES_X64,
    WINDOWS_X86: PROGRAM_FILES_X86,
    MAC_OS: PROGRAM_FILES_MAC,
    LINUX_OS: PROGRAM_FILES_LINUX,
}
REL_SCHEDULE_BAT_PATH = "schedule.bat"
REL_SCHEDULE_SH_PATH = "schedule.sh"
RUN_SCRIPT_LINUX = "/bin/bash"
OS_TO_INSTALLER_DICT = {
    WINDOWS_X64: "installer_windows_x64.bat",
    WINDOWS_X86: "installer_windows_x86.bat",
    MAC_OS: "installer_macos.sh",
    LINUX_OS: "installer_linux.sh",
}


def get_platform():
    os_name = sys.platform.system()
    is_64bit = sys.maxsize > 2**32

    if os_name == "Windows":
        return WINDOWS_X64 if is_64bit else WINDOWS_X86
    elif os_name == "Darwin":
        return MAC_OS
    elif os_name == "Linux":
        return LINUX_OS
    else:
        return UNKNOWN_OS


def main():
    platform = get_platform()
    if platform == UNKNOWN_OS or platform not in OS_TO_INSTALLER_DICT:
        print("Unsupported operating system.")
        return
    print(f"Detected platform: {platform}")
    installer_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), OS_TO_INSTALLER_DICT[platform]
    )
    subprocess.run([installer_path], shell=True)

    """
    os.makedirs(
        os.path.join(OS_TO_PROGRAM_FILES_DICT[platform], "Arazim Local"), exist_ok=True
    )
    dest_path = os.path.join(
        OS_TO_PROGRAM_FILES_DICT[platform], "Arazim Local", "manager"
    )
    shutil.copy2(SRC_MANAGER_PATH, dest_path)
    if platform == WINDOWS_X64 or platform == WINDOWS_X86:
        schedule_path = os.path.join(dest_path, REL_SCHEDULE_BAT_PATH)
        subprocess.run([schedule_path], shell=True)
    elif platform == MAC_OS or platform == LINUX_OS:
        schedule_path = os.path.join(dest_path, REL_SCHEDULE_SH_PATH)
        subprocess.run([RUN_SCRIPT_LINUX, schedule_path])"""
