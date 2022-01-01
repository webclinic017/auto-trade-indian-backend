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
        quantity: int,
        tag: TradeTag,
        publisher: str,
        entry_price: int,
        price: int,
        ltp: int,
        type: TradeType,
    ):
        self.endpoint: str = endpoint
        self.trading_symbol: str = trading_symbol
        self.exchange: str = exchange
        self.quantity: int = quantity
        self.tag: TradeTag = tag
        self.publisher: str = publisher
        self.entry_price: int = entry_price
        self.price: int = price
        self.ltp: int = ltp
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
