import subprocess

SUBNET = "127.16.164.0/23"

def add_subnet_to_loopback():
    cmd = (
        "for i in {1..254}; do "
        "sudo ifconfig lo0 alias 127.16.164.$i; netmask 0xffffffff anycast"
        "sudo ifconfig lo0 alias 127.16.165.$i; netmask 0xffffffff anycast"
        "done"
    )
    subprocess.run(cmd, shell=True, executable="/bin/bash")

def disable_rst():
    rules = (
        f"block drop out proto tcp from any to {SUBNET} flags R/R\n"
        f"block drop out proto tcp from {SUBNET} to any flags R/R\n"
    )

    try:
        subprocess.run(f"echo '{rules}' | sudo pfctl -f -", shell=True, check=True)
        subprocess.run("sudo pfctl -e", shell=True, stderr=subprocess.DEVNULL)
        print("[-] Firewall rules loaded and PF enabled.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to load firewall rules: {e}")

if __name__ == "__main__":
    add_subnet_to_loopback()
    disable_rst()