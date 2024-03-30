import re
import numpy as np
from tickets.settings import tokenizer, emotional_model


def clear_text(text):
    text = text.replace("\\", " ").replace(u"╚", " ").replace(u"╩", " ")
    text = text.lower()
    text = re.sub('\-\s\r\n\s{1,}|\-\s\r\n|\r\n', ' ', text)
    text = re.sub('[.,:;_%©?*,!@#$%^&()\d]|[+=]|[[]|[]]|[/]|"|\s{2,}|-', ' ', text)
    text = re.sub('[^а-яА-Я ]', ' ', text)
    text = re.sub(' +', ' ', text)

    return text


def predict_toxical(text):
    matrixFromtokenizer = tokenizer.texts_to_matrix(np.array([clear_text(text)]), mode='count')
    predict = emotional_model.predict(np.array(matrixFromtokenizer))[0][0]
    print(text, 'Токсичность данного заголовка равна: {:.2f}%'.format(predict*100))