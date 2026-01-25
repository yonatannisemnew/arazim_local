import json
import os


def initialize_cache(ip_addresses: list[str], file_path: str) -> None:
    if os.path.exists(file_path):
        return 

    data = {ip: 0 for ip in ip_addresses}
    data["current"] = ip_addresses[0] if ip_addresses else None

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def clear_cache(file_path: str) -> None:
    if os.path.exists(file_path):
        os.remove(file_path)


def update_cache_entry(ip: str, file_path: str) -> None:
    with open(file_path, 'r') as f:
        data = json.load(f)

    if ip in data:
        data[ip] += 1
        data["current"] = ip
    else:
        data[ip] = 1
        data["current"] = ip

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def cache_to_iterator(file_path: str):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # 1. Yield 'current' first if it exists (Highest Priority)
    if "current" in data:
        yield "current"
        del data["current"]  # Remove so it isn't yielded again

    # 2. Sort the remaining items by value (Descending: highest numbers first)
    # Change reverse=False if you want the lowest numbers (least used) first
    sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)

    # 3. Yield the remaining keys
    for ip, _ in sorted_items:
        yield ip