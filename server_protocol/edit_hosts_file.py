import sys


def find_path():
    # --- Linux Logic ---
    if sys.platform.startswith("linux"):
        return "/etc/hosts"
    if sys.platform.startswith("darwin"):
        return "/etc/hosts"
    if sys.platform == "win32":
        return "C:\\Windows\\System32\\drivers\\etc\\hosts"


def replace_domain_ip(domain: str, ip: str, file_path: str):
    # 1. Read all lines into a list
    with open(file_path, "r") as f:
        lines = f.readlines()
        f.close()

    # 2. Reopen the file in write mode (this clears the file)
    with open(file_path, "w") as f:
        for line in lines:
            if domain not in line:
                f.write(line)
        f.write(f"{ip} {domain}\n")
        f.close()


def insert_to_hosts(domain: str, ip: str):
    replace_domain_ip(domain, ip, find_path())


# if __name__ == '__main__':
#     insert_to_hosts("arazimloc.com", "146.190.62.39")
