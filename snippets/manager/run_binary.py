from subprocess import Popen
from scapy.all import *
import time
from get_network_properties import get_network_properties

# constants
G2_NETWORK_NAME = "Building_G2"


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
    if is_sniffer_running(process):
        return process
    else:
        # server = find_server() (for later use)
        process = Popen([binary_path] + [str(arg) for arg in args])
        return process


def not_in_g2_logic(process):
    if process is not None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except:
            process.kill()  # give some time to terminate
    return None


def main(binary_path, args, t):
    process = None
    while True:
        try:
            network_properties = get_network_properties()
            if network_properties["network_name"] == G2_NETWORK_NAME:
                process = in_g2_logic(binary_path, args, process)
            else:
                process = not_in_g2_logic(process)
            time.sleep(t)
        except KeyboardInterrupt:
            print("Execution interrupted by user.")
            if process:
                process.kill()
            break
        except Exception as ex:
            print(f"An error occurred: {ex}")


if __name__ == "__main__":
    binary_path = "python"  # replace with actual binary path
    # process = Popen([binary_path])
    args = ["snippets\\manager\\test.py"]  # replace with actual arguments if needed
    t = 2  # time interval in seconds
    main(binary_path, args, t)
