import os
import pwd
from constants import LINUX_OS

def add_linux():
    # Who actually invoked sudo?
    real_user = os.environ.get("SUDO_USER")

    if not real_user:
        raise RuntimeError("This script must be run with sudo")

    user_info = pwd.getpwnam(real_user)
    home_dir = user_info.pw_dir

    desktop_dir = os.path.join(home_dir, "Desktop")
    desktop_file = os.path.join(desktop_dir, "my_app.desktop")

    desktop_content = """[Desktop Entry]
    Type=Application
    Name=My App
    Exec=sudo nohup python3 "/usr/bin/Arazim_Local/dashboard/dashboard.py" >/dev/null 2>&1 & 
    Terminal=true
    """

    with open(desktop_file, "w") as f:
        f.write(desktop_content)

    # Fix ownership + permissions
    os.chown(desktop_file, user_info.pw_uid, user_info.pw_gid)
    os.chmod(desktop_file, 0o755)

def add_windows():
    pass

def add_desktop_icon(platform):
    if platform == LINUX_OS:
        add_linux()
    else:
        add_windows()