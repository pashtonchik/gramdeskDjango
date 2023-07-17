import uuid as uuid
from django.db import models


class TelegramUser(models.Model):

    uuid = models.UUIDField(primary_key=True, max_length=40, default=uuid.uuid4, editable=False, unique=True)
    tg_id = models.CharField(max_length=100)
    tg_username = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tg_username


class Ticket(models.Model):

    uuid = models.UUIDField(primary_key=True, max_length=40, default=uuid.uuid4, editable=False, unique=True)
    tg_user = models.ForeignKey(to=TelegramUser, on_delete=models.PROTECT)
    status = models.CharField(max_length=50)
    date_created = models.DateTimeField(auto_now_add=True)
    date_closed = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.tg_user.tg_username} {self.date_created}'


class TicketMessage(models.Model):

    ticket = models.ForeignKey(to=Ticket, on_delete=models.PROTECT)
    tg_user = models.ForeignKey(to=TelegramUser, on_delete=models.PROTECT)
    message_text = models.TextField()
    message_file = models.FileField()
    date_created = models.DateTimeField(auto_now_add=True)



