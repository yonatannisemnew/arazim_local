import os
import psutil
import json

MANAGER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manager")
PATH_TO_RUNNING_BINARIES_FILE = os.path.join(MANAGER_DIR, "current_running_binaries.json")
PATH_TO_IS_CONNECTED_FILE = os.path.join(MANAGER_DIR, "is_connected.txt")

def is_process_running_by_pid(pid, start_time=""):
    """
    Docstring for check_pid
    :param pid: process id
    :param start_time: process start time
    :return: True if the process with the given pid and start_time is running, False otherwise
    """
    return psutil.pid_exists(pid) and psutil.Process(pid).create_time() == start_time

def get_current_manager_info():
    with open(PATH_TO_RUNNING_BINARIES_FILE, "r") as f:
        data = f.read()
    if len(data) != 0:
        json_data = json.loads(data)
        return json_data.get("pid", None), json_data.get("start time", None)
    return None, None

def is_manager_running(update=False):
    """
    Docstring for is_manager_running

    :return: True if there is a manager running, False otherwise
    This function checks if there are any running managers recorded in the
    "current_running_binaries.json" file. If any of the recorded PIDs are
    currently active, it returns True. If none are active, it updates the file
    with the current process's PID and time of execution and returns False.
    """
    running_pid, start_time = get_current_manager_info()
    if running_pid is not None and start_time is not None:
        if is_process_running_by_pid(running_pid, start_time):
            return True
    else:
        return False
    if update:
        with open(PATH_TO_RUNNING_BINARIES_FILE, "w") as f:
            pid = os.getpid()
            json.dump({"pid": pid, "start time": psutil.Process(pid).create_time()}, f)

    return False

def kill_manager():
    pid = get_current_manager_info()[0]
    try:
        p = psutil.Process(pid)
        p.terminate()
    except Exception as e:
        print("manager utils error", e)

def save_is_connected(is_connected):
    with open(PATH_TO_IS_CONNECTED_FILE, "w") as f:
        f.write(str(is_connected))

def load_is_connected():
    with open(PATH_TO_IS_CONNECTED_FILE, "r") as f:
        return f.read(5) == "True"
    return False

