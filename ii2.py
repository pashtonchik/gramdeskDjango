import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from PIL import Image
from tensorflow.keras.preprocessing import image
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.applications.mobilenet_v2 import decode_predictions

# Открываем изображение
img_path = '31-лев-картинки.jpg'
img = Image.open(img_path)
img_resized = img.resize((224, 224))
img_resized.save('resized_image.jpg')

# Загружаем изображение для предсказания
img_resized = image.load_img('resized_image.jpg', target_size=(224, 224))
img_array = image.img_to_array(img_resized)
img_array = np.expand_dims(img_array, axis=0)
img_array = preprocess_input(img_array)

# Загружаем предобученную модель MobileNetV2
model = tf.keras.applications.MobileNetV2(weights='imagenet')

# Предсказываем объекты изображения
predictions = model.predict(img_array)
decoded_predictions = decode_predictions(predictions, top=3)[0]

# Выводим предсказания
for i, (imagenet_id, label, score) in enumerate(decoded_predictions):
    print(f'{i + 1}: {label} ({score})')
