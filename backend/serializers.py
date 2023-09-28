from rest_framework import serializers

from backend.models import Ticket, TicketMessage

class ReplyToMessageSerializer(serializers.ModelSerializer):
    chat_id = serializers.CharField(source='get_ticket_id', read_only=True)
    sender_id = serializers.CharField(source='get_sender_id', read_only=True)
    content = serializers.ReadOnlyField(source='message_text')
    is_outgoing = serializers.SerializerMethodField('get_is_outgoing')
    media = serializers.ReadOnlyField(source='get_file')
    date = serializers.ReadOnlyField(source='get_date')


    class Meta:
        fields = ('id', 'chat_id', 'sending_state', 'sender_id', 'is_outgoing', 'content', 'media', 'date')
        model = TicketMessage


class TicketMessageSerializer(ReplyToMessageSerializer):
    chat_id = serializers.CharField(source='get_ticket_id', read_only=True)
    sender_id = serializers.CharField(source='get_sender_id', read_only=True)
    content = serializers.ReadOnlyField(source='message_text')
    reply_to_message = ReplyToMessageSerializer()
    is_outgoing = serializers.SerializerMethodField('get_is_outgoing')
    media = serializers.ReadOnlyField(source='get_file')
    date = serializers.ReadOnlyField(source='get_date')


    def get_is_outgoing(self, obj):
        user_type = self.context.get("from_user_type")
        if user_type == 'support':
            return obj.get_is_outgoing_support()
        else:
            return obj.get_is_outgoing_client()

    class Meta:
        fields = ('id', 'chat_id', 'sending_state', 'sender_id', 'is_outgoing', 'content', 'media', 'date', "reply_to_message")
        model = TicketMessage


class TicketSerializer(serializers.ModelSerializer):
    count_unread_messages = serializers.ReadOnlyField(source='get_count_unread_messages')
    last_message = serializers.ReadOnlyField(source='get_last_message')
    user_name = serializers.ReadOnlyField(source='get_user_name')

    class Meta:
        exclude = ('tg_user', 'date_created', 'date_closed')
        model = Ticket


# class ClientSerializer(serializers.ModelSerializer):
#     uuid = serializers.CharField(read_only=True)
#     closed_tickets = serializers.ReadOnlyField(source='get_count_tickets')
#     date_added = serializers.ReadOnlyField(source='get_date_added')
#
#     class Meta:
#         exclude = ('is_blocked', )
#         model = Client

