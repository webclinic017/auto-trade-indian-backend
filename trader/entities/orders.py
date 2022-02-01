from typing import Dict, Iterator
from entities.publisher import Publisher
from entities.trade import Trade
from constants.index import PUBLISHER
from enum import Enum


class OrderExecutorType(Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    STRICT = "strict"


class Order:
    def __init__(self, trading_symbol, exchange, total_quantity, average_entry_price):
        self.trading_symbol = trading_symbol
        self.exchange = exchange
        self.total_quantity = total_quantity
        self.average_entry_price = average_entry_price

    def add_trade(self, trade: Trade):
        self.total_quantity += trade.quantity
        self.average_entry_price += trade.entry_price

        self.average_entry_price /= 2


class OrderExecutor:
    def __init__(
        self,
        publisher_uri: str = PUBLISHER,
        mode: OrderExecutorType = OrderExecutorType.MULTIPLE,
    ):
        self.entries: Dict[str, Order] = dict()
        self.publisher: Publisher = Publisher(publisher_uri)
        self.mode: OrderExecutorType = mode

        self.entered_tickers = set()

    def enter_order(self, trade: Trade):
        if trade.trading_symbol not in self.entries:
                if self.mode == OrderExecutorType.STRICT and (trade.trading_symbol not in self.entered_tickers):
                    self.entered_tickers.add(trade.trading_symbol)
                    
                    flag = True
                elif self.mode == OrderExecutorType.STRICT and (trade.trading_symbol in self.entered_tickers):
                    flag = False
                elif self.mode != OrderExecutorType.STRICT:
                    flag = True
                
                if flag:
                    self.entries[trade.trading_symbol] = Order(
                        trade.trading_symbol,
                        trade.exchange,
                        trade.quantity,
                        trade.entry_price,
                    )
        else:
            if self.mode == OrderExecutorType.MULTIPLE:
                self.entries[trade.trading_symbol].add_trade(trade)

    def clean_order(self, trading_symbol: str):
        del self.entries[trading_symbol]

    def get_orders(self) -> Iterator[Order]:
        for trading_symbol in self.entries:
            yield self.entries[trading_symbol]

    def enter_trade(self, trade: Trade):
        self.enter_order(trade)

        # publish the trade to the publisher
        self.publisher.publish_trade(trade)

    def exit_trade(self, trade: Trade):
        self.clean_order(trade.trading_symbol)

        # publish trade to publisher
        self.publisher.publish_trade(trade)
