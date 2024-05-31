from flask import Flask, request, jsonify
import os
import sqlite3
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import shutil

UPLOAD_FOLDER = './upload'
ALLOWED_EXTENSIONS = {'mp4'}
app = Flask(__name__)
DATABASE = 'video_analysis.db'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

import sqlite3

DATABASE = 'video_analysis.db'

def create_database_and_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Создание таблицы videos, если она не существует
    cursor.execute('''CREATE TABLE IF NOT EXISTS videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL UNIQUE,
                        upload_time DATETIME DEFAULT CURRENT_TIMESTAMP
                    );''')

    # Создание таблицы violations, если она не существует
    cursor.execute('''CREATE TABLE IF NOT EXISTS violations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id INTEGER,
                        start_time REAL,
                        end_time REAL,
                        FOREIGN KEY(video_id) REFERENCES videos(id)
                    );''')

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Подключение к базе данных
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Добавление имени файла в базу данных
        try:
            cursor.execute("INSERT INTO videos (filename) VALUES (?)", (filename,))
            db_conn.commit()
            return jsonify({'message': 'Video uploaded successfully'}), 200
        except Exception as e:
            db_conn.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            cursor.close()
            db_conn.close()

# def process_frame(frame):
#     results = {}
#     for model_name, model in models.items():
#         predictions = model.predict(frame)
#         # Предполагаем, что модель возвращает координаты начала и конца нарушения
#         violations = [[prediction[0], prediction[1]] for prediction in predictions]
#         results[model_name] = violations
#     return results

# @app.route('/analyze', methods=['POST'])
# def analyze_video():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file part'}), 400
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'No selected file'}), 400
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(file_path)
        
#         cap = cv2.VideoCapture(file_path)
#         frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         all_violations = []
#         first = True
#         for i in range(frame_count):
#             ret, frame = cap.read()
#             if first:
#                 width, height, _ = frame.shape()
#                 first = False
#             if not ret:
#                 break
#             violations = process_frame(frame)
#             all_violations.append(violations)
        
#         cap.release()
#         os.remove(file_path)  # Удаление временного файла
        
#         final_response = {"all_models": all_violations}
#         return jsonify(final_response), 200

if __name__ == '__main__':
    create_database_and_tables()
    app.run(host="0.0.0.0", port=3000, debug=True)