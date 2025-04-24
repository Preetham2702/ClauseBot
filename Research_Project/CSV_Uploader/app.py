from flask import Flask, render_template, request, redirect, url_for, session
import os
import pandas as pd
import psycopg2
from werkzeug.utils import secure_filename
from matplotlib import cm
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

hostname = 'localhost'
database = 'postgres'
username = 'postgres'
pwd = 'Srinivas@123'
port_id = '5340'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    cleared_files = session.get('cleared_files', [])
    visible_files = [f for f in files if f not in cleared_files and f.endswith('.csv')]
    return render_template('index.html', files=visible_files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files[]' not in request.files:
        return "No file part", 400
    files = request.files.getlist('files[]')
    for file in files:
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cleared_files = session.get('cleared_files', [])
            if filename in cleared_files:
                cleared_files.remove(filename)
                session['cleared_files'] = cleared_files
    return redirect(url_for('index'))

@app.route('/clear_selected', methods=['POST'])
def clear_selected():
    selected_files = request.form.getlist('selected_files')
    cleared_files = session.get('cleared_files', [])
    for filename in selected_files:
        if filename not in cleared_files:
            cleared_files.append(filename)
    session['cleared_files'] = cleared_files
    return redirect(url_for('index'))

@app.route('/preview/<filename>')
def preview(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        with open(filepath, 'r') as file:
            content = file.read().replace('\r', '').strip()
        lines = content.split('\n')
        image_lines = []
        for line in lines:
            parts = [p.strip() for p in line.split(';') if p.strip() != '']
            if all(part.replace('.', '', 1).isdigit() for part in parts):
                image_lines.append([float(p) for p in parts])
        max_len = max(len(row) for row in image_lines)
        image_lines = [row for row in image_lines if len(row) == max_len]
        df = pd.DataFrame(image_lines)
        df.columns = [f"col{i+1}" for i in range(max_len)]
        df_html = df.to_html(classes='table table-bordered', index=False, escape=False)
        return render_template('preview.html', tables=[df_html], filename=filename, show_button=True)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/view/<filename>')
def view_image_data(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        with open(filepath, 'r') as file:
            content = file.read().replace('\r', '').strip()
        lines = content.split('\n')
        image_lines = []
        for line in lines:
            parts = [p.strip() for p in line.split(';') if p.strip() != '']
            if all(part.replace('.', '', 1).isdigit() for part in parts):
                image_lines.append([float(p) for p in parts])
        max_len = max(len(row) for row in image_lines)
        image_lines = [row for row in image_lines if len(row) == max_len]
        df = pd.DataFrame(image_lines)
        df.columns = [f"col{i+1}" for i in range(max_len)]
        norm = plt.Normalize(df.values.min(), df.values.max())
        df_html = '<table class="table table-bordered" style="border-collapse: collapse;">'
        for i, row in df.iterrows():
            df_html += '<tr>'
            cells = row if i % 2 == 0 else row[::-1]
            for j, val in enumerate(cells):
                color_val = norm(val)
                color = cm.rainbow(color_val)
                hex_color = '#%02x%02x%02x' % tuple(int(255 * c) for c in color[:3])
                df_html += f'<td style="background-color: {hex_color}; color: black; text-align: center;">{val:.2f}</td>'
            df_html += '</tr>'
        df_html += '</table>'
        return render_template('preview.html', tables=[df_html], filename=filename, show_button=False)
    except Exception as e:
        return f"Error: {e}", 500
## only image data 
@app.route('/update/<filename>', methods=['POST'])
def update(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        with open(filepath, 'r') as file:
            content = file.read().replace('\r', '').strip()
        lines = content.split('\n')
        image_lines = []
        for line in lines:
            parts = [p.strip() for p in line.split(';') if p.strip() != '']
            if all(part.replace('.', '', 1).isdigit() for part in parts):
                image_lines.append(parts)
        max_len = max(len(row) for row in image_lines)
        image_lines = [row for row in image_lines if len(row) == max_len]
        df = pd.DataFrame(image_lines)
        conn = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cur = conn.cursor()
        table_name = os.path.splitext(secure_filename(filename))[0].lower().replace(" ", "_")
        cur.execute(f'DROP TABLE IF EXISTS "{table_name}";')
        columns = ', '.join([f'"col{i}" TEXT' for i in range(df.shape[1])])
        cur.execute(f'CREATE TABLE "{table_name}" ({columns});')
        for _, row in df.iterrows():
            values = "', '".join(str(v).replace("'", "''") for v in row)
            cur.execute(f"INSERT INTO \"{table_name}\" VALUES ('{values}');")
        conn.commit()
        message = f"'{filename}' uploaded to database successfully!"
        df.columns = [f"col{i+1}" for i in range(df.shape[1])]
        df_html = df.to_html(classes='table table-bordered', index=False, escape=False)
        return render_template('preview.html', tables=[df_html], filename=filename, message=message)
    except Exception as e:
        return f"Error uploading to database: {e}", 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    cleared_files = session.get('cleared_files', [])
    if filename not in cleared_files:
        cleared_files.append(filename)
        session['cleared_files'] = cleared_files
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)