import platform
from constants import *
import sys

def get_platform():
    os_name = platform.system()
    is_64bit = sys.maxsize > 2**32

    if os_name == "Windows":
        return WINDOWS_X64 if is_64bit else WINDOWS_X86
    elif os_name == "Darwin":
        return MAC_OS
    elif os_name == "Linux":
        return LINUX_OS
    else:
        return UNKNOWN_OS