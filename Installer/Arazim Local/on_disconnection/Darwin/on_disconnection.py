import subprocess

def remove_subnet_from_loopback():
    cmd = ("for i in {1..254}; do\n"
    "sudo ifconfig lo0 -alias 127.16.164.$i\n"
    "sudo ifconfig lo0 -alias 127.16.165.$i\n"
    "done\n")
    subprocess.run(cmd, shell=True, check=True)

ANCHOR = "com.custom.rst_block"
def enable_rst():
    cmd = f"sudo pfctl -a {ANCHOR} -F all"
    subprocess.run(cmd, shell=True, check=True)

if __name__ == "__main__":
    enable_rst()
    remove_subnet_from_loopback()