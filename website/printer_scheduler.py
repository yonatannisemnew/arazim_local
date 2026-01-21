import os
from datetime import datetime

SEND_ADDR = "WE NEED TO CREATE AN EMAIL FOR THIS!!!" # TODO: create email
SEND_PASS = "EMAIL PASSWORD HERE"  # TODO: email password
RECV_ADDR = "RECEIVER EMAIL HERE"  # TODO: receiver email

PRINT_PATH = "/path/to/website/printing_script.py"  # TODO: set correct path to printing_script.py

def add_printing_job(filename, time):
    cron = CronTab(user=True)
    cron.new(command=f'python3 {PRINT_PATH} {filename}', comment='printing_job').setall(time)
    print(filename)
    print(datetime.fromisoformat(time))
    pass  # add cron job and stuff




def handle_schecduled_prints(scheduled_time):
    pass  # check cron jobs and send emails
