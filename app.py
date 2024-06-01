from flask import Flask, request, jsonify, send_from_directory, make_response
import os
import sqlite3
from werkzeug.utils import secure_filename
from flask_cors import CORS
import cv2
from models.DuckingModel.ducking_model import DuckingModel
from models.EquipmentModel.equipment_model import Jacket_detection
from moviepy.editor import *
import json

UPLOAD_FOLDER = './upload'
OUTPUT_FOLDER = './outputs'
ALLOWED_EXTENSIONS = {'mp4', 'png'}
app = Flask(__name__)
CORS(app=app)
DATABASE = 'video_analysis.db'
jacket_model = Jacket_detection("./models/EquipmentModel/weights/jacket.pt", "./models/EquipmentModel/weights/people.pt")
ducking_model = DuckingModel("./models/DuckingModel/weights/model.h5")
    
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

import sqlite3

DATABASE = 'video_analysis.db'

def create_database_and_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Создание таблицы videos, если она не существует
    cursor.execute('''CREATE TABLE IF NOT EXISTS videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        violations TEXT
                    );''')

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def insert_video_with_violations(filename, violations_json):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (filename, violations) VALUES (?,?)", (filename, violations_json))
    conn.commit()
    conn.close()

def analyze_video(file_path):
    cap = cv2.VideoCapture(file_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # кодек X264 для записи в MP4
    fps = cap.get(cv2.CAP_PROP_FPS)  # Фреймрейт
    first = True
    filename = file_path[9:]
    count = 0
    
    val1_arr = []
    val2_arr = []
    start_val = -1
    end_val = -1

    start_val2 = -1
    end_val2 = -1
    while True:
        ret, frame = cap.read()
        count += 1 
        if not ret:
            break
        if first:
            shape = frame.shape
            frame_size = (shape[1], shape[0])  # Размер кадра
            out = cv2.VideoWriter(f'./trans/{filename}', fourcc, fps, frame_size)

            first = False

        frame, val = jacket_model.predict_image(frame)
        val2 = ducking_model.predict(frame)
        print(f'./outputs/{filename}')
        if val:
            if start_val == -1:
                start_val = int(count / fps)
            else:
                current_cal = int(count / fps)
                if end_val == -1:
                    end_val = current_cal
                elif current_cal - end_val > 2:
                    if end_val != start_val:
                        val1_arr.append(start_val)
                    start_val = -1
                    end_val = -1
                else:
                    end_val = current_cal

        if val2:
            if start_val2 == -1:
                start_val2 = int(count / fps)
            else:
                current_cal = int(count / fps)
                if end_val2 == -1:
                    end_val2 = current_cal
                elif current_cal - end_val2 > 2:
                    if end_val2 != start_val2:
                        val2_arr.append(start_val2)
                    start_val2 = -1
                    end_val2 = -1
                else:
                    end_val2 = current_cal

        print("time " + str(count/fps))
        print("start_val1 " + str(start_val))
        print("end_val " + str(end_val))
        #cv2.imshow('Video', frame)
        out.write(frame)

    if start_val != -1 and end_val != -1:
        val1_arr.append(start_val)
    if start_val2 != -1 and end_val2 != -1:
        val2_arr.append(start_val2)

    print(val1_arr)
    print(val2_arr)
    cap.release()
    out.release()
    
    clip = VideoFileClip(f'./trans/{filename}')
    clip.write_videofile(f"./outputs/{filename}")
    # Сформируем словарь с результатами
    violations_dict = {
        'vest': val1_arr,
        'ducking': val2_arr
    }

    # Сериализуем словарь в строку JSON
    violations_json = json.dumps(violations_dict)
    insert_video_with_violations(filename=filename, violations_json=violations_json)
    return val1_arr, val2_arr

@app.route('/getvideos', methods=['GET'])
def list_videos():
    # Получаем список всех файлов в папке uploads
    files = [f for f in os.listdir(app.config['OUTPUT_FOLDER']) if os.path.isfile(os.path.join(app.config['OUTPUT_FOLDER'], f))]
    
    if len(files) > 0:
        # Возвращаем список имен файлов
        return jsonify({'files': files})
    else:
        return jsonify({'error': 'No videos available'}), 404

@app.route('/getvideo/<filename>', methods=['GET'])
def send_video(filename):
    # Проверяем, существует ли файл
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.isfile(file_path):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Запрос данных о нарушениях для данного файла
        cursor.execute("SELECT violations FROM videos WHERE filename=?", (filename,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Извлечение данных о нарушениях из результата запроса
            violations = json.loads(result[0])
            vest_violations = violations.get('vest', [])
            ducking_violations = violations.get('ducking', [])
    
            # Создание ответа с файлом и заголовками
            response = make_response(send_from_directory(app.config['OUTPUT_FOLDER'], filename), 200)
            response.headers.add('vest', str(vest_violations))
            response.headers.add('ducking', str(ducking_violations))
            
            return response
        else:
            return jsonify({'error': 'No violations data found for this file'}), 404
    else:
        return jsonify({'error': 'File not found'}), 404


@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        base_filename, file_extension = os.path.splitext(filename)
        index = 1
        new_filename = f"{base_filename} ({index}){file_extension}"
        while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], new_filename)):
            index += 1
            new_filename = f"{base_filename} ({index}){file_extension}"

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(file_path)
        
        try:
            analyze_video(file_path)
            return jsonify({'message': 'Video uploaded successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Database error: {str(e)}'}), 500

if __name__ == '__main__':
    create_database_and_tables()
    app.run(host="0.0.0.0", port=3000, debug=True)