import datetime
from interfaces.bot import TradeBot
from entities.orders import Order
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from constants.index import PUBLISHER
import time


class ExampleStrategyV2(TradeBot):
    NIFTY_50 = "NIFTY 50"
    date = datetime.date.today() - datetime.timedelta(days=1)

    def entry_strategy(self):
        while True:
            nifty_live = self.zerodha.live_data(self.NIFTY_50)
            index_historical = self.zerodha.historical_data_index()

            print(index_historical.nifty)
            print(index_historical.bank_nifty)

            print(nifty_live)

            ticker = "NIFTY2211318150CE"
            ticker_live = self.zerodha.live_data(ticker)

            trade = Trade(
                TradeEndpoint.MARKET_ORDER_BUY,
                ticker,
                "NFO",
                50,
                TradeTag.ENTRY,
                PUBLISHER,
                ticker_live.last_price,
                ticker_live.depth.sell[1].price,
                ticker_live.last_price,
                TradeType.INDEXOPT,
                1800,
            )
            self.enter_trade(trade)

            time.sleep(300)

    def exit_strategy(self, order: Order):
        profit_price = order.average_entry_price * (110 / 100)

        trade = Trade(
            TradeEndpoint.MARKET__ORDER_SELL,
            order.trading_symbol,
            order.exchange,
            order.total_quantity,
            TradeTag.EXIT,
            PUBLISHER,
            order.average_entry_price,
            profit_price,
            profit_price,
            TradeType.INDEXOPT,
            1800,
        )

        self.exit_trade(trade)
