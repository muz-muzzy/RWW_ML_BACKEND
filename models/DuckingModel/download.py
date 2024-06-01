import gdown

# URL файла или его идентификатор
url = "https://drive.google.com/uc?id=1z08IQnnQE8LcQKmrtfycvfvNVqHyjmy7"
# Путь, куда будет сохранён файл
output = "./models/DuckingModel/weights/model.h5"

# Скачивание файла
gdown.download(url, output, quiet=False)