import os
import psutil
import json

MANAGER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "manager")
PATH_TO_RUNNING_BINARIES_FILE = os.path.join(
    MANAGER_DIR, "current_running_binaries.json"
)
PATH_TO_IS_CONNECTED_FILE = os.path.join(MANAGER_DIR, "is_connected.txt")


def is_process_running_by_pid(pid, saved_start_time):
    """
    Checks if a process is still the same one we recorded.
    :param pid: Int from your JSON
    :param saved_start_time: Float from your JSON
    """
    try:
        # 1. Quick check: Is the PID even in the system table?
        if not psutil.pid_exists(pid):
            return False

        proc = psutil.Process(pid)
        current_start_time = proc.create_time()

        # 2. Compare the times.
        if abs(current_start_time - float(saved_start_time)) < 0.1:
            return True

        return False

    except:
        return False


def get_current_manager_info():
    with open(PATH_TO_RUNNING_BINARIES_FILE, "r") as f:
        data = f.read()
    if len(data) != 0:
        json_data = json.loads(data)
        return json_data.get("pid", None), json_data.get("start time", None)
    return None, None


def is_manager_running(update=False):
    """
    Checks if a manager is already running.
    If not, and update=True, records the current process as the active manager.
    """
    try:
        running_pid, start_time = get_current_manager_info()

        # 1. Check if the recorded process is actually alive
        if running_pid is not None and start_time is not None:
            if is_process_running_by_pid(running_pid, start_time):
                return True

        # 2. If we reach here, no manager is running.
        # If update is requested, save the current process info.
        if update:
            curr_proc = psutil.Process(os.getpid())
            data = {"pid": curr_proc.pid, "start time": curr_proc.create_time()}
            with open(PATH_TO_RUNNING_BINARIES_FILE, "w") as f:
                json.dump(data, f)

        return False

    except (psutil.Error, IOError, ValueError) as e:
        # Log error if needed: print(f"Error checking manager status: {e}")
        return False


def kill_manager():
    pid, _ = get_current_manager_info()

    if pid is None:
        print("No manager process recorded.")
        return

    try:
        if is_manager_running():
            parent = psutil.Process(pid)

            # 1. Get all children (sniffers, binaries, etc.)
            # recursive=True finds grandchildren as well
            children = parent.children(recursive=True)

            print(f"Terminating manager (PID {pid}) and {len(children)} children...")

            # 2. Terminate children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            # 3. Terminate the parent
            parent.terminate()

            # 4. Wait for everything to die
            gone, alive = psutil.wait_procs(children + [parent], timeout=3)

            # 5. If anything is still alive, use the "nuclear" option
            for survivor in alive:
                print(f"Force killing stubborn process: {survivor.pid}")
                survivor.kill()

            print("Manager and all sub-processes stopped.")
        else:
            print("Manager not running.")

    except psutil.NoSuchProcess:
        print("Manager process already ended.")
    except Exception as e:
        print(f"Error while killing manager: {e}")


def save_is_connected(is_connected):
    with open(PATH_TO_IS_CONNECTED_FILE, "w") as f:
        f.write(str(is_connected))


def load_is_connected():
    with open(PATH_TO_IS_CONNECTED_FILE, "r") as f:
        return f.read(5) == "True"
    return False
