import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PRINT_OPTIONS = {
    "appointment_time": {
        "label": "Select Date & Time",
        "type": "datetime",
        "required": True,
    },
    "color": {
        "label": "Color printing",
        "type": "bool",
        "default": True,
    },
    "duplex": {
        "label": "Double sided",
        "type": "bool",
        "default": False,
    },
    "copies": {
        "label": "Number of copies",
        "type": "number",  # We'll add handling for 'number' in the template/parser
        "default": 1,
        "min": 1,
        "max": 3
    },
}

FLASK_APP="app.py"
FLASK_DEBUG=1

# Security
SECRET_KEY="YqHgHsvr9ZhIiBKGBlUgl1Ew"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)  # One level up

# Paths (now in parent_dir/auto_printer/...)
AUTO_PRINTER_DIR = os.path.join(PARENT_DIR, "auto_printer")
UPLOAD_FOLDER = os.path.join(AUTO_PRINTER_DIR, "uploads")
TASKS_FOLDER = os.path.join(AUTO_PRINTER_DIR, "tasks")
PRINT_SCRIPT_PATH = os.path.join(AUTO_PRINTER_DIR, "print_tasks.py")

# Allowed Extensions
ALLOWED_EXTENSIONS = "pdf"