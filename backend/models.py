import uuid as uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class SupportUser(AbstractUser):
    my_email = models.CharField(max_length=5000, unique=True, null=True, blank=True)
    username = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    verify_email = models.BooleanField(default=False)
    verify_phone = models.BooleanField(default=False)
    avatar = models.URLField(default='', null=True, blank=True)
    api_access = models.BooleanField(default=False)
    balance = models.DecimalField(default=0, max_digits=300, decimal_places=2)
    otp_auth = models.BooleanField(default=False)
    flex_wallet = models.BooleanField(default=False)
    flex_wallet_uuid = models.CharField(max_length=200, blank=True, null=True)
    enable_withdraws = models.BooleanField(default=True)
    enable_deposits = models.BooleanField(default=True)

    sms_secret_key = models.CharField(max_length=200, null=True, blank=True)
    otp_secret_key = models.CharField(max_length=200, null=True, blank=True)


class Client(models.Model):

    uuid = models.UUIDField(primary_key=True, max_length=40, default=uuid.uuid4, editable=False, unique=True)
    tg_id = models.CharField(max_length=100)
    tg_username = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tg_username

    def get_count_tickets(self):
        return Ticket.objects.filter(tg_user=self, status='closed').count()

    def get_date_added(self):
        return int(self.date_added.timestamp()) if self.date_added else '-'


class Ticket(models.Model):

    uuid = models.UUIDField(primary_key=True, max_length=40, default=uuid.uuid4, editable=False, unique=True)
    tg_user = models.ForeignKey(to=Client, on_delete=models.PROTECT)
    status = models.CharField(max_length=50)
    date_created = models.DateTimeField(auto_now_add=True)
    date_closed = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.tg_user.tg_username} {self.date_created}'

    def get_count_unread_messages(self):
        return TicketMessage.objects.filter(ticket=self, read_by_manager=False).count()

    def get_last_message(self):
        last_message = TicketMessage.objects.filter(ticket=self).order_by('-date_created').first()
        return {
            'content_type': last_message.content_type,
            'message': last_message.message_text
        }

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

    sending_state_selector = (
        ('sent', 'Отправлено'),
        ('delivered', 'Дотсавлено до получателя'),
        ('failed', 'Не дошло до получателя'),
        ('read', 'Прочитано получателем')
    )

    ticket = models.ForeignKey(to=Ticket, on_delete=models.PROTECT)
    sender = models.CharField(max_length=20, choices=sender_selector)
    employee = models.ForeignKey(to=SupportUser, on_delete=models.PROTECT, blank=True, null=True)
    tg_user = models.ForeignKey(to=Client, on_delete=models.PROTECT)
    sending_state = models.CharField(max_length=50)
    message_text = models.TextField()
    message_file = models.FileField()
    content_type = models.CharField(max_length=20)
    read_by_manager = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    def get_ticket_id(self):
        return self.ticket.uuid

    def get_sender_id(self):
        if self.sender == 'client':
            return self.tg_user.uuid
        else:
            return self.employee.id

    def get_is_outgoing(self):
        if self.sender == 'client':
            return False
        else:
            return True

    def get_file(self):
        return None





