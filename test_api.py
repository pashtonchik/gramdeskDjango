import requests

token = "vk1.a.DPKLG_W7WXiFZE8uSjlbsUhNTuYL2vrQQGWBrFHDuBp5n2n9hfg9VZ2gJ4o7GyFmYFPeHpO-lRBLitF8686VBRWsNy_cbkFtX03uDG758enD3blKnlliwKAaD6GGbtf3_ha1iAXE6vVwoS65AVQBboH-JXOTcbv0aO49lgRRD5rd2-6KbGHq9mq9QOkdLjJRyplzXsNTiVrSn8CiyfQURQ"

d = {
    "Authorization": f"Bearer {token}"
}

a = {
    "message_ids": 7
}

a = requests.post("https://api.vk.com/method/messages.getById?message_ids=7&v=5.199", json=a, headers=d)

print(a.text)