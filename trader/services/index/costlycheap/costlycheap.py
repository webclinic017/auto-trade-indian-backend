from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from interfaces.bot import TradeBot
from entities.orders import Order
import datetime
import time
import math

LiveDataException = Exception("live data exception")


class CostlyCheap(TradeBot):
    def get_option_type(self, tradingsymbol):
        if "CE" in tradingsymbol:
            return "CE"
        elif "PE" in tradingsymbol:
            return "PE"

        raise Exception("invalid ticker")

    def get_costly_cheap(self):
        nifty_live = self.zerodha.live_data("NIFTY 50")

        ce_price = math.floor(nifty_live.last_price)
        pe_price = math.floor(nifty_live.last_price)

        while ce_price % 50 != 0:
            ce_price -= 1

        while pe_price % 50 != 0:
            pe_price += 1

        ce_ticker = "NIFTY" + self.year + self.month + self.week + str(ce_price) + "CE"
        pe_ticker = "NIFTY" + self.year + self.month + self.week + str(pe_price) + "PE"

        try:
            ce_live = self.zerodha.live_data(ce_ticker)
            pe_live = self.zerodha.live_data(pe_ticker)
        except Exception:
            raise LiveDataException

        ce_diff = abs(ce_live.last_price - abs(nifty_live.last_price - ce_price))
        pe_diff = abs(pe_live.last_price - abs(nifty_live.last_price - pe_price))

        if ce_diff > pe_diff:
            costly = ce_ticker
            cheap = pe_ticker
        else:
            costly = pe_ticker
            cheap = ce_ticker

        return costly, cheap

    def entry_strategy(self):
        while True:
            if datetime.datetime.now().time() < self.start_time:
                continue

            for tick in self.ticker_generator.index(5):
                try:
                    _, cheap = self.get_costly_cheap(tick)
                except LiveDataException:
                    continue

                quote = self.zerodha.live_data(cheap)
                trade = Trade(
                    endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                    trading_symbol=cheap,
                    exchange="NFO",
                    quantity=25,
                    tag=TradeTag.ENTRY,
                    publisher="",
                    entry_price=quote.last_price,
                    price=quote.depth.sell[1].price,
                    ltp=quote.last_price,
                    type=TradeType.INDEXOPT,
                )

                self.enter_trade(trade)

            time.sleep(300)

    def exit_strategy(self, order: Order):
        profit_price = (110 / 100) * order.average_entry_price

        try:
            quote = self.zerodha.live_data(order.trading_symbol)
        except Exception:
            return

        try:
            costly, _ = self.get_costly_cheap()
        except LiveDataException:
            return

        trade = Trade(
            TradeEndpoint.MARKET_ORDER_SELL,
            order.trading_symbol,
            "NFO",
            order.total_quantity,
            TradeTag.ENTRY,
            "",
            quote.last_price,
            quote.depth.buy[1].price,
            quote.last_price,
            TradeType.INDEXOPT,
            1800,
        )

        if self.get_option_type(order.trading_symbol) in costly:
            self.exit_trade(trade)
            return

        if quote.last_price >= profit_price:
            self.exit_trade(trade)
            return

    def start(self):
        current_time = datetime.datetime.now()
        current_minute = current_time.time().minute
        current_hour = current_time.time().hour

        if current_hour == 9 and current_minute < 30:
            current_minute = 30
        else:
            while current_minute % 5 != 0:
                current_minute += 1

            current_minute += 1

            if current_minute > 60:
                current_hour += 1

            current_hour %= 24
            current_minute %= 60

        self.start_time = datetime.time(current_hour, current_minute, 10)

        super().start()
