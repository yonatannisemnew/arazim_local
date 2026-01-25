1. protocol 
- args: subnet, interface
- first, check if we have the server IP, validate it is the server IP
    - check in server_ip_address.json
    - send validation ICMP packet
    - if returns correctly, exit and return
    - else continue
- if not, find it - send unicast messages to all members of the subnet, whoever responds "correctly" is the servers
    - for ip in subnet, send validation ICMP, if someone returns correctly, it's them
    - update server_ip_address.json
    - return their IP


- 