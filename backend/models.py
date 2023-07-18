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

    def get_count_unread_messages(self):
        return TicketMessage.objects.filter(ticket=self, read_by_manager=False)

    def get_last_message(self):
        return TicketMessage.objects.filter(ticket=self).order_by('-date_created').first()

    def get_user_name(self):
        return self.tg_user.tg_username


class TicketMessage(models.Model):

    sender_selector = (
        ('client', 'Клиент'),
        ('employee', 'Сотрудник')
    )

    content_type_selector = (
        ('text', 'Текст'),
        ('file', 'Файл'),
    )

    ticket = models.ForeignKey(to=Ticket, on_delete=models.PROTECT)
    sender = models.CharField(max_length=20, choices=sender_selector)
    # employee = models.ForeignKey
    tg_user = models.ForeignKey(to=TelegramUser, on_delete=models.PROTECT)
    message_text = models.TextField()
    message_file = models.FileField()
    content_type = models.CharField(max_length=20)
    read_by_manager = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)



