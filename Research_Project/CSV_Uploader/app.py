from flask import Flask, render_template, request, redirect, url_for, session
import os
import pandas as pd
import psycopg2
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2
import numpy as np
import imageio
from uuid import uuid4
import io
from PIL import Image

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5 GB
os.environ["IMAGEIO_FFMPEG_EXE"] = "/opt/homebrew/bin/ffmpeg"

hostname = 'localhost'
database = 'postgres'
username = 'postgres'
pwd = 'Srinivas@123'
port_id = '5340'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
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
            cur.execute("INSERT INTO Machine (M_ID, M_Name) VALUES (%s, %s) ON CONFLICT (M_ID) DO NOTHING", (number, name))

            cur.execute("SELECT 1 FROM Material WHERE Material_Type = %s", (material,))
            if cur.fetchone():
                cur.execute("UPDATE Material SET M_ID = %s WHERE Material_Type = %s", (number, material))
            else:
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

            cur.execute("SELECT 1 FROM Machine WHERE M_ID = %s", (machine_id,))
            if not cur.fetchone():
                cur.execute("INSERT INTO Machine (M_ID, M_Name) VALUES (%s, %s)", (machine_id, f"Machine_{machine_id}"))

            cur.execute("INSERT INTO Material (Material_Type, M_ID) VALUES (%s, %s)", (material_type, machine_id))
            conn.commit()
        except Exception as e:
            return f"Error: {e}"
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('select_machine'))

    return render_template('add_material.html')

@app.route('/index')
def index():
    grouped_files = {}

    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
        files.sort()
        for file in files:
            rel_dir = os.path.relpath(root, app.config['UPLOAD_FOLDER'])
            rel_file = os.path.join(rel_dir, file) if rel_dir != '.' else file

            if rel_dir == '.':
                grouped_files.setdefault('', []).append(rel_file)
            else:
                folder = rel_dir.split(os.sep)[0]
                grouped_files.setdefault(folder, []).append(rel_file)

    return render_template('index.html', files=grouped_files)

@app.route('/upload', methods=['POST'])
def upload_file():
    for file in request.files.getlist('files[]'):
        relative_path = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], relative_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
    return ('', 204)

def extract_image_dataframe(filepath, expected_cols=20):
    with open(filepath, 'r') as file:
        lines = file.read().replace('\r', '').strip().split('\n')

    image_lines = []
    start_data = False

    for line in lines:
        line = line.strip()
        if not start_data:
            if "Image Data" in line:
                start_data = True
            continue
        if not line:
            continue

        parts = [p.strip() for p in line.split(';') if p.strip()]
        try:
            float_parts = [float(p) for p in parts[:expected_cols]]
            if len(float_parts) == expected_cols:
                image_lines.append(float_parts)
        except ValueError:
            continue

    if not image_lines:
        raise ValueError("No valid numeric data found.")

    df = pd.DataFrame(image_lines)
    df.columns = [f"Col{i+1}" for i in range(expected_cols)]
    return df

@app.route('/preview/<path:filename>')
def preview(filename):
    safe_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    if not safe_path.startswith(app.config['UPLOAD_FOLDER']):
        return "Invalid file path!", 400

    try:
        df = extract_image_dataframe(safe_path)
        df_html = df.to_html(classes='table table-bordered', index=False, escape=False)
        return render_template('preview.html', tables=[df_html], filename=filename, show_button=True)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/view/<path:filename>')
def view_image_data(filename):
    safe_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    if not safe_path.startswith(app.config['UPLOAD_FOLDER']):
        return "Invalid file path!", 400

    try:
        df = extract_image_dataframe(safe_path)
        vmin, vmax = df.values.min(), df.values.max()

        def get_gradient_color(value):
            norm_val = (value - vmin) / (vmax - vmin)
            norm_val = max(0.0, min(1.0, norm_val))
            return plt.cm.plasma(norm_val)

        df_html = '<table class="table table-bordered" style="border-collapse: collapse;">'
        for row in df.values:
            df_html += '<tr>'
            for val in row:
                rgba = get_gradient_color(val)
                hex_color = matplotlib.colors.to_hex(rgba)
                df_html += f'<td style="background-color: {hex_color}; text-align: center;">{val:.2f}</td>'
            df_html += '</tr>'
        df_html += '</table>'

        return render_template('preview.html', tables=[df_html], filename=filename, show_button=False)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/update/<path:filename>', methods=['POST'])
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

        conn = psycopg2.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cur = conn.cursor()

        # Ensure entry in Sensor3Data table
        cur.execute("INSERT INTO Sensor3 (File_Path, Sensor_ID, Type) VALUES (%s, %s, %s) ON CONFLICT (File_Path) DO NOTHING", (filename, 1, 'IR_Camera'))

        for idx, row in df.iterrows():
            row_index = idx + 1  # 1-based index for DB
            values = [filename, row_index] + [row[i] if pd.notna(row[i]) else None for i in df.columns]
            cur.execute("""
                INSERT INTO Sensor3_IRCamera (
                    File_Path, Row_Index,
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


@app.route('/generate_video/<path:folder>')
def generate_folder_video(folder):
    base_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    video_name = f"{folder.replace('/', '_')}_thermal_video.mp4"
    output_path = os.path.join("static", "videos", video_name)

    if not os.path.exists("static/videos"):
        os.makedirs("static/videos")

    try:
        # Get all .csv files from the folder recursively
        csv_files = sorted([
            os.path.join(root, file)
            for root, _, files in os.walk(base_path)
            for file in files if file.endswith('.csv')
        ])

        if not csv_files:
            return "No CSV files found in folder", 404

        import imageio
        writer = imageio.get_writer(output_path, fps=30)

        for file in csv_files:
            try:
                df = extract_image_dataframe(file)
                image = create_colored_image(df)  # Same as for top-level
                writer.append_data(image)
            except Exception as e:
                print(f"Skipping file {file}: {e}")  # Continue if one file fails

        writer.close()
        return redirect(f"/{output_path}")

    except Exception as e:
        return f"Error: {e}", 500

@app.route('/generate_video_top_level')
def generate_top_level_video():
    top_files = []
    base_path = app.config['UPLOAD_FOLDER']

    for file in os.listdir(base_path):
        if file.endswith('.csv'):
            top_files.append(os.path.join(base_path, file))
    top_files.sort()

    output_path = os.path.join("static", "videos", "top_level_video.mp4")
    os.makedirs("static/videos", exist_ok=True)

    try:
        writer = imageio.get_writer(output_path, fps=10)
        for file in top_files:
            df = extract_image_dataframe(file)
            image = create_colored_image(df)
            writer.append_data(image)
        writer.close()
        return redirect(f"/{output_path}")
    except Exception as e:
        return f"Error: {e}", 500

def create_colored_image(df):
    fig, ax = plt.subplots()
    ax.imshow(df.values, cmap='plasma')  # 'plasma' works well for thermal
    ax.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)

    image = Image.open(buf)
    return np.array(image)

@app.route('/clear_selected', methods=['POST'])
def clear_selected():
    selected_items = request.form.getlist('selected_files')

    for item in selected_items:
        full_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], item))

        if os.path.isdir(full_path):
            # Delete all files and subfolders in the folder
            for root, dirs, files in os.walk(full_path, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            try:
                os.rmdir(full_path)
            except FileNotFoundError:
                pass

            # ✅ Delete corresponding video file if it exists
            video_name = f"{item.strip('/').replace('/', '_')}_thermal_video.mp4"
            video_path = os.path.join("static", "videos", video_name)
            if os.path.exists(video_path):
                os.remove(video_path)

        elif os.path.isfile(full_path):
            os.remove(full_path)

        # Clean up empty parent directories
        folder = os.path.dirname(full_path)
        while folder and folder != app.config['UPLOAD_FOLDER']:
            if os.path.exists(folder) and not os.listdir(folder):
                os.rmdir(folder)
                folder = os.path.dirname(folder)
            else:
                break

    return redirect(url_for('index'))


@app.route('/delete/<path:filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

        folder = os.path.dirname(file_path)
        while folder and folder != app.config['UPLOAD_FOLDER']:
            if not os.listdir(folder):
                os.rmdir(folder)
                folder = os.path.dirname(folder)
            else:
                break

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=5001, debug=True)
