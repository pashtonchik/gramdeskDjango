from rest_framework import serializers

from backend.models import Ticket, Client


class TicketSerializer(serializers.ModelSerializer):
    count_unread_messages = serializers.ReadOnlyField(source='get_count_unread_messages')
    last_message = serializers.ReadOnlyField(source='get_last_message')
    user_name = serializers.ReadOnlyField(source='get_user_name')

    class Meta:
        exclude = ('tg_user', 'date_created', 'date_closed')
        model = Ticket


class ClientSerializer(serializers.ModelSerializer):
    closed_tickets = serializers.ReadOnlyField(source='get_count_tickets')
    date_added = serializers.ReadOnlyField(source='get_date_added')

    class Meta:
        exclude = ('is_blocked', )
        model = Client


class TicketMessageSerializer(serializers.ModelSerializer):
    chat_id = serializers.ReadOnlyField(source='get_ticket_id')
    sender_id = serializers.ReadOnlyField(source='get_sender_id')
    is_outgoing = serializers.ReadOnlyField(source='get_is_outgoing')
    content = serializers.ReadOnlyField(source='message_text')
    media = serializers.ReadOnlyField(source='get_file')
    date = serializers.ReadOnlyField(source='date_created')

    class Meta:
        fields = ('id', 'chat_id', 'sending_state', 'sender_id', 'is_outgoing', 'content', 'media', 'date')
        model = Client

