from interfaces.bot import TradeBot
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.orders import Order
import datetime
import time
from entities.ticker import TickerGenerator


class First5Min(TradeBot):
    def entry_strategy(self):
        while True:
            if datetime.datetime.now().time() < datetime.time(9, 30):
                continue

            
            for tick in self.ticker_generator.stocks():
                live_data = self.zerodha.live_data(tick.ticker.tradingsymbol)
                historical_data = self.zerodha.historical_data_today(
                    tick.ticker.tradingsymbol, HistoricalDataInterval.INTERVAL_5_MINUTE
                )

                first_5min_ohlc = historical_data[0]

                if (
                    # first_5min_ohlc.open == first_5min_ohlc.low
                    # and
                    live_data.last_price
                    < first_5min_ohlc.high
                ):
                    live_data_der = self.zerodha.live_data(tick.ce_ticker.tradingsymbol)

                    trade = Trade(
                        endpoint=TradeEndpoint.LIMIT_ORDER_BUY,
                        trading_symbol=tick.ce_ticker.tradingsymbol,
                        exchange="NFO",
                        quantity=tick.ce_ticker.lot_size,
                        tag=TradeTag.ENTRY,
                        publisher="",
                        entry_price=live_data_der.last_price,
                        price=live_data_der.depth.buy[1].price,
                        ltp=live_data_der.last_price,
                        type=TradeType.STOCKOPT,
                    )

                    self.enter_trade(trade)

            time.sleep(60)

    def exit_strategy(self, order: Order):
        entry_price = order.average_entry_price
        profit = (110 / 100) * entry_price
        ticker_der = order.trading_symbol

        live_data = self.zerodha.live_data(ticker_der)
        historical_data = self.zerodha.historical_data_today(
            ticker_der, HistoricalDataInterval.INTERVAL_5_MINUTE
        )

        trade = Trade(
            endpoint=TradeEndpoint.LIMIT_ORDER_SELL,
            trading_symbol=ticker_der,
            exchange="NFO",
            quantity=1,
            tag=TradeTag.EXIT,
            publisher="",
            entry_price=live_data.last_price,
            price=live_data.depth.buy[1].price,
            ltp=live_data.last_price,
            type=TradeType.STOCKOPT,
        )

        if "CE" in ticker_der:
            if live_data.last_price < historical_data[0].low:
                self.exit_trade(trade)
                return

        if "PE" in ticker_der:
            if live_data.last_price > historical_data[0].high:
                self.exit_trade(trade)
                return

        if live_data.last_price >= profit:
            self.exit_trade(trade)
            return

    def start(self):
        self.ticker_generator = TickerGenerator("22", "JAN")

        super().start()