from typing import Dict, Iterator, List
from entities.publisher import Publisher
from entities.trade import Trade
from constants.index import PUBLISHER
from pymongo import MongoClient
from pymongo.database import Database, Collection
from bson import ObjectId
from enum import Enum
import datetime


class OrderExecutorType(Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    STRICT = "strict"


class StrategyType(Enum):
    NORMAL = "normal"
    HYBRID = "hybrid"


class Order:
    def __init__(
        self,
        trading_symbol,
        exchange,
        total_quantity,
        average_entry_price,
        parent_ticker,
        profit_percent=5,
        exit_time="",
    ):
        self.trading_symbol = trading_symbol
        self.exchange = exchange
        self.total_quantity = total_quantity
        self.average_entry_price = average_entry_price
        self.profit_percent = profit_percent
        self._exit_time = str(exit_time)
        self.parent_ticker = parent_ticker

    @property
    def exit_time(self):
        if self._exit_time:
            return datetime.datetime.strptime(self._exit_time, "%H:%M:%S")

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
        self.hybrid_collection: Collection = self.db[name + "_hybrid"]

    def create_order(self, order: Order) -> ObjectId:
        _filter = {"trading_symbol": order.trading_symbol}

        _update = {
            "$set": {
                "trading_symbol": order.trading_symbol,
                "average_entry_price": order.average_entry_price,
                "exchange": order.exchange,
                "total_quantity": order.total_quantity,
                "profit_percent": order.profit_percent,
                "exit_time": order._exit_time,
                "parent_ticker": order.parent_ticker,
            }
        }

        update = self.collection.update_one(_filter, _update, upsert=True)
        return update.raw_result["_id"]

    def get_order(self, trading_symbol) -> Order:
        order = self.collection.find_one({"trading_symbol": trading_symbol})

        return Order(
            order["trade"],
            order["exchange"],
            order["total_quantity"],
            order["average_entry_price"],
            order["profit_percent"],
            order["exit_time"],
            order["parent_ticker"],
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
                        order["parent_ticker"],
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
        """
        parameters:
            trade: Trade
            options: {"profit_percent":?, "exit_time":?}
        """
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
                    trade.parent_ticker,
                )
                # self.entries[trade.trading_symbol]
                orderid = self.__db.create_order(order)

                return True, orderid
        else:
            if self.mode == OrderExecutorType.MULTIPLE:
                order = self.__db.get_order(trade.trading_symbol).add_trade(trade)
                orderid = self.__db.create_order(order)
                # self.entries[trade.trading_symbol].add_trade(trade)
                return True, orderid

        return False, None

    def clean_order(self, trading_symbol: str):
        # del self.entries[trading_symbol]
        self.__db.delete_order(trading_symbol)

    def get_orders(self) -> Iterator[Order]:
        # for trading_symbol in self.entries:
        #     yield self.entries[trading_symbol]
        return self.__db.orders()

    def enter_trade(self, trade: Trade, options: dict = {}):
        should_trade, _ = self.enter_order(trade, options)

        if should_trade:
            # publish the trade to the publisher
            self.publisher.publish_trade(trade)

    def enter_hybrid_trade(self, trades: List[Trade], options={}):
        order_ids = []

        for trade in trades:
            _, orderid = self.enter_trade(trade, options)

            order_ids.append(orderid)

    def exit_trade(self, trade: Trade):
        self.clean_order(trade.trading_symbol)

        # publish trade to publisher
        self.publisher.publish_trade(trade)
