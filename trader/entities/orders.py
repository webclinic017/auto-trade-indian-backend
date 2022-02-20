from typing import Dict, Iterator
from entities.publisher import Publisher
from entities.trade import Trade
from constants.index import PUBLISHER
from pymongo import MongoClient
from pymongo.database import Database, Collection
from enum import Enum
import datetime


class OrderExecutorType(Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    STRICT = "strict"


class Order:
    def __init__(
        self,
        trading_symbol,
        exchange,
        total_quantity,
        average_entry_price,
        profit_percent=5,
        exit_time="",
    ):
        self.trading_symbol = trading_symbol
        self.exchange = exchange
        self.total_quantity = total_quantity
        self.average_entry_price = average_entry_price
        self.profit_percent = profit_percent
        self._exit_time = str(exit_time)

    @property
    def exit_time(self):
        if self.exit_time:
            return datetime.datetime.strptime(self.exit_time, "%H:%M:%S")

        return None

    def add_trade(self, trade: Trade):
        self.total_quantity += trade.quantity
        self.average_entry_price += trade.entry_price

        self.average_entry_price /= 2


class OrderDatabase(MongoClient):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

        self.db: Database = self["autotrade"]
        self.collection: Collection = self.db[name]

    def create_order(self, order: Order) -> None:
        _filter = {"trading_symbol": order.trading_symbol}

        _update = {
            "$set": {
                "trading_symbol": order.trading_symbol,
                "average_entry_price": order.average_entry_price,
                "exchange": order.exchange,
                "total_quantity": order.total_quantity,
                "profit_percent": order.profit_percent,
                "exit_time": order._exit_time,
            }
        }

        self.collection.update_one(_filter, _update, upsert=True)

    def get_order(self, trading_symbol) -> Order:
        order = self.collection.find_one({"trading_symbol": trading_symbol})

        return Order(
            order["trade"],
            order["exchange"],
            order["total_quantity"],
            order["average_entry_price"],
            order["profit_percent"],
            order["exit_time"],
        )

    def delete_order(self, trading_symbol) -> None:
        self.collection.delete_one({"trading_symbol": trading_symbol})

    def orders(self) -> Iterator[Order]:
        if self.collection.count_documents({}) > 0:
            for order in self.collection.find():
                if order:
                    yield Order(
                        order["trading_symbol"],
                        order["exchange"],
                        order["total_quantity"],
                        order["average_entry_price"],
                        order["profit_percent"],
                        order["exit_time"],
                    )
        else:
            return []


class OrderExecutor:
    def __init__(
        self,
        publisher_uri: str = PUBLISHER,
        mode: OrderExecutorType = OrderExecutorType.MULTIPLE,
    ):
        self.entries: Dict[str, Order] = dict()
        self.__db = OrderDatabase(name=self.name, host="mongodb://db")

        self.publisher: Publisher = Publisher(publisher_uri)
        self.mode: OrderExecutorType = mode

        self.entered_tickers = set()

    def enter_order(self, trade: Trade, options: dict = {}):
        if trade.trading_symbol not in self.entries:
            if self.mode == OrderExecutorType.STRICT:
                if trade.trading_symbol not in self.entered_tickers:
                    self.entered_tickers.add(trade.trading_symbol)

                    flag = True
                else:
                    flag = False
            else:
                flag = True

            if flag:
                order = Order(
                    trade.trading_symbol,
                    trade.exchange,
                    trade.quantity,
                    trade.entry_price,
                    options.get("profit_percent", 5),
                    options.get("exit_time", ""),
                )
                # self.entries[trade.trading_symbol]
                self.__db.create_order(order)

                return True
        else:
            if self.mode == OrderExecutorType.MULTIPLE:
                order = self.__db.get_order(trade.trading_symbol).add_trade(trade)
                self.__db.create_order(order)
                # self.entries[trade.trading_symbol].add_trade(trade)
                return True

        return False

    def clean_order(self, trading_symbol: str):
        # del self.entries[trading_symbol]
        self.__db.delete_order(trading_symbol)

    def get_orders(self) -> Iterator[Order]:
        # for trading_symbol in self.entries:
        #     yield self.entries[trading_symbol]
        return self.__db.orders()

    def enter_trade(self, trade: Trade, options: dict = {}):
        if self.enter_order(trade, options):
            # publish the trade to the publisher
            self.publisher.publish_trade(trade)

    def exit_trade(self, trade: Trade):
        self.clean_order(trade.trading_symbol)

        # publish trade to publisher
        self.publisher.publish_trade(trade)
