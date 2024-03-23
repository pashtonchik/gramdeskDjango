from rest_framework import serializers

from backend.models import Ticket, TicketMessage, Attachment, User, Platform, TelegramBot

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
import logging

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from backend.models import JWTToken


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        logger = logging.getLogger("mylogger")
        logger.info("Whatever to log")
        token['username'] = user.username
        token['password'] = user.password
        token['id'] = user.id
        return token



class MyTokenRefreshSerializer(TokenRefreshSerializer):
    @classmethod
    def validate(self, attrs):

        refresh = self.token_class(attrs["refresh"])
        data = {"access": str(refresh.access_token)}

        refresh_token = OutstandingToken.objects.get(token=str(refresh))

        outstanding = JWTToken.objects.select_for_update().filter(user=refresh_token.user, active=True)
        outstanding.update(active=False)

        JWTToken.objects.create(
            user=refresh_token.user,
            jwt=refresh.access_token,
            refresh=OutstandingToken.objects.get(token=str(refresh))
        ).save()

        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()

        data["refresh"] = str(refresh)

        return data


class ReplyToMessageSerializer(serializers.ModelSerializer):
    chat_id = serializers.CharField(source='get_ticket_id', read_only=True)
    sender_id = serializers.CharField(source='get_sender_id', read_only=True)
    sender_username = serializers.CharField(source='get_sender_username', read_only=True)
    content = serializers.ReadOnlyField(source='message_text')
    is_outgoing = serializers.SerializerMethodField('get_is_outgoing')
    media = serializers.ReadOnlyField(source='get_files')
    date = serializers.ReadOnlyField(source='get_date')

    def get_is_outgoing(self, obj):
        user_type = self.context.get("from_user_type")
        if user_type == 'support':
            return obj.get_is_outgoing_support()
        else:
            return obj.get_is_outgoing_client()

    class Meta:
        fields = ('id', 'chat_id', 'sending_state', 'sender_id', 'sender_username', 'is_outgoing', 'content', 'media', 'date')
        model = TicketMessage


class TicketMessageSerializer(ReplyToMessageSerializer):
    message_to_reply = ReplyToMessageSerializer()


    def get_is_outgoing(self, obj):
        user_type = self.context.get("from_user_type")
        if user_type == 'support':
            return obj.get_is_outgoing_support()
        else:
            return obj.get_is_outgoing_client()

    class Meta:
        fields = ('id', 'chat_id', 'sending_state', 'sender_id', 'sender_username', 'is_outgoing', 'content', 'media', 'date', "message_to_reply")
        model = TicketMessage


class TicketSerializer(serializers.ModelSerializer):
    count_unread_messages = serializers.ReadOnlyField(source='get_count_unread_messages')
    last_message = serializers.SerializerMethodField('get_last_message')
    user_name = serializers.ReadOnlyField(source='get_user_name')

    class Meta:
        exclude = ('tg_user', 'date_created', 'date_closed', 'platform')
        model = Ticket

    def get_last_message(self, obj):
        return TicketMessageSerializer(obj.last_message, context=self.context).data if obj.last_message else []


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'total_bytes', 'received_bytes', 'ext', 'buf_size')
        model = Attachment


class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'source', 'tg_username', 'tg_id', 'is_blocked', 'date_added', 'username')
        model = User


class PlatformSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('uuid', 'name', 'description')
        model = Platform


class TelegramBotSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'bot_apikey', 'webhook_connected', 'message_error')
        model = TelegramBot



# class ClientSerializer(serializers.ModelSerializer):
#     uuid = serializers.CharField(read_only=True)
#     closed_tickets = serializers.ReadOnlyField(source='get_count_tickets')
#     date_added = serializers.ReadOnlyField(source='get_date_added')
#
#     class Meta:
#         exclude = ('is_blocked', )
#         model = Client

