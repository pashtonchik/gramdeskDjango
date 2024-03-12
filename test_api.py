import base64
import requests


a = requests.get('https://api.telegram.org/bot5368795970:AAFHF5s1P2j_b5rbfBeN25F4ZRcQZAF8e_Y/setWebhook?url=https://pashtonp.space/tg_bots/5368795970:AAFHF5s1P2j_b5rbfBeN25F4ZRcQZAF8e_Y')

b = a.json()

print(b)