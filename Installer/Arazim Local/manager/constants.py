"""
Docstring for manager.constants
This module contains constant values used throughout the manager directory.
"""

# Constant values for get_network_properties.py
WINDOWS = "Windows"
LINUX = "Linux"
MACOS = "Darwin"
DECODE_FORMAT = "utf-8"
NETWORK_NOT_FOUND = "Network name not found (or not on Wi-Fi)"
SUBNET_NOT_FOUND = "Subnet mask not found for the given interface."
DEFAULT_GATEWAY = "0.0.0.0"
LOOPBACK_IP = "127.0.0.1"
NOT_CONNECTED_MESSAGE = "Not connected to any network"
NETWORK_NAME_KEY = "network_name"
MY_IP_KEY = "my_ip"
ROUTER_IP_KEY = "router_ip"
DEFAULT_DEVICE_KEY = "default_device"
SUBNET_MASK_KEY = "subnet_mask"


# Constant values for run_binary.py
G2_NETWORK_NAME = "Building_G2"
PROCESSES_ALREADY_RUNNING_MESSAGE = "Required processes are already running. Exiting."
KEYBOARD_INTERRUPT_MESSAGE = "Execution interrupted by user."
# format: binary_path: [arg1, arg2, ...]
BINARIES_TO_EXEC = {
    "python": ["manager\\test.py"]
}  # TODO: replace with actual binary paths and their args
TIME_INTERVAL_BETWEEN_CHECKS = 2  # time interval in seconds
PATH_TO_RUNNING_BINARIES_FILE = "C:\\Users\\samel\\arazim_practice\\networks_exercises\\arazim_local\\arazim_local\\Installer\\Arazim Local\\manager\\current_running_binaries.json"
PID_KEY = "pid"
START_TIME_KEY = "start_time"
