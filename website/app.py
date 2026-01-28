import os
import json
import hashlib
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from printer_scheduler import schedule_task

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load config from environment variables
app.secret_key = os.getenv('SECRET_KEY', 'default_dev_key')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
TASKS_FOLDER = os.getenv('TASKS_FOLDER', 'tasks')
PREVIEW_FOLDER = os.getenv('PREVIEW_FOLDER', 'previews')
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'pdf').split(','))

# Add more fields here as needed in the future
TASK_FIELDS = [
    "appointment_time",
    "example_field",
]

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TASKS_FOLDER'] = TASKS_FOLDER
app.config['PREVIEW_FOLDER'] = PREVIEW_FOLDER
# folder creation if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TASKS_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)

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
        
    return task_id


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


@app.route('/task/<task_id>/increment', methods=['POST'])
def increment_copies(task_id):
    """Increase the copies count for a given task JSON by 1."""
    folder = app.config.get('TASKS_FOLDER', 'tasks')
    json_path = os.path.join(folder, f"{task_id}.json")
    if not os.path.exists(json_path):
        flash('Task not found.', 'error')
        return redirect(url_for('scheduled_prints'))

    try:
        with open(json_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception:
        flash('Could not read task file.', 'error')
        return redirect(url_for('scheduled_prints'))

    data['copies'] = int(data.get('copies', 1)) + 1

    try:
        with open(json_path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=4, ensure_ascii=False)
        flash(f"Copies increased to {data['copies']}", 'success')
    except Exception:
        flash('Could not update task file.', 'error')

    return redirect(url_for('scheduled_prints'))

# --- Routes ---

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/add_file', methods=['GET'])
def show_add_file_form():
    """ only show the form to upload a file and set a print time"""
    return render_template('index.html')


@app.route('/previews', methods=['GET'])
def list_previews():
    """Show a page that lists preview files with view/download links."""
    folder = app.config.get('PREVIEW_FOLDER', 'previews')
    try:
        files = sorted(os.listdir(folder))
    except FileNotFoundError:
        files = []
    return render_template('previews.html', files=files)


@app.route('/previews/view/<path:filename>', methods=['GET'])
def view_preview(filename):
    folder = app.config.get('PREVIEW_FOLDER', 'previews')
    try:
        return send_from_directory(folder, filename, as_attachment=False)
    except FileNotFoundError:
        abort(404)


@app.route('/previews/download/<path:filename>', methods=['GET'])
def download_preview(filename):
    folder = app.config.get('PREVIEW_FOLDER', 'previews')
    try:
        return send_from_directory(folder, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/add_file', methods=['POST'])
def handle_file_upload():
    """Process the form: save file and create a task JSON"""
    fields = {field: request.form.get(field, None) for field in TASK_FIELDS}
    file = request.files.get('document')

    # Basic validation
    if not fields.get('appointment_time') or not file or file.filename == '':
        flash('Error: You must provide both a Date/Time and a file.', 'error')
        return redirect(url_for('show_add_file_form'))

    if file and allowed_file(file.filename):
        # 1. file hash calculation and new filename creation
        file_hash = calculate_file_hash(file)
        new_filename = f"{file_hash}." + secure_filename(file.filename).rsplit('.', 1)[1].lower()
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        preview_path = os.path.join(app.config['PREVIEW_FOLDER'], secure_filename(file.filename))
        
        # 2. file saving (only if it doesn't already exist, saves space)
        if not os.path.exists(full_path):
            file.save(full_path)
            file.seek(0)  # Reset file pointer for preview generation if needed

        if not os.path.exists(preview_path):
            file.save(preview_path)  # Save a copy for preview purposes

        # 3. create task JSON
        task_id = create_task_json(full_path, secure_filename(file.filename), fields)

        # 4. schedule the task
        appointment_dt = datetime.fromisoformat(fields['appointment_time'])
        schedule_task(appointment_dt, os.path.join(os.getcwd(), 'printing_script.py'), task_id)
        
        flash(f'Success! Task created for {fields["appointment_time"]}. File saved as {secure_filename(file.filename)}', 'success')
        return redirect(url_for('show_add_file_form'))
    else:
        flash('Error: Invalid file extension.', 'error')
        return redirect(url_for('show_add_file_form'))
    

if __name__ == '__main__':
    app.run(debug=True)