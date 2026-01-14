import os
import subprocess
import shlex
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SEND_ADDR = os.getenv("SEND_ADDR", "WE NEED TO CREATE AN EMAIL FOR THIS!!!") # TODO: create email
SEND_PASS = os.getenv("SEND_PASS", "EMAIL PASSWORD HERE")  # TODO: email password
RECV_ADDR = os.getenv("RECV_ADDR", "RECEIVER EMAIL HERE")  # TODO: receiver email

PRINT_PATH = os.getenv("PRINT_PATH", "/path/to/website/printing_script.py")  # TODO: set correct path to printing_script.py


def schedule_task(date: datetime, file_to_exec_path: str, file_to_exec_args: str):
    formatted_date = date.strftime("%H:%M %Y-%m-%d")
    safe_path = shlex.quote(file_to_exec_path)
    safe_args = shlex.quote(file_to_exec_args)
    
    command_to_run = f"python3 {safe_path} {safe_args}"
    
    subprocess.run(["at", formatted_date], input=command_to_run, text=True)
