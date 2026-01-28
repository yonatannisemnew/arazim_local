import subprocess

def remove_subnet_from_loopback():
    cmd = (
        "for i in {1..254}; do "
        "sudo ifconfig lo0 -alias 127.16.164.$i 2>/dev/null; "
        "sudo ifconfig lo0 -alias 127.16.165.$i 2>/dev/null; "
        "done"
    )
    subprocess.run(cmd, shell=True, check=True)

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