from unittest import TestCase, mock
from entities.publisher import Publisher
from entities.trade import Trade, TradeTag, TradeType


class TestPublisher(TestCase):
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
    @mock.patch("websocket.WebSocket.send")
    def test_publish_trade(self, ws_send_mock: mock.Mock, ws_connect_mock: mock.Mock):
        publisher = Publisher("ws://publisher_mock")

        publisher.publish_trade(self.trade_mock)

        ws_connect_mock.assert_called_once_with("ws://publisher_mock")
        ws_send_mock.assert_called_once_with(self.trade_mock.json())
