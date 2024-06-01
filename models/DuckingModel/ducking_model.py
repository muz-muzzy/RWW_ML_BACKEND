import cv2
import os
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model

class DuckingModel():
    def __init__(self):
        self.model = load_model('./weights/precise_under_train_classifier.h5')
        self.image_size = (512, 512)
        self.threshold = 0.9

    def predict(self, img):
        img = Image.fromarray(img)
        img = img.resize(self.image_size)
        img_array = np.array(img) / 255.0

        prediction = self.model.predict(np.expand_dims(img_array, axis=0))[0][0]

        if prediction > self.threshold:
            return True
        
        return False
    

if __name__ == '__main__':
    model = DuckingModel()
    img = cv2.imread('./test.jpg')
    print(model.predict(img))