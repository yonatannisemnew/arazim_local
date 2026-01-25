import subprocess

def add_subnet_to_loopback():
    cmd = ("for i in {1..254}; do\n"
    "sudo ifconfig lo0 alias 127.16.164.$i up\n"
    "sudo ifconfig lo0 alias 127.16.165.$i up\n"
    "done\n")
    subprocess.run(cmd, shell=True, check=True)

ANCHOR = "com.custom.rst_block"
SUBNET = "127.16.164.0/23"
def disable_rst():
    # FIX 1: Added explicit newline characters (\n) so pfctl sees two distinct lines.
    rules = (f"block drop out proto tcp from any to {SUBNET} flags R/R\n"
             f"block drop out proto tcp from {SUBNET} to any flags R/R\n")
    
    # FIX 2 & 3:
    # -e : Enable the packet filter (if not already active)
    # -f - : Read rules from standard input (stdin)
    # We removed '-a' so these rules are applied to the main ruleset immediately.
    cmd = f"printf '{rules}' | sudo pfctl -e -f -"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("[-] Firewall rules loaded and PF enabled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to load firewall rules: {e}")

if __name__ == "__main__":
    add_subnet_to_loopback()
    disable_rst()