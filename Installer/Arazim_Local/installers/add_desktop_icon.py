import os
import sys
from constants import *
from utils import get_platform
import pwd

def get_desktop_icon_path(platform=get_platform()):
    if platform == LINUX_OS:
        real_user = os.environ.get("SUDO_USER")
        if not real_user:
            raise RuntimeError("This script must be run with sudo")

        user_info = pwd.getpwnam(real_user)
        home_dir = user_info.pw_dir

        desktop_dir = os.path.join(home_dir, "Desktop")
        return os.path.join(desktop_dir, "my_app.desktop")
    elif platform in [WINDOWS_X64, WINDOWS_X86]:
        home_dir = os.path.expanduser("~")
        desktop_dir = os.path.join(home_dir, "Desktop")
        return os.path.join(desktop_dir, "ARAZIM_LOCAL.bat")
    
def add_linux(dashboard_path):
    real_user = os.environ.get("SUDO_USER")
    if not real_user:
        raise RuntimeError("This script must be run with sudo")

    user_info = pwd.getpwnam(real_user)
    home_dir = user_info.pw_dir

    desktop_dir = os.path.join(home_dir, "Desktop")
    desktop_file = os.path.join(desktop_dir, "my_app.desktop")

    python_name = sys.executable

    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=My App
Exec=sudo nohup "{python_name}" "{dashboard_path}" >/dev/null 2>&1 &
Terminal=true
Categories=Utility;
"""

    os.makedirs(desktop_dir, exist_ok=True)

    with open(desktop_file, "w") as f:
        f.write(desktop_content)

    os.chown(desktop_file, user_info.pw_uid, user_info.pw_gid)
    os.chmod(desktop_file, 0o755)


def add_windows(dashboard_path):
    home_dir = os.path.expanduser("~")
    desktop_dir = os.path.join(home_dir, "Desktop")
    bat_file = os.path.join(desktop_dir, "ARAZIM_LOCAL.bat")

    python_name = sys.executable

    bat_content = f"""@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

start "" "{python_name}" "{dashboard_path}"
"""

    os.makedirs(desktop_dir, exist_ok=True)
    with open(bat_file, "w", encoding="utf-8") as f:
        f.write(bat_content)


def add_desktop_icon(platform, project_dir):
    dashboard_path = os.path.join(project_dir, DASHBOARD_RELATIVE_TO_BASE_DIR)

    if platform == LINUX_OS:
        add_linux(dashboard_path)
    else:
        add_windows(dashboard_path)
