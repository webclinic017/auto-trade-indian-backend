from kiteconnect.connect import KiteConnect
import os


class TradeBot:
    def __init__(self, name):
        self.name = name
        self.kite = KiteConnect(
            api_key=os.environ["API_KEY"], access_token=os.environ["ACCESS_TOKEN"]
        )
