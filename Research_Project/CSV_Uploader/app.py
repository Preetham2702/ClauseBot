from flask import Flask, render_template, request, redirect, url_for, session
import os
import pandas as pd
import psycopg2
from werkzeug.utils import secure_filename
from matplotlib import cm
import matplotlib.pyplot as plt
import cv2
import numpy as np
import imageio
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5 GB

hostname = 'localhost'
database = 'postgres'
username = 'postgres'
pwd = 'Srinivas@123'
port_id = '5340'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/',methods=['GET', 'POST'])
def root():
    return redirect(url_for('select_machine'))

@app.route('/machine', methods=['GET', 'POST'])
def select_machine():
    if request.method == 'POST':
        name = request.form['machine_name']
        number = request.form['machine_number']
        material = request.form['material']

        try:
            conn = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
            cur = conn.cursor()
            # Insert machine if not already exists
            cur.execute("INSERT INTO Machine (M_ID, M_Name) VALUES (%s, %s) ON CONFLICT (M_ID) DO NOTHING", (number, name))

            # Check if the material exists
            cur.execute("SELECT 1 FROM Material WHERE Material_Type = %s", (material,))
            if cur.fetchone():
                # Update the material with machine id
                cur.execute("UPDATE Material SET M_ID = %s WHERE Material_Type = %s", (number, material))
            else:
                # Insert the material with machine id
                cur.execute("INSERT INTO Material (Material_Type, M_ID) VALUES (%s, %s)", (material, number))

            conn.commit()
        except Exception as e:
            return f"Error: {e}"
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('index'))

    conn = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
    cur = conn.cursor()
    cur.execute("SELECT Material_Type FROM Material")
    materials = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    return render_template('machine.html', materials=materials)

    
@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    if request.method == 'POST':
        material_type = request.form['material_type']
        machine_id = request.form['machine_id']

        try:
            conn = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
            cur = conn.cursor()

            # Ensure machine exists before linking
            cur.execute("SELECT 1 FROM Machine WHERE M_ID = %s", (machine_id,))
            if not cur.fetchone():
                cur.execute("INSERT INTO Machine (M_ID, M_Name) VALUES (%s, %s)", (machine_id, f"Machine_{machine_id}"))

            # Now insert the material
            cur.execute("INSERT INTO Material (Material_Type, M_ID) VALUES (%s, %s)", (material_type, machine_id))
            conn.commit()
        except Exception as e:
            return f"Error: {e}"
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('select_machine'))

    return render_template('add_material.html')


@app.route('/index', methods = ['GET'])
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    cleared_files = session.get('cleared_files', [])
    visible_files = [f for f in files if f not in cleared_files and f.endswith('.csv')]
    return render_template('index.html', files=visible_files)

@app.route('/upload', methods=['POST','GET'])
def upload_file():
    if 'files[]' not in request.files:
        return "No file part", 400
    files = request.files.getlist('files[]')
    for file in files:
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(f"{uuid4().hex}_{file.filename}")    
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
        image_lines = []
        start_data = False

        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip().replace('\r', '')

                # Start collecting after 'Image Data'
                if not start_data:
                    if "Image Data" in line:
                        start_data = True
                    continue

                # Skip empty lines
                if not line:
                    continue

                parts = [p.strip() for p in line.split(';') if p.strip()]
                if parts and all(part.replace('.', '', 1).isdigit() for part in parts):
                    image_lines.append([float(p) for p in parts])

        if not image_lines:
            return f"No valid numeric data found in {filename}", 400

        max_len = max(len(row) for row in image_lines)
        image_lines = [row for row in image_lines if len(row) == max_len]

        df = pd.DataFrame(image_lines)
        df.columns = [f"col{i+1}" for i in range(max_len)]
        df_html = df.to_html(classes='table table-bordered', index=False, escape=False)

        return render_template('preview.html', tables=[df_html], filename=filename, show_button=True)
        #return f"<pre>{image_lines}</pre>"

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

@app.route('/update/<filename>', methods=['POST'])
def update(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(filepath, 'r') as file:
            content = file.read().replace('\r', '').strip()
        lines = content.split('\n')
        image_lines = []
        for line in lines:
            if not any(char.isdigit() for char in line):
                continue
            parts = [p.strip() for p in line.split(';') if p.strip() != '']
            if all(part.replace('.', '', 1).isdigit() for part in parts):
                image_lines.append(parts)

        max_len = max(len(row) for row in image_lines)
        image_lines = [row for row in image_lines if len(row) == max_len]
        df = pd.DataFrame(image_lines).astype(float)
        df.insert(0, 'Row_Index', range(1, len(df) + 1))

        conn = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cur = conn.cursor()

        # Ensure entry in Sensor3Data table
        cur.execute("INSERT INTO Sensor3 (File_Path, Sensor_ID, Type) VALUES (%s, %s, %s) ON CONFLICT (File_Path) DO NOTHING", (filename, 1, 'IR_Camera'))

        for _, row in df.iterrows():
            values = [filename, int(row['Row_Index'])] + [float(row.get(i, None)) if pd.notna(row.get(i, None)) else None for i in df.columns[1:]]
            cur.execute("""
                INSERT INTO Sensor3_IRCamera (
                    File_Path,Row_Index,
                    Col1, Col2, Col3, Col4, Col5, Col6, Col7, Col8, Col9, Col10,
                    Col11, Col12, Col13, Col14, Col15, Col16, Col17, Col18, Col19, Col20
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)

        conn.commit()
        message = f"'{filename}' inserted into Sensor3_IRCamera successfully!"
        df.columns = [f"Col{i+1}" for i in range(df.shape[1])]
        table_html = df.to_html(classes='table table-bordered', index=False)

        return render_template('preview.html', tables=[df.to_html(classes='table table-bordered', index=False)], filename=filename, message=message)
  
        
    except Exception as e:
        return f"Error uploading to Sensor3_IRCameraData: {e}", 500
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


@app.route('/generate_video')
def generate_video():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    cleared_files = session.get('cleared_files', [])
    visible_files = [f for f in files if f not in cleared_files and f.endswith('.csv')]

    frame_list = []
    for filename in visible_files:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'r') as file:
            content = file.read().replace('\r', '').strip()
        lines = content.split('\n')
        image_lines = []
        for line in lines:
            parts = [p.strip() for p in line.split(';') if p.strip() != '']
            if all(part.replace('.', '', 1).isdigit() for part in parts):
                image_lines.append([float(p) for p in parts])
        if not image_lines:
            continue
        max_len = max(len(row) for row in image_lines)
        image_lines = [row for row in image_lines if len(row) == max_len]
        df = pd.DataFrame(image_lines)
        norm = plt.Normalize(df.values.min(), df.values.max())
        colored = cm.rainbow(norm(df.values))[:, :, :3]  # RGB only
        img = (colored * 255).astype(np.uint8)

        # Resize for consistency
        img = cv2.resize(img, (400, 400), interpolation=cv2.INTER_AREA)
        frame_list.append(img)

    if not frame_list:
        return "No valid image data found in uploaded files.", 400

    video_path = os.path.join('static', 'preview_video.mp4')
    os.makedirs('static', exist_ok=True)

    # Write video
    writer = imageio.get_writer(video_path, fps=10)
    for frame in frame_list:
        writer.append_data(frame)
    writer.close()

    return redirect(url_for('static', filename='preview_video.mp4'))


if __name__ == '__main__':
    app.run(port = 5001, debug=True)