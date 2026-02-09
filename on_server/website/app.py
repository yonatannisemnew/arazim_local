import os
import json
import hashlib
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from printer_scheduler import schedule_task
from constants import * 

app = Flask(__name__)

app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TASKS_FOLDER'] = TASKS_FOLDER
#app.config["PREVIEW_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TASKS_FOLDER, exist_ok=True)

def allowed_file(filename):
    """ check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_file_hash(file_stream):
    """
    Calculate SHA256 of the file content to generate a unique name.
    Returns the hash as a string.
    """
    sha256_hash = hashlib.sha256()
    # Reading the file in blocks to avoid memory overload
    for byte_block in iter(lambda: file_stream.read(4096), b""):
        sha256_hash.update(byte_block)
    
    # Important: Reset the file pointer to the beginning so we can save it later
    file_stream.seek(0)
    return sha256_hash.hexdigest()

def create_task_json(file_path, file_name, fields):
    """
    Create a JSON file in the tasks folder with details about the print job.
    """    

    task_id = str(uuid.uuid4())

    task_data = {
        "task_id": task_id,
        "file_path": file_path,
        "file_name": file_name,
        "copies": 1,
    }
    
    # Add additional fields from the form
    for key, value in fields.items():
        task_data[key] = value
    
    json_filename = f"{task_id}.json"
    json_path = os.path.join(app.config['TASKS_FOLDER'], json_filename)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(task_data, f, indent=4, ensure_ascii=False)
        
    return json_path


@app.route('/scheduled_prints', methods=['GET'])
def scheduled_prints():
    """List scheduled print tasks and show copies with increment button."""
    tasks = []
    folder = app.config.get('TASKS_FOLDER', 'tasks')
    try:
        files = sorted([f for f in os.listdir(folder) if f.endswith('.json')])
    except FileNotFoundError:
        files = []
    for fname in files:
        path = os.path.join(folder, fname)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            continue
        # ensure copies exists
        data.setdefault('copies', 1)
        tasks.append(data)

    return render_template('scheduled_prints.html', tasks=tasks)


def _update_task_copies(task_id, change):
    """Helper to update copies and return the new count or None on error."""
    folder = app.config.get('TASKS_FOLDER', 'tasks')
    json_path = os.path.join(folder, f"{task_id}.json")
    
    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        
        current = int(data.get('copies', 1))
        new_total = current + change
        
        # Guard: Don't allow negative copies
        if new_total < 0:
            return current

        data['copies'] = new_total
        
        with open(json_path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=4, ensure_ascii=False)
        return new_total
    except Exception:
        return None

@app.route('/task/<task_id>/increment', methods=['POST'])
def increment_copies(task_id):
    result = _update_task_copies(task_id, 1)
    if result is None:
        flash('Task not found or error updating.', 'error')
    return redirect(url_for('scheduled_prints'))

@app.route('/task/<task_id>/decrement', methods=['POST'])
def decrement_copies(task_id):
    result = _update_task_copies(task_id, -1)
    if result is None:
        flash('Task not found or error updating.', 'error')
    return redirect(url_for('scheduled_prints'))

# --- Routes ---

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/add_file', methods=['GET'])
def show_add_file_form():
    """ only show the form to upload a file and set a print time"""
    return render_template('index.html', print_options=PRINT_OPTIONS)


# Add this near your other os.makedirs calls
os.makedirs(app.config.get('PREVIEW_FOLDER', 'previews'), exist_ok=True)

@app.route('/previews', methods=['GET'])
def list_previews():
    """List previews based on active tasks to show original filenames."""
    preview_data = []
    tasks_folder = app.config.get('TASKS_FOLDER', 'tasks')
    
    try:
        # Get all task files
        task_files = [f for f in os.listdir(tasks_folder) if f.endswith('.json')]
    except FileNotFoundError:
        task_files = []

    for fname in task_files:
        path = os.path.join(tasks_folder, fname)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            
            # Extract the stored info
            # data['file_path'] is the absolute path to the UUID-named file
            # data['file_name'] is the original name (e.g., "my_homework.pdf")
            full_path = data.get('file_path')
            original_name = data.get('file_name', 'Unknown File')
            
            if full_path and os.path.exists(full_path):
                preview_data.append({
                    'original_name': original_name,
                    'internal_filename': os.path.basename(full_path),
                    'task_id': data.get('task_id')
                })
        except Exception:
            continue

    return render_template('previews.html', previews=preview_data)

@app.route('/previews/view/<filename>', methods=['GET'])
def view_preview(filename):
    """Serves the file for viewing using the internal UUID filename."""
    # We use UPLOAD_FOLDER here because that's where the PDF actually lives
    folder = os.path.abspath(app.config.get('UPLOAD_FOLDER'))
    return send_from_directory(folder, filename, as_attachment=False)

@app.route('/previews/download/<filename>/<path:display_name>', methods=['GET'])
def download_preview(filename, display_name):
    """Serves the file for download with the original filename."""
    folder = os.path.abspath(app.config.get('UPLOAD_FOLDER'))
    return send_from_directory(
        folder, 
        filename, 
        as_attachment=True, 
        download_name=display_name # This restores the original name for the user
    )

@app.route('/add_file', methods=['POST'])
def handle_file_upload():
    file = request.files.get('document')

    # Parse dynamic options
    try:
        print_options = parse_print_options(request.form, PRINT_OPTIONS)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('show_add_file_form'))

    # Validate file
    if not file or file.filename == '':
        flash('Error: No file provided', 'error')
        return redirect(url_for('show_add_file_form'))

    if not allowed_file(file.filename):
        flash('Error: Invalid file extension', 'error')
        return redirect(url_for('show_add_file_form'))

    # Save file, calculate hash, etc.
    file_hash = calculate_file_hash(file)
    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4()}.{ext}"
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    if not os.path.exists(full_path):
        file.save(full_path)

    # Create JSON task
    task_file_path = create_task_json(full_path, secure_filename(file.filename), print_options)

    schedule_task(task_file_path, print_options)

    flash(f"Success! Task scheduled for {print_options['appointment_time']}", 'success')
    return redirect(url_for('show_add_file_form'))


def parse_print_options(form, schema):
    """
    Parse form data according to PRINT_OPTIONS schema.
    Returns a dictionary of all options ready to save in JSON.

    form: request.form (Flask POST data)
    schema: PRINT_OPTIONS dictionary
    """
    parsed = {}

    for name, opt in schema.items():
        # Boolean options: checkbox returns "on" if checked, missing if unchecked
        if opt["type"] == "bool":
            parsed[name] = name in form

        # Datetime option
        elif opt["type"] == "datetime":
            value = form.get(name)
            if opt.get("required") and not value:
                raise ValueError(f"Missing required field: {name}")
            parsed[name] = value  # ISO string, e.g., "2026-02-08T14:30"

        # Select option
        elif opt["type"] == "select":
            value = form.get(name, opt.get("default"))
            if value not in opt["choices"]:
                raise ValueError(f"Invalid value for {name}: {value}")
            parsed[name] = value

        # Text option
        elif opt["type"] == "text":
            parsed[name] = form.get(name, opt.get("default", ""))

        # number option
        elif opt["type"] == "number":
            value = form.get(name, opt.get("default"))
            try:
                parsed[name] = int(value)
            except (ValueError, TypeError):
                parsed[name] = opt.get("default", 1)

        else:
            # Unknown type fallback
            parsed[name] = form.get(name, opt.get("default"))

    return parsed

    

if __name__ == '__main__':
    app.run(debug=True, port=80)