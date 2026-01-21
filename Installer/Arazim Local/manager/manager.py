from subprocess import Popen
import psutil
from scapy.all import *
import time

from get_network_properties import get_network_properties
import os
import json
from constants import *

LAST_CONNECTION_TO_G2 = 0



def is_connection_new():
    global LAST_CONNECTION_TO_G2
    current_time  = time.time()
    if (current_time - LAST_CONNECTION_TO_G2) > (TIME_INTERVAL_BETWEEN_CHECKS * 2 - 1):
        LAST_CONNECTION_TO_G2 = current_time
        return True
    LAST_CONNECTION_TO_G2 = current_time
    return False

def is_disconnected_now_from_G2():
    global LAST_CONNECTION_TO_G2
    current_time  = time.time()
    return (current_time - LAST_CONNECTION_TO_G2) < (TIME_INTERVAL_BETWEEN_CHECKS * 2 - 1)


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
    with open(PATH_TO_RUNNING_BINARIES_FILE, 'r') as f:
        data = f.read()
    if len(data) != 0:
        json_data = json.loads(data)
        running_pid = json_data.get("pid", [])
        start_time = json_data.get("start time", [])
        #print(running_pid, start_time)
        if is_process_running_by_pid(running_pid, start_time):
            return True

    with open(PATH_TO_RUNNING_BINARIES_FILE, "w") as f:
        json.dump({"pid": pid, "start time": psutil.Process(pid).create_time()}, f)

    return False


def is_subprocess_running(process):
    """
    Docstring for is_sniffer_running

    :param process: the current running process
    :return: True if there is a process running, False otherwise
    """
    #print(process)
    if process is None:
        return False
    if process.poll() is not None:
        return_code = process.returncode
        print(f"subprocess ended with return code: {return_code}")
        return False
    return True


def find_server():
    return "Server_placeholder"  # placeholder for actual implementation


def watchdog(
    binary_args, process
):  # the args Omri' and Cyber (Anaki) need are my_ip, router_ip, default_device, subnet_mask
    """
    Docstring for in_g2_logic

    :param binary_path: the path to the binary that needs to be run
    :param args: arguments to be passed to the binary
    :param process: the current running process
    :return: the process if it is running, otherwise starts a new process and returns it
    """
    if is_subprocess_running(process):
        return process
    else:
        process = Popen(binary_args)
        return process


def kill_process(process):
    """
    Docstring for kill_process
    :param process: the current running process
    :return: None
    """
    if process is not None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except:
            process.kill()  # give some time to terminate
    return None


def once_first_connected():
    server = find_server()


def once_first_disconnected():
    print("Disconnecting from G2 network...")  # placeholder for actual implementation

    
def main(backround_binaries_to_run, t, network_name=G2_NETWORK_NAME):
    if is_manager_running():
        print(PROCESSES_ALREADY_RUNNING_MESSAGE)
        return
    processes = [None for _ in backround_binaries_to_run]
    while True:
        try:
            network_properties = get_network_properties()
            if network_properties[NETWORK_NAME_KEY] == G2_NETWORK_NAME:
                ###always running binaries
                if is_connection_new():
                    once_first_connected()
                for i, binary_args in enumerate(backround_binaries_to_run):
                    processes[i] = watchdog(binary_args, processes[i])
                    print(
                        f"Process {i}: PID {processes[i].pid if processes[i] else 'None'}"
                    )
            else:
                #not in G2 logic
                if is_disconnected_now_from_G2():
                    once_first_disconnected()


                #kill all running sniffers
                for i, process in enumerate(processes):
                    processes[i] = kill_process(process)
            time.sleep(t)
        except KeyboardInterrupt:
            print(KEYBOARD_INTERRUPT_MESSAGE)
            for process in processes:
                if process:
                    process.kill()
            break
        except Exception as ex:
            print(f"An error occurred: {ex}")


if __name__ == "__main__":
    main(BACKGROUND_BINARIES_TO_RUN, TIME_INTERVAL_BETWEEN_CHECKS)
