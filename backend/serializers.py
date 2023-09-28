from rest_framework import serializers

from backend.models import Ticket, TicketMessage

class TicketMessageSerializer(serializers.ModelSerializer):
    chat_id = serializers.CharField(source='get_ticket_id', read_only=True)
    sender_id = serializers.CharField(source='get_sender_id', read_only=True)
    is_outgoing = serializers.ReadOnlyField(source=serializers.SerializerMethodField('get_is_outgoing'))
    content = serializers.ReadOnlyField(source='message_text')
    media = serializers.ReadOnlyField(source='get_file')
    date = serializers.ReadOnlyField(source='get_date')

    def get_is_outgoing(self, obj):
        user_type = self.context.get("from_user_type")
        if user_type == 'support':
            return 'get_is_outgoing_support'
        else:
            return 'get_is_outgoing_client'

    class Meta:
        fields = ('id', 'chat_id', 'sending_state', 'sender_id', 'is_outgoing', 'content', 'media', 'date')
        model = TicketMessage


class TicketClientMessageSerializer(TicketMessageSerializer):
    # is_outgoing = serializers.ReadOnlyField(source='get_is_outgoing_client')


class TicketSupportMessageSerializer(TicketMessageSerializer):
    # is_outgoing = serializers.ReadOnlyField(source='get_is_outgoing_support')


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

