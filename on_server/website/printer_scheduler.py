import os
import subprocess
import shlex
from datetime import datetime
from constants import *

def schedule_task(task_file_path, print_options):
    """
    Schedule the task using 'at' based on the appointment time in print_options.
    The scheduled task will run:
        python3 /usr/bin/print_task.py <task_file_path>
    
    task_file_path: absolute path to the JSON task file
    print_options: dictionary containing at least 'appointment_time' (ISO string)
    """

    appointment_time_str = print_options.get("appointment_time")
    if not appointment_time_str:
        raise ValueError("Missing 'appointment_time' in print_options")

    appointment_dt = datetime.fromisoformat(appointment_time_str)
    formatted_date = appointment_dt.strftime("%H:%M %Y-%m-%d")

    safe_script = shlex.quote(PRINT_SCRIPT_PATH)
    safe_task_file = shlex.quote(os.path.abspath(task_file_path))

    command_to_run = f"{safe_script} {safe_task_file}"

    print(f"Scheduling task at {formatted_date} with command:\n{command_to_run}")

    # 5️⃣ Schedule the command using 'at'
    try:
        subprocess.run(["at", formatted_date], input=command_to_run, text=True, check=True)
        print("Task scheduled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error scheduling task: {e}")
