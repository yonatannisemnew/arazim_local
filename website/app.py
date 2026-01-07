import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from printer_scheduler import add_printing_job
app = Flask(__name__)

app.secret_key = 'supersecretkey'  # Needed for flashing messages
# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has a .pdf extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/add_file', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Retrieve data from form
        date_time = request.form.get('appointment_time')
        file = request.files.get('document')

        # 2. Server-Side Validation: Check if both fields exist
        if not date_time or not file or file.filename == '':
            flash('Error: You must provide both a Date/Time and a PDF file.', 'error')
            return redirect(request.url)

        # 3. Check if file is actually a PDF
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_path)
            
            # Success!
            flash(f'Success! PDF uploaded for {date_time}', 'success')
            add_printing_job(full_path, date_time) # TODO: change the filename to the full path
            return redirect(request.url)
        else:
            flash('Error: Only PDF files are allowed.', 'error')
            return redirect(request.url)

    return render_template('index.html')

@app.route('/',methods=['GET'])
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)