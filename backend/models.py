import base64
import io
import uuid as uuid

from channels.db import database_sync_to_async
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from tickets.settings import MEDIA_ROOT


class User(AbstractUser):

    user_type_selector = (
        ('client', 'Клиент'),
        ('support', 'Поддержка')
    )

    type = models.CharField(max_length=5000, blank=True, choices=user_type_selector)
    my_email = models.CharField(max_length=5000, unique=True, null=True, blank=True)
    username = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    profiat_id = models.CharField(max_length=100, blank=True, null=True)
    profiat_username = models.CharField(max_length=100, blank=True, null=True)
    profiat_email = models.CharField(max_length=100, blank=True, null=True)
    tg_id = models.CharField(max_length=100, blank=True, null=True)
    tg_username = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)


class Ticket(models.Model):

    uuid = models.UUIDField(primary_key=True, max_length=40, default=uuid.uuid4, editable=False, unique=True)
    support_user = models.ForeignKey(to=User, on_delete=models.PROTECT, blank=True, null=True)
    tg_user = models.ForeignKey(to=User, on_delete=models.PROTECT)
    status = models.CharField(max_length=50)
    date_created = models.DateTimeField(auto_now_add=True)
    date_closed = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.tg_user.tg_username} {self.date_created}'

    def get_count_unread_messages(self):
        return TicketMessage.objects.filter(ticket=self, read_by_received=False, deleted=False).count()

    @property
    def last_message(self):
        last_message = TicketMessage.objects.filter(ticket=self, deleted=False).order_by('-date_created')
        if last_message.exists():
            last_message = last_message.first()
            return last_message
        else:
            return None

    def get_user_name(self):
        return self.tg_user.username


class TicketMessage(models.Model):

    sender_selector = (
        ('client', 'Клиент'),
        ('support', 'Сотрудник')
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
    employee = models.ForeignKey(to=User, on_delete=models.PROTECT, blank=True, null=True, related_name='ticket_message_employee')
    tg_user = models.ForeignKey(to=User, on_delete=models.PROTECT, related_name='ticket_message_client')
    sending_state = models.CharField(max_length=50)
    message_to_reply = models.ForeignKey(to='TicketMessage', on_delete=models.CASCADE, blank=True, null=True)
    deleted = models.BooleanField(default=False)
    message_text = models.TextField()
    message_file = models.FileField()
    content_type = models.CharField(max_length=20)
    read_by_received = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    def get_ticket_id(self):
        return str(self.ticket.uuid)

    def get_sender_id(self):
        if self.sender == 'client':
            return self.tg_user.id
        else:
            return self.employee.id

    def get_sender_username(self):
        if self.sender == 'client':
            return self.tg_user.username
        else:
            return self.employee.username


    def get_is_outgoing_client(self):
        if self.sender == 'client':
            return True
        else:
            return False

    def get_is_outgoing_support(self):
        if self.sender == 'client':
            return False
        else:
            return True

    @transaction.atomic()
    def get_files(self):
        from backend.serializers import AttachmentSerializer
        attachments = Attachment.objects.filter(message=self).values('id', 'name', 'total_bytes', 'received_bytes', 'ext', 'buf_size').order_by('id')
        if attachments.exists():
            return AttachmentSerializer(attachments, many=True).data
        return None

    def get_date(self):
        return self.date_created.isoformat() if self.date_created else '-'


class Attachment(models.Model):
    message = models.ForeignKey(to=TicketMessage, on_delete=models.PROTECT)
    file = models.FileField(blank=True, null=True)
    name = models.CharField(max_length=500)
    content = models.BinaryField(blank=True, null=True)
    total_bytes = models.IntegerField()
    buf_size = models.IntegerField(default=512)
    received_bytes = models.IntegerField(default=0)
    uploaded = models.BooleanField(default=False)
    ext = models.CharField(max_length=50)


class JWTToken(models.Model):
    class Meta:
        verbose_name = 'JWT'
        verbose_name_plural = 'JWT'

    user = models.ForeignKey(to=User, blank=True, null=True, on_delete=models.PROTECT)
    jwt = models.TextField(blank=True, null=True, unique=True)
    active = models.BooleanField(default=True)
    refresh = models.ForeignKey(to=OutstandingToken, blank=True, null=True, on_delete=models.CASCADE)
    date_created = models.IntegerField(blank=True, null=True)


class SocketConnection(models.Model):
    class Meta:
        verbose_name = 'Socket Connection'
        verbose_name_plural = 'Socket Connections'

    user = models.ForeignKey(to=User, blank=True, null=True, on_delete=models.PROTECT)
    jwt = models.ForeignKey(to=JWTToken, blank=True, null=True, on_delete=models.PROTECT)
    channel_name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    last_heartbeat = models.IntegerField(default=0)
    approve_heartbeat = models.BooleanField(default=False)
    date_created = models.IntegerField()
    date_closed = models.IntegerField(default=0)


class TelegramBots(models.Model):
    class Meta:
        verbose_name = 'Telegram Bot'
        verbose_name_plural = 'Telegram Bots'

    user = models.ForeignKey(to=User, blank=True, null=True, on_delete=models.PROTECT)
    bot_apikey = models.CharField(max_length=300)






