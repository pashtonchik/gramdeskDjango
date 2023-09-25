from channels.middleware import BaseMiddleware


class HeartbeatMiddleware(BaseMiddleware):
    def __init__(self, *args, **kwargs):
        super(HeartbeatMiddleware, self).__init__(*args, **kwargs)
        self.ping_interval = 30  # Interval in seconds between heartbeats

    def process_request(self, request):
        self.setup_heartbeat(request)

    def process_message(self, message):
        self.setup_heartbeat(message)

    def setup_heartbeat(self, channel):
        def send_heartbeat():
            channel.send({"text": "heartbeat"})

        if hasattr(channel, "send"):
            # WebSocket connection
            channel.send_heartbeat = send_heartbeat
        else:
            # Other channel types (e.g., HTTP)
            channel.send = send_heartbeat

        if hasattr(channel, "on_message"):
            # WebSocket consumer
            old_on_message = channel.on_message

            def new_on_message(message):
                channel.send_heartbeat()
                old_on_message(message)

            channel.on_message = new_on_message