import subprocess
disable_recv = "sudo iptables -A OUTPUT -p tcp --tcp-flags RST RST -d 127.16.164.0/23 -j DROP"
disable_send = "sudo iptables -A OUTPUT -s 127.16.164.0/23 -p tcp --tcp-flags RST RST -j DROP"
subprocess.run(disable_recv, shell=True, check=True)
subprocess.run(disable_send, shell=True, check=True)