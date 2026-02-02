import os
import psutil
import json

PATH_TO_RUNNING_BINARIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manager", "current_running_binaries.json")

def is_process_running_by_pid(pid, start_time=""):
    """
    Docstring for check_pid
    :param pid: process id
    :param start_time: process start time
    :return: True if the process with the given pid and start_time is running, False otherwise
    """
    return psutil.pid_exists(pid) and psutil.Process(pid).create_time() == start_time


def is_manager_running():
    """
    Docstring for is_manager_running

    :return: True if there is a manager running, False otherwise
    This function checks if there are any running managers recorded in the
    "current_running_binaries.json" file. If any of the recorded PIDs are
    currently active, it returns True. If none are active, it updates the file
    with the current process's PID and time of execution and returns False.
    """
    pid = os.getpid()
    with open(PATH_TO_RUNNING_BINARIES_FILE, "r") as f:
        data = f.read()
    if len(data) != 0:
        json_data = json.loads(data)
        running_pid = json_data.get("pid", [])
        start_time = json_data.get("start time", [])
        # print(running_pid, start_time)
        if is_process_running_by_pid(running_pid, start_time):
            return True

    with open(PATH_TO_RUNNING_BINARIES_FILE, "w") as f:
        json.dump({"pid": pid, "start time": psutil.Process(pid).create_time()}, f)

    return False