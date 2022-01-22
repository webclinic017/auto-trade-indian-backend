from entities.trade import Trade
import requests, json, os


class Publisher:
    def __init__(self, publisher_uri: str):
        self.publisher_uri = publisher_uri

    def publish_trade(self, trade: Trade):
        payload = trade.json()
        print(payload)

        AUTH_TOKEN = os.environ["AUTH_TOKEN"]
        requests.post(
            self.publisher_uri,
            json=json.loads(payload),
            headers={"Authorization": f"Token {AUTH_TOKEN}"},
        )
