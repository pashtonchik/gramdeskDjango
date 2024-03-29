from celery import shared_task
import requests
from django.db import transaction
from datetime import datetime


@shared_task(bind=True)
def upload_doc(self, attach_id, platform_id):
    from backend.models import Attachment, Platform
    try:
        with transaction.atomic():
            attach = Attachment.objects.select_for_update().get(id=attach_id)
            platform = Platform.objects.get(uuid=platform_id)


            auth = {
                "Authorization": f"Bearer {platform.vk_access_key}"
            }

            # 1
            get_upload_url = requests.get(
                f"https://api.vk.com/method/docs.getMessagesUploadServer?peer_id={attach.message.tg_user.vk_id}&v=5.199", headers=auth)
            print(get_upload_url.text)
            if get_upload_url.status_code == 200:
                attach.vk_upload_url = get_upload_url.json()["response"]["upload_url"].replace("\\", "")
                attach.save()
            else:
                print(get_upload_url.text)
                raise KeyError

            # 2
            files = {'file': attach.file.open('rb')}

            upload_doc = requests.post(attach.vk_upload_url, files=files)
            print(upload_doc.text)
            if get_upload_url.status_code == 200:
                attach.vk_file_data = upload_doc.json()["file"]
                attach.save()
            else:
                print(upload_doc.text)
                raise KeyError

            # 3
            save_doc = requests.post(f"https://api.vk.com/method/docs.save?file={attach.vk_file_data}&v=5.199", headers=auth)
            print(save_doc.text)
            if save_doc.status_code == 200:
                type = save_doc.json()["response"]["type"]
                attach.vk_file_id = save_doc.json()["response"][type]["id"]
                attach.vk_owner_id = save_doc.json()["response"][type]["owner_id"]
                attach.vk_file_type = type
                attach.save()
            else:
                print(save_doc.text)
                raise KeyError
            print("возвращаем")

            return {
                "type": attach.vk_file_type,
                "id": attach.vk_file_id,
                "owner_id": attach.vk_owner_id,
            }

    except Exception as e:
        return {
                "status": "rejected"
            }