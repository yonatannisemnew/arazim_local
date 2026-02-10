import shutil
import time
import os
import sys
PARENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.append(os.path.join(PARENT_DIR, "utils"))
from manager_utils import kill_manager, is_manager_running
from add_desktop_icon import get_desktop_icon_path


def remove_desktop_icon():
    icon_path = get_desktop_icon_path()
    os.remove(icon_path)

def uninstall_project():
    kill_manager()
    remove_desktop_icon()
    while is_manager_running():
        time.sleep(0.1) #wait for manager to stop running
    shutil.rmtree(os.path.normpath(PARENT_DIR))

if __name__ == "__main__":
    uninstall_project()