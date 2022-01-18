from entities.trade import Trade
import websocket


class Publisher:
    def __init__(self, publisher_uri: str):
        self.publisher_uri = publisher_uri

    def publish_trade(self, trade: Trade):
        payload = trade.json()
        print(payload)

        ws = websocket.create_connection(self.publisher_uri)
        ws.send(payload)
        ws.close()
