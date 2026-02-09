import subprocess
from pathlib import Path
import sys
import json
from datetime import datetime

# Assuming LOG_FILE is defined globally or imported from your config
from pathlib import Path
CURRENT_DIR = Path(__file__).parent
LOG_FILE = CURRENT_DIR / "logs" / "print_task.log"

def reset_printer(printer_name: str):
    """Re-enables the printer and clears all stuck jobs from the queue."""
    try:
        log_message(f"Resetting printer: {printer_name}")
        
        # 1. Re-enable the printer (brings it back from 'disabled' state)
        subprocess.run(["cupsenable", printer_name], check=True)
        
        # 2. Clear all pending/stuck jobs to prevent repeat crashes
        subprocess.run(["cancel", "-a", printer_name], check=True)
        
        log_message("Printer re-enabled and queue cleared.")
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to reset printer: {e}")

def print_pdf(printer_name: str, pdf_path: str, color: bool, double_sided: bool, copies: int = 1):
    """Prints a PDF with specified color, duplex, and copy count settings."""
    # Before printing, ensure the printer is actually enabled
    reset_printer(printer_name)
    
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Initialize the lp command with destination and number of copies
    # -n <num> is the standard flag for copies in CUPS
    cmd = ["lp", "-d", printer_name, "-n", str(copies)]

    # Optimized flags for HP DeskJets
    if not color:
        cmd += ["-o", "print-color-mode=monochrome"]
    else:
        cmd += ["-o", "print-color-mode=color"]
    
    cmd += ["-o", "sides=two-sided-long-edge" if double_sided else "sides=one-sided"]
    
    # Add the file path as the final argument
    cmd.append(str(pdf))

    log_message(f"Running print command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def log_message(message: str):
    """Append message to log file with timestamp, and print to stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    try:
        # Ensure log directory exists before writing
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"[LOGGING ERROR] {e}")
    print(log_entry)