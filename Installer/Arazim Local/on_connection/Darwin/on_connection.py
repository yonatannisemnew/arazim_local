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
    rules = (f"block drop out proto tcp from any to {SUBNET} flags R/R"
            f"block drop out proto tcp from {SUBNET} to any flags R/R")
    cmd = f"printf '{rules}' | sudo pfctl -a {ANCHOR} -f -"
    
    subprocess.run(cmd, shell=True, check=True)

if __name__ == "__main__":
    add_subnet_to_loopback()
    disable_rst()