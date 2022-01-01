from unittest import TestCase
from entities.zerodha import OHLC


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
