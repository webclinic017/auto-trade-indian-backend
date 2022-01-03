import datetime
import math
from entities.zerodha import HistoricalDataInterval
from interfaces.tradeapp import TradeApp
import time
from interfaces.bot import TradeBot
from entities.orders import Order
from entities.trade import Trade, TradeTag, TradeType
from constants.index import PUBLISHER


class ExampleStrategyV2(TradeBot):
    NIFTY_50 = "NIFTY 50"

    def entry_strategy(self):
        nifty_live = self.zerodha.live_data(self.NIFTY_50)

        ce_price = math.floor(nifty_live.last_price)
        pe_price = math.floor(nifty_live.last_price)

        while ce_price % 50 != 0:
            ce_price -= 1

        while pe_price % 50 != 0:
            pe_price += 1

        ce_ticker = "NIFTY22106" + str(ce_price) + "CE"
        ce_ticker_live = self.zerodha.live_data(ce_ticker)

        pe_ticker = "NIFTY22106" + str(pe_price) + "PE"
        pe_ticker_live = self.zerodha.live_data(pe_ticker)

        trade = Trade(
            "",
            ce_ticker,
            "NSE",
            1,
            TradeTag.ENTRY,
            PUBLISHER,
            ce_ticker_live.last_price,
            ce_ticker_live.depth.sell[1].price,
            ce_ticker_live.last_price,
            TradeType.INDEXOPT,
        )
        self.enter_trade(trade)

        trade = Trade(
            "",
            pe_ticker,
            "NSE",
            1,
            TradeTag.ENTRY,
            PUBLISHER,
            pe_ticker_live.last_price,
            pe_ticker_live.depth.buy[1].price,
            pe_ticker_live.last_price,
            TradeType.INDEXOPT,
        )
        self.enter_trade(trade)

    def exit_strategy(self, order: Order):
        profit_price = order.average_entry_price * (110 / 100)

        trade = Trade(
            "",
            order.trading_symbol,
            order.exchange,
            order.total_quantity,
            TradeTag.EXIT,
            PUBLISHER,
            order.average_entry_price,
            profit_price,
            profit_price,
            TradeType.INDEXOPT,
        )

        self.exit_trade(trade)
