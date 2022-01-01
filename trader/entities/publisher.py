from entities.trade import Trade
from websocket import WebSocket


class Publisher:
    def __init__(self, publisher_uri: str):
        self.publisher_uri = publisher_uri
        self.ws = WebSocket()

        self.ws.connect(self.publisher_uri)

    def publish_trade(self, trade: Trade):
        payload = trade.json()

        self.ws.send(payload)
