from interfaces.bot import TradeBot
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.orders import Order
import datetime
import math
import time


class BuyersSellers(TradeBot):
    NIFTY_50 = "NIFTY 50"
    BANK_NIFTY = "NIFTY BANK"

    def __init__(self, name: str, year: str, month: str, week: str):
        super(TradeBot, self).__init__(name)
        self.year = year
        self.month = month
        self.week = week

    def get_buy_sell_diff(self):
        nifty_live = self.zerodha.live_data(self.NIFTY_50)
        bank_nifty_live = self.zerodha.live_data(self.BANK_NIFTY)

        nifty_atm = (math.ceil(nifty_live.last_price) // 50) * 50

        ce_tickers = []
        pe_tickers = []

        for i in range(1, 5):
            ce_ticker = (
                "NIFTY"
                + self.year
                + self.month
                + self.week
                + str(i * 50 + nifty_atm)
                + "CE"
            )

            ce_tickers.append(ce_ticker)

            pe_ticker = (
                "NIFTY"
                + self.year
                + self.month
                + self.week
                + str(nifty_atm - i * 50)
                + "PE"
            )

            pe_tickers.append(pe_ticker)

        diff_buy_sell_ce = []
        diff_buy_sell_pe = []

        for ticker in ce_tickers:
            ticker_live = self.zerodha.live_data(ticker)

            diff_buy_sell = (
                ticker_live.total_buy_quantity - ticker_live.total_sell_quantity
            )

            diff_buy_sell_ce.append(diff_buy_sell)

        for ticker in pe_tickers:
            ticker_live = self.zerodha.live_data(ticker)

            diff_buy_sell = (
                ticker_live.total_buy_quantity - ticker_live.total_sell_quantity
            )

            diff_buy_sell_pe.append(diff_buy_sell)

        diff_ce = sum(diff_buy_sell_ce)
        diff_pe = sum(diff_buy_sell_pe)

        return diff_ce, diff_pe, ce_tickers, pe_tickers

    def entry_strategy(self):
        while True:
            if datetime.datetime.now().time() < datetime.time(
                9, 33
            ) or datetime.datetime.now().time() > datetime.time(15, 10):
                continue

            try:
                diff_ce, diff_pe, ce_tickers, pe_tickers = self.get_buy_sell_diff()
            except Exception as e:
                print(e)
                time.sleep(60)
                continue

            if diff_ce > 0 and diff_ce > diff_pe:
                for ticker in ce_tickers:
                    ticker_live = self.zerodha.live_data(ticker)

                    trade = Trade(
                        endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                        trading_symbol=ticker,
                        exchange="NFO",
                        quantity=50,
                        tag=TradeTag.ENTRY,
                        publisher="",
                        entry_price=ticker_live.last_price,
                        price=ticker_live.depth.sell[1].price,
                        ltp=ticker_live.last_price,
                        type=TradeType.INDEXOPT,
                        max_quantity=1800,
                    )
                    self.enter_trade(trade)
            elif diff_pe > 0 and diff_pe > diff_ce:
                for ticker in pe_tickers:
                    ticker_live = self.zerodha.live_data(ticker)

                    trade = Trade(
                        endpoint=TradeEndpoint.MARKET_ORDER_SELL,
                        trading_symbol=ticker,
                        exchange="NFO",
                        quantity=50,
                        tag=TradeTag.ENTRY,
                        publisher="",
                        entry_price=ticker_live.last_price,
                        price=ticker_live.depth.buy[1].price,
                        ltp=ticker_live.last_price,
                        type=TradeType.INDEXOPT,
                        max_quantity=1800,
                    )
                    self.enter_trade(trade)

            time.sleep(900)

    def exit_strategy(self, order: Order):
        ticker_live = self.zerodha.live_data(order.trading_symbol)
        profit_price = (110 / 100) * order.average_entry_price
        diff_ce, diff_pe, _, _ = self.get_buy_sell_diff()
        trade = Trade(
            endpoint=TradeEndpoint.MARKET_ORDER_SELL,
            trading_symbol=order.trading_symbol,
            exchange="NFO",
            quantity=order.total_quantity,
            tag=TradeTag.EXIT,
            publisher="",
            entry_price=order.average_entry_price,
            price=ticker_live.depth.buy[1].price,
            ltp=ticker_live.last_price,
            type=TradeType.INDEXOPT,
        )

        ticker_type = ""

        if "CE" in order.trading_symbol:
            ticker_type = "CE"
        else:
            ticker_type = "PE"

        if ticker_type == "CE":
            if diff_ce < diff_pe:
                self.exit_trade(trade)
                return

        if ticker_type == "PE":
            if diff_pe < diff_ce:
                self.exit_trade(trade)
                return

        if ticker_live.last_price >= profit_price:
            self.exit_trade(trade)
            return
