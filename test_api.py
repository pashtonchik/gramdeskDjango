import requests
#
token = "vk1.a.Df89ZjgqhW_HDU4cIZ3iNpOqprbm9-z47pam8KGDeAWl8Rj-qINKl0LbQyfOYuUFkPpR1uM3y562ONMHogxSmwtd5Gzw5nkZoygC_Yy_dS1x9iZozbtXdYDkqmXpHjyqjmQHTRyDDcUnTsdCbMdfk0yPks07tQqUWUfYivsXZpshq5AMQ4FlH0F4H1mmmQnM6gGNGbtlnWuJQ0wy-9EsZQ"
#
# d = {
#     "Authorization": f"Bearer {token}"
# }
#
# get_message = requests.get(
#     f"https://api.vk.com/method/docs.getMessagesUploadServer?peer_id=212361840&v=5.199", headers=d)
#
# print(get_message.text)
# print(get_message.json()["response"]["upload_url"])


# url = "https:\/\/pu.vk.com\/c909518\/upload.php?act=add_doc_new&mid=-225303200&aid=-1&gid=0&type=0&peer_id=212361840&rhash=d0f897466918cbddcc743c6bb3b1106d&api=1&server=909518&_origin=https%3A%2F%2Fapi.vk.com&_sig=1fcd0ab0849ef18d68c00f94e217daf1"
#
#
#
# files = {'file': open('C:/Users/pashk/OneDrive/Рабочий стол/123/60.pdf', 'rb')}
#
#
# upload_doc = requests.post(url.replace("\\", ""), files=files)
#
# print(upload_doc.text)
# print(upload_doc.json())


# file_data = "212361840|0|-1|909518|9950ccc745|pdf|118758|60.pdf|8aebb3f0c087452061572b85d883553d|b54ce15228c609cb1411e0e573553b51||||eyJkaXNrIjoiMTciLCJwZWVyX3NlbmRlciI6Ii0yMjUzMDMyMDAifQ=="
#
# d = {
#     "Authorization": f"Bearer {token}"
# }
#
# save_doc = requests.get(f"https://api.vk.com/method/docs.save?file={file_data}&v=5.199", headers=d)
#
# print(save_doc.text)

doc_owner_id = "212361840"
doc_id = "673317441"

d = {
    "Authorization": f"Bearer {token}"
}

send_message = requests.get(f"https://api.vk.com/method/messages.send?user_id=212361840&attachment=doc{doc_owner_id}_{doc_id}&random_id=0&message=123&v=5.199", headers=d)

print(send_message.text)



