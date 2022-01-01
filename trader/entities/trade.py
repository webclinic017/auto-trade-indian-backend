from enum import Enum
import json


class TradeType(Enum):
    INDEXOPT = "INDEXOPT"
    INDEXFUT = "INDEXFUT"
    STOCKOPT = "STOCKOPT"
    STOCK = "STOCK"
    STOCKFUT = "STOCKFUT"


class TradeTag(Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class Trade:
    def __init__(
        self,
        endpoint: str,
        trading_symbol: str,
        exchange: str,
        quantity: str,
        tag: TradeTag,
        publisher: str,
        entry_price: str,
        price: str,
        ltp: str,
        type: TradeType,
    ):
        self.endpoint: str = endpoint
        self.trading_symbol: str = trading_symbol
        self.exchange: str = exchange
        self.quantity: str = quantity
        self.tag: TradeTag = tag
        self.publisher: str = publisher
        self.entry_price: str = entry_price
        self.price: str = price
        self.ltp: str = ltp
        self.type: TradeType = type

    def json(self):
        return json.dumps(
            {
                "endpoint": self.endpoint,
                "trading_symbol": self.trading_symbol,
                "exchange": self.exchange,
                "quantity": self.quantity,
                "tag": self.tag.value,
                "publisher": self.publisher,
                "entry_price": self.entry_price,
                "price": self.price,
                "ltp": self.ltp,
                "type": self.type.value,
            }
        )
