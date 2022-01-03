import datetime
from kiteconnect.connect import KiteConnect
import os
import time
from trader.entities.orders import Order, OrderExecutor, OrderExecutorType
from trader.interfaces.constants import PUBLISHER


class TradeBot(OrderExecutor):
    def __init__(
        self,
        name: str,
        entry_time_start: datetime.datetime = datetime.time(9, 30),
        entry_time_end: datetime.datetime = datetime.time(15, 10),
        publisher_uri: str = PUBLISHER,
        mode: OrderExecutorType = OrderExecutorType.MULTIPLE,
    ):
        super().__init__(publisher_uri=publisher_uri, mode=mode)
        self.name = name
        self.kite = KiteConnect(
            api_key=os.environ["API_KEY"], access_token=os.environ["ACCESS_TOKEN"]
        )
        self.entry_time_start = entry_time_start
        self.entry_time_end = entry_time_end

    def entry_strategy(self):
        raise NotImplementedError

    def exit_strategy(self, order: Order):
        raise NotImplementedError

    def _entry_strategy(self, interval=300):
        while True:
            time_now = datetime.datetime.now().time()
            if time_now < self.entry_time_start:
                continue

            if time_now > self.entry_time_end:
                return

            self.entry_strategy()
            time.sleep(interval)

    def _exit_strategy(self, interval=50):
        while True:
            tickers = self.entries.keys()

            for ticker in tickers:
                if ticker in self.entries:
                    self.exit_strategy(self.entries[ticker])

            time.sleep(interval)
