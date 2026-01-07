import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from printing import add_printing_job

app = Flask(__name__)

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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Success!
            flash(f'Success! PDF uploaded for {date_time}', 'success')
            add_printing_job(filename, date_time)
            return redirect(request.url)
        else:
            flash('Error: Only PDF files are allowed.', 'error')
            return redirect(request.url)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)