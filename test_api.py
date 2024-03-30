# Загрузка необходимых библиотек и модулей
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Embedding, LSTM, Bidirectional
from keras.optimizers import RMSprop
from keras.preprocessing.text import Tokenizer

from sklearn.preprocessing import normalize
from sklearn.model_selection import train_test_split

print(keras.__version__)
#
# print(123)

# Датасет из Домотехники
DT_csv = './dt_reviews.csv'
DT_df = pd.read_csv(DT_csv, sep=';').dropna()

# Метод для сжатия градации в данных из Домотехники (1 и 2 становятся 1 (плохо), 4 и 5 становятся 0 (хорошо))
def change_rating_value(df, before, after):
    df['rating'][df['rating'] == before] = after
    return df

# Метод подготовка текста для Токинайзера
def clear_text(text):
    text = text.replace("\\", " ").replace(u"╚", " ").replace(u"╩", " ")
    text = text.lower()
    text = re.sub('\-\s\r\n\s{1,}|\-\s\r\n|\r\n', ' ', text)
    text = re.sub('[.,:;_%©?*,!@#$%^&()\d]|[+=]|[[]|[]]|[/]|"|\s{2,}|-', ' ', text)
    text = re.sub('[^а-яА-Я ]', ' ', text)
    text = re.sub(' +', ' ', text)

    return text

change_rating_value(DT_df, 4, 5)
change_rating_value(DT_df, 5, 0)
change_rating_value(DT_df, 2, 1)

# Удаление записей с рейтингом 3 (Теперь между плохими и хорошими отзывами есть "пропасть")
DT_df = DT_df[~(DT_df.rating==3)]

# Удаляем ненужные столбцы
DT_df = DT_df.drop(['#', 'limits', 'comment'],axis=1)

# uint- целые числа без знака позволяют хранить столбцы с положительными числами более эффективно
DT_df['rating'] = DT_df['rating'].astype('uint8')

# Переименовываем столбцы
DT_df = DT_df.rename(columns={'rating': 'toxic','accomps': 'comment'})

# 38940
DT_df['comment'] = DT_df['comment'].apply(clear_text)


# Датасет из Kaggle
kaggle_csv = './labeled.csv'
kaggle_df = pd.read_csv(kaggle_csv)

# Подготавливаем текст
kaggle_df['comment'] = kaggle_df['comment'].apply(clear_text)
# Токсичность может быть 0 или 1, поэтому меняем тип rating с float на uint8
kaggle_df['toxic'] = kaggle_df['toxic'].astype('uint8')


frames = [kaggle_df, DT_df]
main_df = pd.concat(frames)

# Перемешиваем данные
main_df = main_df.sample(frac=1)

# Токенайзер создает словарь, в котором будет хранить 10000 наиболее часто встречающихся слов из DataFrame'а
tokenizer = Tokenizer(num_words=10000, filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n',
                      lower=True,
                      split=' ',
                      char_level=False)
tokenizer.fit_on_texts(main_df['comment'])


# Преобразует слова в числа (модели работают с токенами)
matrix = tokenizer.texts_to_matrix(main_df['comment'], mode='count')


# Нормализованные данные - это данные от 0 до 1 (было от 0 до 15000), модели проще обучаться на числах в небольшом диапазоне
normalize_matrix = normalize(matrix)
labels = np.array(main_df['toxic'])

# Разделение данных на обучающие и тестовые ((36032, 10000), (9009, 10000), (36032,), (9009,))
data_train, data_test, labels_train, labels_test = train_test_split(normalize_matrix, labels, test_size=0.2)


def get_model():
    #     Модель с точностью в 85%
    model = Sequential()

    model.add(Dense(32, activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(16, activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(16, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer=RMSprop(lr=0.0001),
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    return model


model = get_model()

model_history = model.fit(data_train,
                    labels_train,
                    epochs=70,
                    batch_size=500,
                    validation_data=(data_test, labels_test))


history = model_history.history
# fig = plt.figure(figsize=(20, 10))
#
# ax1 = fig.add_subplot(221)
# ax2 = fig.add_subplot(223)
#
# x = range(70)
#
# ax1.plot(x, history['acc'], 'b-', label='Accuracy')
# ax1.plot(x, history['val_acc'], 'r-', label='Validation accuracy')
# ax1.legend(loc='lower right')
#
# ax2.plot(x, history['loss'], 'b-', label='Losses')
# ax2.plot(x, history['val_loss'], 'r-', label='Validation losses')
# ax2.legend(loc='upper right')

# Модуль для работы с моделями (сохранить / загрузить), чтобы каждый раз не создавать её заново
from keras import models


def save_model(model, model_name):
    model.save(model_name + '.h5')


def load_model(model_name):
    return models.load_model(model_name + '.h5')


# Модуль для работы с Токенайзером (сохраненить / загрузить), чтобы каждый раз не создавать его заново
import pickle

def write_to_pickle(data, file_name):
    with open(file_name + '.pickle', 'wb') as file:
        pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)

def read_from_pickle(file_name):
    with open(file_name + '.pickle', 'rb') as file:
        return pickle.load(file)

save_model(model, "my_model")
write_to_pickle(tokenizer, "my_tokenizer")
