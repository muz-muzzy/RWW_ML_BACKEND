# RWW_ML_BACKEND
## Описание
Это API на Flask, для работы веб-приложения по автоматическому обнаружению нарушений правил безопасности на записях с нагрудных камер работников РЖД.
## Установка и запуск
1. Клонирование репозитория:
```bash
git clone https://github.com/muz-muzzy/RWW_ML_BACKEND.git
```
2. Переход в каталог проекта:
```bash
cd RWW_ML_BACKEND
```
3. Установка зависимостей:
```bash
pip install -r requirements.txt
```
4. Скачивание весов модели:
windows:
```bash
python ./models/DuckingModel/download.py
```
linux:
```bash
python3 ./models/DuckingModel/download.py
```
4. Запуск
```bash
python app.py
```

## Роуты
### /getvideos
Метод - GET
Результат - JSON файл вида:
{
    "files": [
        "video1.mp4",
        "video2.mp4", 
        ....
    ]
}

### /getvideo/%filename%
Метод - GET
Результат - .mp4 файл (видео)
Отдаёт видео по его названию (передаётся в url, например - "http://127.0.0.1:3000/getvideo/video.mp4").
В headers ответа функции также содержатся списки таймкодов нарушений всех видов
![скриншот хэдеров](headers_screenshot.png)

### /upload
Метод - POST
Принимает form-data с .mp3 файлом, загружает его на сервер, анализируя его, и сохраняя данные о нём в БД.
Возвращает JSON с сообщением об успехе или неудаче