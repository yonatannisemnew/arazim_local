import os
import sys
import shutil
import subprocess
import platform
import ctypes

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
TARGET = "Target"
SCHEDULERS = "Schedulers"
SRC_MANAGER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(os.path.join("Arazim Local", "manager")))
)
OS_TO_PROGRAM_FILES_DICT = {
    WINDOWS_X64: PROGRAM_FILES_X64,
    WINDOWS_X86: PROGRAM_FILES_X86,
    MAC_OS: PROGRAM_FILES_MAC,
    LINUX_OS: PROGRAM_FILES_LINUX,
}
RUN_SCRIPT_LINUX = "/bin/bash"
OS_TO_INSTALLER_DICT = {
    WINDOWS_X64: "installer_windows_x64.bat",
    WINDOWS_X86: "installer_windows_x86.bat",
    MAC_OS: "installer_macos.sh",
    LINUX_OS: "installer_linux.sh",
}

OS_TO_SCHEDULER_DICT = {
    WINDOWS_X64: "schedule_windows_x64.bat",
    WINDOWS_X86: "schedule_windows_x86.bat",
    MAC_OS: "schedule_macos.sh",
    LINUX_OS: "schedule_linux.sh",
}

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


def main():
    run_as_admin()
    platform = get_platform()
    if platform == UNKNOWN_OS or platform not in OS_TO_INSTALLER_DICT:
        print("Unsupported operating system.")
        return
    print(f"Detected platform: {platform}")
    installer_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        TARGET,
        OS_TO_INSTALLER_DICT[platform],
    )

    scheduler_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        SCHEDULERS,
        OS_TO_SCHEDULER_DICT[platform],
    )
    if platform in [MAC_OS, LINUX_OS]:
        subprocess.run(["/bin/bash", installer_path])
        subprocess.run(["/bin/bash", scheduler_path])
    else:
        subprocess.run([installer_path], shell=True)
        subprocess.run([scheduler_path], shell=True)

if __name__ == "__main__":
    main()
