import os
import sys
import platform
import ctypes


def root_check():
    # 1. Extract the OS type yourself
    this_os = platform.system()

    is_admin = False

    # 2. Perform the OS-specific check
    if this_os == "Windows":
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except AttributeError:
            is_admin = False

        if not is_admin:
            print("Requesting administrative privileges...")
            # Re-run the script with admin rights
            # 'runas' is the magic word that triggers the UAC prompt
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)  # Exit the current non-privileged process
    else:
        # For Linux/macOS
        try:
            is_admin = os.getuid() == 0
        except AttributeError:
            is_admin = False

    # 3. Handle the result
    if not is_admin:
        privilege_name = "Administrator" if this_os == "Windows" else "root/sudo"
        print(f"[-] Error: Insufficient Permissions.")
        print(
            f"[*] This script must be run as {privilege_name} to access network interfaces."
        )
        sys.exit(1)


# Usage in your code:
if __name__ == "__main__":
    root_check()
    print("[+] Permissions verified. Starting NetworkStats...")
