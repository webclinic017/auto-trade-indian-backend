from interfaces.tradeapp import TradeApp
import time, json, threading, datetime
from collections import defaultdict
import datetime, time
import os
from nsetools import Nse

nse = Nse()

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()


class Worker7(TradeApp):

    ohlc_ticker = {}

    NIFTY_QTY = 50
    BANK_NIFTY_QTY = 25

    def entryStrategy(self):
        nifty_gamechanger = self.data["index"]["NSE:NIFTY 50"]["ltp"]
        banknifty_gamechanger = self.data["index"]["NSE:NIFTY BANK"]["ltp"]
        for ticker in self.index_tickers:
            if datetime.datetime.now().time() < datetime.time(9, 20):
                continue

            live_data_der = self.getLiveData(ticker)
            rsi, slope = self.getRSISlope(ticker)

            nifty_live = self.getLiveData("NSE:NIFTY")
            banknifty_live = self.getLiveData("NSE:NIFTY BANK")

            if datetime.datetime.now().time() == datetime.time(9, 21):
                nifty_fivehigh = nifty_live["ohlc"]["high"]
                nifty_fivelow = nifty_live["ohlc"]["low"]
                banknifty_fivehigh = banknifty_live["ohlc"]["high"]
                banknifty_fivelow = banknifty_live["ohlc"]["low"]

            if datetime.datetime.now().time() == datetime.time(9, 31):
                nifty_15high = nifty_live["ohlc"]["high"]
                nifty_15low = nifty_live["ohlc"]["low"]
                banknifty_15high = banknifty_live["ohlc"]["high"]
                banknifty_15low = banknifty_live["ohlc"]["low"]

            t = datetime.date.today()

        now = datetime.datetime.now().time()

        log = {
            "rsi": rsi,
            "slope": slope,
            "ticker": ticker,
            "ltp": ltp,
        }

        print(json.dumps(log, indent=2))
        if rsi > 40 and slope > 0 and now > datetime.time(9, 30):

            if (
                "BANKNIFTY" in ticker
                and banknifty_live["last_price"] > banknifty_gamechanger
            ):
                quantity = self.BANK_NIFTY_QTY
            elif nifty_live > nifty_gamechanger:
                quantity = self.NIFTY_QTY

            trade = self.generateMarketOrderBuyIndexOption(ticker, quantity, "ENTRY")
            self.sendTrade(trade)
            return

    # strategy for exit
    def exitStrategy(self):
        nifty_gamechanger = self.data["index"]["NSE:NIFTY 50"]["ltp"]
        banknifty_gamechanger = self.data["index"]["NSE:NIFTY BANK"]["ltp"]
        nifty_live = self.getLiveData("NSE:NIFTY")
        banknifty_live = self.getLiveData("NSE:NIFTY BANK")

        m = defaultdict(int)
        acc = defaultdict(list)
        acc_drop = defaultdict(int)

        iterations = 0

        while True:
            orders = self.getAllOrders()

            for order_ in orders:
                ticker = order_["ticker"]
                entry_price = self.averageEntryprice(order_["data"])

                try:
                    ticker_data = self.getLiveData(ticker)
                except:
                    continue

                ltp = ticker_data["last_price"]

                pnl = self.getPnl(entry_price, ticker_data)
                if (
                    "BANK"
                    and "CE" in ticker
                    and pnl >= 10
                    or datetime.datetime.now().time() >= datetime.time(21, 25)
                    or banknifty_live < banknifty_gamechanger
                ):

                    trade = self.generateMarketOrderBuyIndexOption(
                        order_["ticker"], order_["quantity"], "EXIT"
                    )
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)

                if (
                    "BANK"
                    and "PE" in ticker
                    and pnl >= 10
                    or datetime.datetime.now().time() >= datetime.time(21, 25)
                    or banknifty_live > banknifty_gamechanger
                ):

                    trade = self.generateMarketOrderBuyIndexOption(
                        order_["ticker"], order_["quantity"], "EXIT"
                    )
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)

                elif (
                    "CE" in ticker
                    and pnl >= 10
                    or datetime.datetime.now().time() >= datetime.time(21, 25)
                    or nifty_live < nifty_gamechanger
                ):

                    trade = self.generateMarketOrderBuyIndexOption(
                        order_["ticker"], order_["quantity"], "EXIT"
                    )
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)

                elif (
                    "PE" in ticker
                    and pnl >= 10
                    or datetime.datetime.now().time() >= datetime.time(21, 25)
                    or nifty_live > nifty_gamechanger
                ):

                    trade = self.generateMarketOrderBuyIndexOption(
                        order_["ticker"], order_["quantity"], "EXIT"
                    )
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)

            time.sleep(10)


def main():
    app = Worker7(name="worker_7_index")
    app.start()
