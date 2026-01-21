import subprocess
import json
import os
import tempfile

# Path to where the batch file writes the result
result_file = os.path.join(tempfile.gettempdir(), "sniffer_result.json")

# Clean up any old file first
if os.path.exists(result_file):
    os.remove(result_file)

# Run the batch script
subprocess.run(["sniffer_start.bat"], capture_output=False)

subprocess.run(["arp_cacher.bat", "works!!!"], capture_output=False)
# Read the result file
try:
    with open(result_file, "r") as f:
        network_info = json.load(f)
    
    print(f"Success! Data loaded from file: {network_info}")
    print(f"IP: {network_info[0]}")
    print(f"Interface: {network_info[3]}")

except FileNotFoundError:
    print("Error: The batch script failed to produce a result file.")
except json.JSONDecodeError:
    print("Error: The file contained invalid JSON.")