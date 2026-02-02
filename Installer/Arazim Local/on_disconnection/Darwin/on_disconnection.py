import subprocess

def remove_subnet_from_loopback():
    print("remove")
    cmd = (
        "ifconfig lo0 | grep 'inet ' | awk '{print $2}' | grep -v '^127.0.0.1$' | "
        "xargs -n 1 -I {} sudo ifconfig lo0 -alias {}"
    )

    try:
        subprocess.run(cmd, shell=True, executable="/bin/bash")
        print("[-] Loopback interface reset (all aliases removed).")
    except Exception as e:
        print(f"[!] Error cleaning loopback: {e}")

    print("[-] Cleaning up firewall rules...")
    subprocess.run("sudo pfctl -a 'com.user.anycast' -F all 2>/dev/null", shell=True, executable="/bin/bash")
    try:
        subprocess.run("sudo pfctl -f /etc/pf.conf", shell=True, check=True)
        print("[-] Firewall defaults restored (NAT rules wiped).")
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to reload /etc/pf.conf: {e}")
def enable_rst():
    try:
        subprocess.run("sudo pfctl -f /etc/pf.conf", shell=True, check=True)
        subprocess.run("sudo pfctl -d", shell=True, stderr=subprocess.DEVNULL)
        print("[-] Firewall defaults restored and PF disabled.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to restore firewall: {e}")

if __name__ == "__main__":
    enable_rst()
    remove_subnet_from_loopback()