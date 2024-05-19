import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import numpy as np
from keras.datasets import mnist
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Dense
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

# Загрузка и обработка данных
(X_train, y_train), (X_test, y_test) = mnist.load_data()

# Преобразование данных
X_train = X_train.reshape(60000, 784) / 255.0
X_test = X_test.reshape(10000, 784) / 255.0
y_train = to_categorical(y_train, num_classes=10)
y_test = to_categorical(y_test, num_classes=10)

# Создание модели
model = Sequential()
model.add(Dense(64, input_dim=784, activation='relu'))
model.add(Dense(64, activation='relu'))
#model.add(Dense(64, activation='relu'))
model.add(Dense(10, activation='softmax'))
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Тренируем модель
model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test))

# Определяем функцию отрисовки
def draw_symbol():
    # Функция сохранения изображения и предсказания цифры
    def save_image():
        pil_image_resized = pil_image.resize((28, 28)).convert('L')  # Изменяем размер изображения и переводим в оттенки серого
        image = np.array(pil_image_resized)
        image = image.reshape(1, 784) / 255.0

        prediction = model.predict(image)
        predicted_digit = np.argmax(prediction)
        result_label.config(text=f'Predicted digit: {predicted_digit}')

    # Функция отслеживания движения мыши для рисования
    def on_mouse_drag(event):
        x, y = event.x, event.y
        draw.ellipse([x - 10, y - 10, x + 10, y + 10], fill="white")  # Рисуем круг при движении мыши
        canvas.image = ImageTk.PhotoImage(pil_image)  # Обновляем изображение на холсте
        canvas.create_image(0, 0, anchor='nw', image=canvas.image)

    # Функция очистки холста
    def clear_canvas():
        draw.rectangle((0, 0, 280, 280), fill="black")  # Заполняем холст черным цветом
        canvas.image = ImageTk.PhotoImage(pil_image)  # Обновляем изображение на холсте
        canvas.create_image(0, 0, anchor='nw', image=canvas.image)
        result_label.config(text='Predicted digit: ')  # Сбрасываем текст с предсказанной цифрой

    root = tk.Tk()
    root.title('Draw a digit from 0 to 9')

    pil_image = Image.new("RGB", (280, 280), "black")
    draw = ImageDraw.Draw(pil_image)

    canvas = tk.Canvas(root, width=280, height=280, bg='black')
    canvas.pack()

    canvas.bind("<B1-Motion>", on_mouse_drag)

    result_label = tk.Label(root, text='Predicted digit: ')
    result_label.pack()

    save_button = tk.Button(root, text="Save", command=save_image)
    save_button.pack()

    clear_button = tk.Button(root, text="Clear", command=clear_canvas)
    clear_button.pack()

    root.mainloop()

draw_symbol()