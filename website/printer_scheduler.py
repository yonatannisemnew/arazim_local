import os
import subprocess
import shlex
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SEND_ADDR = os.getenv("SEND_ADDR", "WE NEED TO CREATE AN EMAIL FOR THIS!!!") # TODO: create email
SEND_PASS = os.getenv("SEND_PASS", "EMAIL PASSWORD HERE")  # TODO: email password
RECV_ADDR = os.getenv("RECV_ADDR", "RECEIVER EMAIL HERE")  # TODO: receiver email

TASKS_FOLDER = os.getenv('TASKS_FOLDER', 'tasks')

def schedule_task(date: datetime, file_to_exec_path: str, file_to_exec_args: str):
    formatted_date = date.strftime("%H:%M %Y-%m-%d")
    safe_path = shlex.quote(file_to_exec_path)
    safe_args = shlex.quote(os.path.abspath(os.path.join(TASKS_FOLDER, file_to_exec_args + ".json")))
    
    command_to_run = f"python3 {safe_path} {safe_args}"

    print(f"Scheduling task at {formatted_date} with command: {command_to_run}")
    
    subprocess.run(["at", formatted_date], input=command_to_run, text=True)
