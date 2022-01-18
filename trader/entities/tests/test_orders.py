from unittest import TestCase, mock
from entities.orders import OrderExecutor, OrderExecutorType
from entities.trade import Trade, TradeTag, TradeType


class TestOrders(TestCase):
    def setUp(self) -> None:
        self.trade_mock = Trade(
            "endpoint/mock",
            "NIFTYMOCK",
            "NSE",
            10,
            TradeTag.ENTRY,
            "ws://publisher_mock",
            121,
            121,
            111,
            TradeType.INDEXOPT,
        )

    @mock.patch("websocket.WebSocket.connect")
    def test_order_executor_enter_order(self, ws_mock: mock.Mock):
        order_executor = OrderExecutor("ws://publisher_mock")

        ws_mock.assert_called_once()
        ws_mock.assert_called_with("ws://publisher_mock")

        order_executor.enter_order(self.trade_mock)

        self.assertIn("NIFTYMOCK", order_executor.entries)

        self.assertEqual(order_executor.entries["NIFTYMOCK"].average_entry_price, 121)
        self.assertEqual(order_executor.entries["NIFTYMOCK"].exchange, "NSE")
        self.assertEqual(order_executor.entries["NIFTYMOCK"].total_quantity, 10)
        self.assertEqual(
            order_executor.entries["NIFTYMOCK"].trading_symbol, "NIFTYMOCK"
        )

    @mock.patch("websocket.WebSocket.connect")
    def test_order_executor_enter_multiple_order(self, ws_connect_mock: mock.Mock):
        order_executor = OrderExecutor("ws://publisher_mock")

        ws_connect_mock.assert_called_once()
        ws_connect_mock.assert_called_with("ws://publisher_mock")

        trade_mock = self.trade_mock

        order_executor.enter_order(trade_mock)

        self.assertIn("NIFTYMOCK", order_executor.entries)
        self.assertEqual(order_executor.entries["NIFTYMOCK"].average_entry_price, 121)
        self.assertEqual(order_executor.entries["NIFTYMOCK"].exchange, "NSE")
        self.assertEqual(order_executor.entries["NIFTYMOCK"].total_quantity, 10)
        self.assertEqual(
            order_executor.entries["NIFTYMOCK"].trading_symbol, "NIFTYMOCK"
        )

        trade_mock.entry_price = 120

        order_executor.enter_order(trade_mock)
        self.assertAlmostEqual(
            order_executor.entries["NIFTYMOCK"].average_entry_price, (120 + 121) / 2
        )
        self.assertEqual(order_executor.entries["NIFTYMOCK"].exchange, "NSE")
        self.assertEqual(order_executor.entries["NIFTYMOCK"].total_quantity, 20)
        self.assertEqual(
            order_executor.entries["NIFTYMOCK"].trading_symbol, "NIFTYMOCK"
        )

    @mock.patch("websocket.WebSocket.connect")
    @mock.patch("entities.publisher.Publisher.publish_trade")
    def test_enter_trade_multiple_trades(
        self, publish_trade_mock: mock.Mock, ws_connect_mock: mock.Mock
    ):
        order_executor = OrderExecutor("ws://publisher_mock")

        ws_connect_mock.assert_called_once_with("ws://publisher_mock")

        order_executor.enter_trade(self.trade_mock)
        publish_trade_mock.assert_called_once_with(self.trade_mock)

        publish_trade_mock.reset_mock()

        order_executor.enter_trade(self.trade_mock)
        publish_trade_mock.assert_called_once_with(self.trade_mock)

    @mock.patch("websocket.WebSocket.connect")
    def test_enter_order_single_mode(self, ws_connect_mock: mock.Mock):
        order_executor = OrderExecutor("ws://publisher_mock", OrderExecutorType.SINGLE)

        ws_connect_mock.assert_called_once_with("ws://publisher_mock")

        trade_mock = self.trade_mock
        order_executor.enter_order(trade_mock)

        self.assertIn("NIFTYMOCK", order_executor.entries)
        self.assertEqual(order_executor.entries["NIFTYMOCK"].average_entry_price, 121)
        self.assertEqual(order_executor.entries["NIFTYMOCK"].exchange, "NSE")
        self.assertEqual(order_executor.entries["NIFTYMOCK"].total_quantity, 10)
        self.assertEqual(
            order_executor.entries["NIFTYMOCK"].trading_symbol, "NIFTYMOCK"
        )

        trade_mock.entry_price = 120
        trade_mock.quantity = 11
        order_executor.enter_order(trade_mock)

        self.assertIn("NIFTYMOCK", order_executor.entries)
        self.assertEqual(order_executor.entries["NIFTYMOCK"].average_entry_price, 121)
        self.assertEqual(order_executor.entries["NIFTYMOCK"].exchange, "NSE")
        self.assertEqual(order_executor.entries["NIFTYMOCK"].total_quantity, 10)
        self.assertEqual(
            order_executor.entries["NIFTYMOCK"].trading_symbol, "NIFTYMOCK"
        )
        self.assertNotAlmostEqual(
            order_executor.entries["NIFTYMOCK"].average_entry_price, (120 + 121) / 2
        )
        self.assertNotEqual(order_executor.entries["NIFTYMOCK"].total_quantity, 21)
