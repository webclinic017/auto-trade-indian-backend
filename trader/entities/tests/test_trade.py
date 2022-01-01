from unittest import TestCase
from entities.trade import Trade, TradeTag, TradeType
import json


class TestTrade(TestCase):
    """
    Testing the Trade entity
    """

    def setUp(self) -> None:
        self.mock_trade = {
            "endpoint": "/mock_endpoint",
            "trading_symbol": "NIFTYMOCK",
            "exchange": "NSE",
            "quantity": 100,
            "tag": TradeTag.ENTRY,
            "publisher": "ws://mock_publisher",
            "entry_price": 107,
            "price": 107,
            "ltp": 110,
            "type": TradeType.INDEXOPT,
        }

    def test_trade_entity_initialized_empty(self):
        self.assertRaises(TypeError, Trade)

    def test_trade_entity_initialized_with_parameters(self):
        trade = Trade(**self.mock_trade)

        self.assertEqual(trade.endpoint, "/mock_endpoint")
        self.assertEqual(trade.trading_symbol, "NIFTYMOCK")
        self.assertEqual(trade.exchange, "NSE")
        self.assertEqual(trade.quantity, 100)
        self.assertEqual(trade.tag.value, "ENTRY")
        self.assertEqual(trade.publisher, "ws://mock_publisher")
        self.assertEqual(trade.entry_price, 107)
        self.assertEqual(trade.price, 107)
        self.assertEqual(trade.ltp, 110)
        self.assertEqual(trade.type.value, "INDEXOPT")

    def test_trade_entity_json(self):
        trade = Trade(**self.mock_trade)
        mock_trade = {
            **self.mock_trade,
            "tag": self.mock_trade["tag"].value,
            "type": self.mock_trade["type"].value,
        }

        self.assertEqual(trade.json(), json.dumps(mock_trade))
