from django.contrib import admin

from backend.models import *


@admin.register(User)
class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = ('date_added', )
    ordering = ('-date_added', )


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin')


@admin.register(DualFactorRequest)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('factor_type', 'user', 'action', 'timestamp', 'otp', 'verified')


@admin.register(Ticket)
class PayMethodAdmin(admin.ModelAdmin):
    list_display = ('tg_user', 'status', 'date_created', 'date_closed')
    readonly_fields = ('date_created',)


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('tg_user', 'ticket', 'message_text', 'date_created', 'deleted')
    readonly_fields = ('date_created', )
    ordering = ('-date_created', )


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('message', )
    exclude = ('content', )


@admin.register(JWTToken)
class JWTTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'active', 'date_created')


@admin.register(SocketConnection)
class SocketConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'active', 'date_created', 'date_closed')


@admin.register(TelegramBot)
class SocketConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'bot_apikey')

