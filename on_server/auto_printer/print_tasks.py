#!/usr/bin/env python3

import sys
import json
import time
from pathlib import Path
from print_utils import reset_printer, print_pdf, log_message

# --- Configuration ---
PRINTER_NAME = "HP_DeskJet_5200_series_FAD6D7"
CLEANUP_DELAY = 5 

def delete_file(file_path):
    """Safely removes a file from the system."""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            log_message(f"Deleted: {path.name}")
    except Exception as e:
        log_message(f"Failed to delete {file_path}: {e}")

def load_task_data(task_file_path):
    """
    Reads and parses the JSON task file. 
    Raises ValueError if JSON is invalid.
    """
    path = Path(task_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Task file not found: {task_file_path}")
    
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in: {task_file_path}")

def process_print_job(task_file_path):
    """Orchestrates the loading, printing, and cleanup of a job."""
    try:
        # 1. Load and Validate Data
        try:
            task_data = load_task_data(task_file_path)
        except (ValueError, json.JSONDecodeError) as e:
            log_message(f"Critical Error: {e}. Deleting corrupted task file.")
            delete_file(task_file_path)
            return

        pdf_path = task_data.get("file_path")
        if not pdf_path:
            log_message(f"Error: Missing 'file_path' in {task_file_path}. Deleting task.")
            delete_file(task_file_path)
            return

        # Extract printing parameters
        color = task_data.get("color", False)
        double_sided = task_data.get("duplex", True)
        copies = task_data.get("copies", 1)  # Default to 1 if not specified

        # 2. Execute Print
        log_message(f"Starting print job for: {pdf_path} ({copies} copies)")
        print_pdf(
            PRINTER_NAME, 
            pdf_path, 
            color, 
            double_sided,
            copies  # Passing the copies argument here
        )

        # 3. Wait and Cleanup
        log_message(f"Waiting {CLEANUP_DELAY}s for spooler...")
        time.sleep(CLEANUP_DELAY)
        
        delete_file(pdf_path)
        delete_file(task_file_path)
        
        log_message("Print job and cleanup completed successfully.")

    except Exception as e:
        log_message(f"Unexpected error during job: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: ./print_task.py <task_file_path>")
        sys.exit(1)

    reset_printer(PRINTER_NAME)
    process_print_job(sys.argv[1])

if __name__ == "__main__":
    main()