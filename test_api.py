import base64

with open('IMG_3917.JPG', 'rb') as file:
    file = base64.b64encode(file.read()).decode('UTF-8')


open('IMG_1.JPG', 'wb').write(base64.b64decode(file.encode('UTF-8')))