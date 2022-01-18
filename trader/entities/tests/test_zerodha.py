import datetime
from unittest import TestCase
from entities.zerodha import OHLC, Depth, LiveTicker


class TestOHLC(TestCase):
    def setUp(self) -> None:
        self.ohlc_mock = {"open": 11, "high": 21, "low": 10, "close": 15}

    def test_ohlc_initialized_empty(self):
        self.assertRaises(TypeError, OHLC)

    def test_ohlc_initialized_with_empty_dict(self):
        ohlc = OHLC({})

        self.assertEqual(ohlc.open, None)
        self.assertEqual(ohlc.high, None)
        self.assertEqual(ohlc.low, None)
        self.assertEqual(ohlc.close, None)

    def test_ohlc_initialized_with_ohlc_dict(self):
        ohlc = OHLC(self.ohlc_mock)

        self.assertEqual(ohlc.open, 11)
        self.assertEqual(ohlc.high, 21)
        self.assertEqual(ohlc.low, 10)
        self.assertEqual(ohlc.close, 15)


class TestDepth(TestCase):
    def setUp(self) -> None:
        self.depth_mock = {
            "buy": [{"price": 21, "orders": 1000, "quantity": 10}],
            "sell": [{"price": 15, "orders": 500, "quantity": 7}],
        }

    def test_depth_initialize(self):
        depth = Depth(self.depth_mock)

        self.assertEqual(depth.buy[0].price, 21)
        self.assertEqual(depth.buy[0].quantity, 10)
        self.assertEqual(depth.buy[0].orders, 1000)

        self.assertEqual(depth.sell[0].price, 15)
        self.assertEqual(depth.sell[0].quantity, 7)
        self.assertEqual(depth.sell[0].orders, 500)


class TestLiveTicker(TestCase):
    def setUp(self) -> None:
        self.live_mock_ticker = {
            "instrument_token": 408065,
            "timestamp": datetime.datetime.fromisoformat("2021-06-08 15:45:56"),
            "last_trade_time": datetime.datetime.fromisoformat("2021-06-08 15:45:52"),
            "last_price": 1412.95,
            "last_quantity": 5,
            "buy_quantity": 0,
            "sell_quantity": 5191,
            "volume": 7360198,
            "average_price": 1412.47,
            "oi": 110,
            "net_change": 50,
            "ohlc": {"open": 1396, "high": 1421.75, "low": 1395.55, "close": 1389.65},
            "depth": {
                "buy": [
                    {"price": 123.4, "quantity": 10, "orders": 11},
                ],
                "sell": [
                    {"price": 141, "quantity": 51, "orders": 12},
                ],
            },
        }

    def test_live_ticker_initialize(self):
        live_ticker = LiveTicker(self.live_mock_ticker)

        self.assertEqual(live_ticker.instrument_token, 408065)
        self.assertEqual(
            live_ticker.timestamp,
            datetime.datetime.fromisoformat("2021-06-08 15:45:56"),
        )
        self.assertEqual(
            live_ticker.last_trade_time,
            datetime.datetime.fromisoformat("2021-06-08 15:45:52"),
        )
        self.assertEqual(live_ticker.last_price, 1412.95)
        self.assertEqual(live_ticker.last_quantity, 5)
        self.assertEqual(live_ticker.buy_quantity, 0)
        self.assertEqual(live_ticker.sell_quantity, 5191)
        self.assertEqual(live_ticker.volume, 7360198)
        self.assertEqual(live_ticker.average_price, 1412.47)
        self.assertEqual(live_ticker.oi, 110)
        self.assertEqual(live_ticker.ohlc.open, 1396)
        self.assertEqual(live_ticker.ohlc.high, 1421.75)
        self.assertEqual(live_ticker.ohlc.low, 1395.55)
        self.assertEqual(live_ticker.ohlc.close, 1389.65)
        self.assertEqual(live_ticker.depth.buy[0].orders, 11)
        self.assertEqual(live_ticker.depth.buy[0].price, 123.4)
        self.assertEqual(live_ticker.depth.buy[0].quantity, 10)
        self.assertEqual(live_ticker.depth.sell[0].orders, 12)
        self.assertEqual(live_ticker.depth.sell[0].price, 141)
        self.assertEqual(live_ticker.depth.sell[0].quantity, 51)
