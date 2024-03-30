# Загрузка необходимых библиотек и модулей
import pandas as pd
import numpy as np
import pickle
import re
from keras.preprocessing.text import Tokenizer
from keras import models

# Модуль для работы с моделями (сохранить / загрузить), чтобы каждый раз не создавать её заново
def load_model(model_name):
    return models.load_model(model_name+'.h5')


# Модуль для работы с Токенайзером (сохраненить / загрузить), чтобы каждый раз не создавать его заново
def read_from_pickle(file_name):
    with open(file_name + '.pickle', 'rb') as file:
        return pickle.load(file)

tokenizer = read_from_pickle('my_tokenizer')
model = load_model('my_model')


ATA_csv = './posts.csv'
ATA_df = pd.read_csv(ATA_csv,sep=';').dropna()


def clear_text(text):
    text = text.replace("\\", " ").replace(u"╚", " ").replace(u"╩", " ")
    text = text.lower()
    text = re.sub('\-\s\r\n\s{1,}|\-\s\r\n|\r\n', ' ', text)
    text = re.sub('[.,:;_%©?*,!@#$%^&()\d]|[+=]|[[]|[]]|[/]|"|\s{2,}|-', ' ', text)
    text = re.sub('[^а-яА-Я ]', ' ', text)
    text = re.sub(' +', ' ', text)

    return text


ATA_title = ATA_df.title


def predict_toxical(text):
    matrixFromtokenizer = tokenizer.texts_to_matrix(np.array([clear_text(text)]), mode='count')
    predict = model.predict(np.array(matrixFromtokenizer))[0][0]
    print(text, 'Токсичность данного заголовка равна: {:.2f}%'.format(predict*100))


# for i in range(20):
#     predict_toxical(ATA_title[i])

predict_toxical("""идите лесом тупые уебаны""")