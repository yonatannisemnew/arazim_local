import subprocess
from scapy.all import *
import time


def run_binary(binary_path, args, t):
    try:
        command = [f"./{binary_path}"] + [str(arg) for arg in args]
        while True:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error executing {binary_path}: {result.stderr}")
            time.sleep(t)
    except KeyboardInterrupt:
        print("Execution interrupted by user.")
    except Exception as ex:
        print(f"An error occurred: {ex}")
