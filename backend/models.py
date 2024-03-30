import base64
import io
import uuid as uuid

from channels.db import database_sync_to_async
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from tickets.settings import MEDIA_ROOT


class Platform(models.Model):

    uuid = models.UUIDField(primary_key=True, max_length=40, default=uuid.uuid4, editable=False, unique=True)
    admin = models.ForeignKey(to='User', on_delete=models.PROTECT, related_name="admin_platform")
    name = models.CharField(max_length=1000)
    description = models.TextField(blank=True, null=True)
    vk_confirmation_code = models.CharField(max_length=100)
    vk_access_key = models.CharField(max_length=1000)
    vk_webhook_connected = models.BooleanField(default=False)


class User(AbstractUser):

    user_type_selector = (
        ('client', 'Клиент'),
        ('support', 'Поддержка')
    )

    source_selector = (
        ('telegram', 'Телеграм'),
        ('widget', 'Виджет'),
        ('vk', "ВК")
    )

    type = models.CharField(max_length=100, blank=True, choices=user_type_selector)
    source = models.CharField(max_length=100, blank=True, choices=source_selector)
    platform = models.ForeignKey(to=Platform, on_delete=models.PROTECT, related_name="platform", blank=True, null=True)
    my_email = models.CharField(max_length=5000, unique=True, null=True, blank=True)
    verify_email = models.BooleanField(default=False)
    username = models.CharField(max_length=50, unique=True)
    support_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    profiat_id = models.CharField(max_length=100, blank=True, null=True)
    profiat_username = models.CharField(max_length=100, blank=True, null=True)
    profiat_email = models.CharField(max_length=100, blank=True, null=True)

    tg_id = models.CharField(max_length=100, blank=True, null=True)
    tg_username = models.CharField(max_length=500, blank=True, null=True)

    vk_id = models.CharField(max_length=100, blank=True, null=True)
    vk_username = models.CharField(max_length=500, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    otp_key = models.CharField(max_length=300, blank=True, null=True)
    enable_otp = models.BooleanField(default=False)


class Ticket(models.Model):

    source_selector = (
        ('telegram', 'Телеграм'),
        ('widget', 'Виджет')
    )

    uuid = models.UUIDField(primary_key=True, max_length=40, default=uuid.uuid4, editable=False, unique=True)
    platform = models.ForeignKey(to=Platform, on_delete=models.PROTECT)
    source = models.CharField(max_length=50, choices=source_selector)
    tg_user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="tg_user")
    status = models.CharField(max_length=50)
    date_created = models.DateTimeField(auto_now_add=True)
    date_closed = models.DateTimeField(blank=True, null=True)
    date_last_message = models.DateTimeField(blank=True, null=True)

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

    def get_user_source(self):
        return self.tg_user.source


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

    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    sender = models.CharField(max_length=20, choices=sender_selector)
    employee = models.ForeignKey(to=User, on_delete=models.PROTECT, blank=True, null=True, related_name='ticket_message_employee')
    tg_user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='ticket_message_client')
    sending_state = models.CharField(max_length=50)
    message_to_reply = models.ForeignKey(to='TicketMessage', on_delete=models.CASCADE, blank=True, null=True)
    deleted = models.BooleanField(default=False)
    message_text = models.TextField()
    content_type = models.CharField(max_length=20)
    read_by_received = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    vk_message_id = models.CharField(max_length=20, default="0")
    emotional = models.FloatField()

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

    def get_toxic(self):
        return self.emotional > 0.9

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
    message = models.ForeignKey(to=TicketMessage, on_delete=models.CASCADE)
    file = models.FileField(blank=True, null=True)
    name = models.CharField(max_length=500)
    content = models.BinaryField(blank=True, null=True)
    total_bytes = models.IntegerField()
    buf_size = models.IntegerField(default=512)
    received_bytes = models.IntegerField(default=0)
    uploaded = models.BooleanField(default=False)
    ext = models.CharField(max_length=50)
    telegram_file_id = models.CharField(max_length=100, blank=True, null=True)
    telegram_file_path = models.CharField(max_length=100, blank=True, null=True)
    vk_file_url = models.CharField(max_length=1000, blank=True, null=True)
    vk_upload_url = models.CharField(max_length=1000, blank=True, null=True)
    vk_file_id = models.CharField(max_length=100, blank=True, null=True)
    vk_owner_id = models.CharField(max_length=100, blank=True, null=True)
    vk_file_data = models.CharField(max_length=1000, blank=True, null=True)
    vk_file_type = models.CharField(max_length=1000, blank=True, null=True)


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


class TelegramBot(models.Model):
    class Meta:
        verbose_name = 'Telegram Bot'
        verbose_name_plural = 'Telegram Bots'

    platform = models.ForeignKey(to=Platform, on_delete=models.PROTECT)
    bot_apikey = models.CharField(max_length=300)
    webhook_connected = models.BooleanField(default=False)
    message_error = models.TextField(blank=True, null=True)


class DualFactorRequest(models.Model):
    class Meta:
        verbose_name = '2FA Request'
        verbose_name_plural = '2FA Request'

    action_selector = (
        ('registration', 'Регистрация'),
        ('login', 'Вход'),
        ('edit_password', 'Смена пароля'),
        ('edit_profile', 'Смена данных профиля'),
        ('enable_2fa', 'Активация 2FA'),
        ('restore', 'Смена пароля'),
    )

    factor_type_selector = (
        ('otp_auth', 'OTP Auth'),
        ('email_auth', 'E-mail Auth')
    )


    factor_type = models.CharField(max_length=100, verbose_name='Вид Factor', choices=factor_type_selector, default='sms_auth', blank=True, null=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Пользователь')
    action = models.CharField(max_length=100, verbose_name='Действие', choices=action_selector, blank=True, null=True)
    timestamp = models.IntegerField(default=0, verbose_name='Timestamp')
    otp = models.CharField(default=0, verbose_name='2FA Code')
    verified = models.BooleanField(verbose_name='Verified', default=False)
    attempt = models.IntegerField(verbose_name='Кол-во попыток', default=3)






