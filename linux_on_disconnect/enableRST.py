import subprocess
def enable_rst():
    enable_recv = (
        "iptables -D OUTPUT "
        "-p tcp --tcp-flags RST RST "
        "-d 127.16.164.0/23 -j DROP"
    )
    subprocess.run(enable_recv, shell=True, check=False)

    enable_send = (
        "iptables -D OUTPUT "
        "-s 127.16.164.0/23 "
        "-p tcp --tcp-flags RST RST -j DROP"
    )
    subprocess.run(enable_send, shell=True, check=False)