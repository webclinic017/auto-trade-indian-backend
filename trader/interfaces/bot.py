from kiteconnect.connect import KiteConnect
import os
import time
from entities.orders import Order, OrderExecutor, OrderExecutorType
from entities.zerodha import ZerodhaKite
from constants.index import PUBLISHER
import threading
import glob
import json


class TradeBot(OrderExecutor):
    def __init__(
        self,
        name: str,
        publisher_uri: str = PUBLISHER,
        mode: OrderExecutorType = OrderExecutorType.MULTIPLE,
    ):
        super().__init__(publisher_uri=publisher_uri, mode=mode)
        self.name = name

        self.kite = KiteConnect(
            api_key=os.environ["API_KEY"], access_token=os.environ["ACCESS_TOKEN"]
        )
        self.zerodha = ZerodhaKite(self.kite)

        self.data = {}
        for file in glob.glob("/app/data/*.json"):
            filename = file.split("/")[-1].split(".")[0]

            self.data[filename] = json.loads(open(file, "r").read())

    def entry_strategy(self):
        raise NotImplementedError

    def exit_strategy(self, order: Order):
        raise NotImplementedError

    def _exit_strategy(self, interval=10):
        while True:
            tickers = set(self.entries.keys()).copy()

            for ticker in tickers:
                if ticker in self.entries:
                    self.exit_strategy(self.entries[ticker])

            time.sleep(interval)

    def start(self):
        entry_thread = threading.Thread(target=self.entry_strategy)
        exit_thread = threading.Thread(target=self._exit_strategy)

        entry_thread.start()
        exit_thread.start()
