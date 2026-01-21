from subprocess import Popen
import psutil
from scapy.all import *
import time

from get_network_properties import get_network_properties
import os
import json
from constants import *


def is_process_running(pid, start_time=""):
    """
    Docstring for check_pid
    :param pid: process id
    :param start_time: process start time
    :return: True if the process with the given pid and start_time is running, False otherwise
    """
    return psutil.pid_exists(pid) and psutil.Process(pid).create_time() == start_time


def check_running_processes():
    """
    Docstring for check_running_processes

    :return: True if there is a process running, False otherwise
    This function checks if there are any running processes recorded in the
    "current_running_binaries.json" file. If any of the recorded PIDs are
    currently active, it returns True. If none are active, it updates the file
    with the current process's PID and time of execution and returns False.
    """
    pid = os.getpid()
    with open(PATH_TO_RUNNING_BINARIES_FILE) as f:
        data = f.read()
    if len(data) != 0:
        json_data = json.loads(data)
        running_pid = json_data.get("pid", [])
        start_time = json_data.get("start time", [])
        print(running_pid, start_time)
        if is_process_running(running_pid, start_time):
            return True

    with open(PATH_TO_RUNNING_BINARIES_FILE, "w") as f:
        json.dump({"pid": pid, "start time": psutil.Process(pid).create_time()}, f)

    return False


def is_sniffer_running(process):
    """
    Docstring for is_sniffer_running

    :param process: the current running process
    :return: True if there is a process running, False otherwise
    """
    print(process)
    if process is None:
        return False
    if process.poll() is not None:
        return_code = process.returncode
        print(f"Sniffer process ended with return code: {return_code}")
        return False
    return True


def find_server():
    return "Server_placeholder"  # placeholder for actual implementation


def in_g2_logic(
    binary_path, args, process
):  # the args Omri' and Cyber (Anaki) need are my_ip, router_ip, default_device, subnet_mask
    """
    Docstring for in_g2_logic

    :param binary_path: the path to the binary that needs to be run
    :param args: arguments to be passed to the binary
    :param process: the current running process
    :return: the process if it is running, otherwise starts a new process and returns it
    """
    if is_sniffer_running(process):
        return process
    else:
        # server = find_server() (for later use)
        process = Popen([binary_path] + [str(arg) for arg in args])
        return process


def not_in_g2_logic(process):
    """
    Docstring for not_in_g2_logic
    :param process: the current running process
    :return: None after terminating the process if it is running
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


def dummy_main(binaries_to_execute, t, network_name=G2_NETWORK_NAME):
    if check_running_processes():
        print(PROCESSES_ALREADY_RUNNING_MESSAGE)
        return
    input()


def main(binaries_to_execute, t, network_name=G2_NETWORK_NAME):
    if check_running_processes():
        print(PROCESSES_ALREADY_RUNNING_MESSAGE)
        return
    processes = [None for _ in binaries_to_execute.keys()]
    while True:
        try:
            network_properties = get_network_properties()
            if network_properties[NETWORK_NAME_KEY] == G2_NETWORK_NAME:
                i = 0
                for binary_path, binary_args in binaries_to_execute:
                    processes[i] = in_g2_logic(binary_path, binary_args, processes[i])
                    print(
                        f"Process {i}: PID {processes[i].pid if processes[i] else 'None'}"
                    )
                    i += 1
            else:
                for i, process in enumerate(processes):
                    processes[i] = not_in_g2_logic(process)
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
    binaries_to_execute = BINARIES_TO_EXEC.keys()
    t = TIME_INTERVAL_BETWEEN_CHECKS
    main(binaries_to_execute, t)
