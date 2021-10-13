from interfaces.tradeapp import TradeApp
import time, json, datetime
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

            rsi, slope = self.getRSISlope(ticker)

            try:
                nifty_live = self.getLiveData("NSE:NIFTY 50")
                banknifty_live = self.getLiveData("NSE:NIFTY BANK")
            except Exception as e:
                print(e)
                continue

            if datetime.datetime.now().time() >= datetime.time(9, 21):
                nifty_fivehigh = nifty_live["ohlc"]["high"]
                nifty_fivelow = nifty_live["ohlc"]["low"]
                banknifty_fivehigh = banknifty_live["ohlc"]["high"]
                banknifty_fivelow = banknifty_live["ohlc"]["low"]

            if datetime.datetime.now().time() >= datetime.time(9, 31):
                nifty_15high = nifty_live["ohlc"]["high"]
                nifty_15low = nifty_live["ohlc"]["low"]
                banknifty_15high = banknifty_live["ohlc"]["high"]
                banknifty_15low = banknifty_live["ohlc"]["low"]

            t = datetime.date.today()

            now = datetime.datetime.now().time()

            if rsi > 40 and slope > 0 and now > datetime.time(9, 30):
                for ticker in self.index_tickers:
                    if datetime.datetime.now().time() < datetime.time(9, 20):
                        continue

                    rsi, slope = self.getRSISlope(ticker)

                    try:
                        nifty_live = self.getLiveData("NSE:NIFTY 50")
                        banknifty_live = self.getLiveData("NSE:NIFTY BANK")
                    except Exception as e:
                        print(e)
                        continue

                    if datetime.datetime.now().time() >= datetime.time(9, 21):
                        nifty_fivehigh = nifty_live["ohlc"]["high"]
                        nifty_fivelow = nifty_live["ohlc"]["low"]
                        banknifty_fivehigh = banknifty_live["ohlc"]["high"]
                        banknifty_fivelow = banknifty_live["ohlc"]["low"]

                    if datetime.datetime.now().time() >= datetime.time(9, 31):
                        nifty_15high = nifty_live["ohlc"]["high"]
                        nifty_15low = nifty_live["ohlc"]["low"]
                        banknifty_15high = banknifty_live["ohlc"]["high"]
                        banknifty_15low = banknifty_live["ohlc"]["low"]

                    t = datetime.date.today()

                    now = datetime.datetime.now().time()

                    if (
                        "BANKNIFTY" in ticker
                        and banknifty_live["last_price"] > banknifty_gamechanger
                    ):
                        quantity = self.BANK_NIFTY_QTY
                        trade = self.generateMarketOrderBuyIndexOption(
                            ticker, quantity, "ENTRY"
                        )
                        self.sendTrade(trade)
                    elif nifty_live["last_price"] > nifty_gamechanger:
                        quantity = self.NIFTY_QTY

                        trade = self.generateMarketOrderBuyIndexOption(
                            ticker, quantity, "ENTRY"
                        )
                        self.sendTrade(trade)

                time.sleep(300)

    # strategy for exit
    def exitStrategy(self):
        nifty_gamechanger = self.data["index"]["NSE:NIFTY 50"]["ltp"]
        banknifty_gamechanger = self.data["index"]["NSE:NIFTY BANK"]["ltp"]

        while True:
            try:
                nifty_live = self.getLiveData("NSE:NIFTY 50")
                banknifty_live = self.getLiveData("NSE:NIFTY BANK")
            except:
                continue

            orders = self.getAllOrders()

            for order_ in orders:
                ticker = order_["ticker"]
                entry_price = self.averageEntryprice(order_["data"])

                try:
                    ticker_data = self.getLiveData(ticker)
                except:
                    continue

                ltp = ticker_data["last_price"]
                profit = entry_price * ((100 + 10) / 100)

                if "BANK" in ticker:
                    if (
                        "CE" in ticker
                        and ltp >= profit
                        or datetime.datetime.now().time() >= datetime.time(21, 25)
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            order_["ticker"], 1, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                    else:
                        trade = self.generateMarketOrderSellIndexOption(
                            order_["ticker"], 1, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                else:
                    if (
                        "CE" in ticker
                        and ltp >= profit
                        or datetime.datetime.now().time() >= datetime.time(21, 25)
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            order_["ticker"], 1, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                    elif (
                        "PE" in ticker
                        and ltp >= profit
                        or datetime.datetime.now().time() >= datetime.time(21, 25)
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            order_["ticker"], 1, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                # if (
                #     ("BANK" in ticker and "CE" in ticker and ltp >= profit)
                #     or datetime.datetime.now().time() >= datetime.time(21, 25)
                #     or (
                #         "BANK" in ticker
                #         and "CE" in ticker
                #         and banknifty_live["last_price"] < banknifty_gamechanger
                #     )
                # ):

                #     trade = self.generateMarketOrderSellIndexOption(
                #         order_["ticker"], 1, "EXIT"
                #     )
                #     self.sendTrade(trade)
                #     self.deleteOrder(ticker)

                # if (
                #     ("BANK" in ticker and "PE" in ticker and ltp >= profit)
                #     or datetime.datetime.now().time() >= datetime.time(21, 25)
                #     or (
                #         "BANK" in ticker
                #         and "PE" in ticker
                #         or banknifty_live["last_price"] > banknifty_gamechanger
                #     )
                # ):

                #     trade = self.generateMarketOrderSellIndexOption(
                #         order_["ticker"], 1, "EXIT"
                #     )
                #     self.sendTrade(trade)
                #     self.deleteOrder(ticker)

                # elif (
                #     "CE" in ticker
                #     and ltp >= profit
                #     or datetime.datetime.now().time() >= datetime.time(21, 25)
                #     or nifty_live["last_price"] < nifty_gamechanger
                # ):

                #     trade = self.generateMarketOrderSellIndexOption(
                #         order_["ticker"], 1, "EXIT"
                #     )
                #     self.sendTrade(trade)
                #     self.deleteOrder(ticker)

                # elif (
                #     "PE" in ticker
                #     and ltp >= profit
                #     or datetime.datetime.now().time() >= datetime.time(21, 25)
                #     or nifty_live["last_price"] > nifty_gamechanger
                # ):

                #     trade = self.generateMarketOrderSellIndexOption(
                #         order_["ticker"], 1, "EXIT"
                #     )
                #     self.sendTrade(trade)
                #     self.deleteOrder(ticker)

            time.sleep(10)


def main():
    app = Worker7(name="worker_7_index")
    app.start()
