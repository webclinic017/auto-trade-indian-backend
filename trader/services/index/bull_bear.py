import datetime, time
from interfaces.tradeapp import TradeApp
from threading import Thread


class BullBear(TradeApp):
    nifty_first5min_ohlc = None
    banknifty_first5min_ohlc = None

    nifty_latesthigh = None
    nifty_latestlow = None
    nifty_latestopen = None
    nifty_latestclose = None

    banknifty_latesthigh = None
    banknifty_latestlow = None
    banknifty_latestopen = None
    banknifty_latestclose = None

    nifty_profitcount = 0
    nifty_losscount = 0
    banknifty_profitcount = 0
    banknifty_losscount = 0

    def isValuesNone(self):
        return (
            self.nifty_first5min_ohlc == None
            or self.banknifty_first5min_ohlc == None
            or self.nifty_latesthigh == None
            or self.nifty_latestlow == None
            or self.nifty_latestopen == None
            or self.nifty_latestclose == None
            or self.banknifty_latesthigh == None
            or self.banknifty_latestlow == None
            or self.banknifty_latestopen == None
            or self.banknifty_latestclose == None
        )

    def calculateValues(self):
        today = datetime.date.today()

        while True:
            if datetime.datetime.now().time() < datetime.time(
                9, 30
            ) or datetime.datetime.now().time() > datetime.time(15, 10):
                continue

            nifty_historical = self.getHistoricalDataDict(
                "NSE:NIFTY 50", today, today, "5minute"
            )

            banknifty_historical = self.getHistoricalDataDict(
                "NSE:NIFTY BANK", today, today, "5minute"
            )

            if self.nifty_first5min_ohlc == None:
                self.nifty_first5min_ohlc = nifty_historical[0]

            if self.banknifty_first5min_ohlc == None:
                self.banknifty_first5min_ohlc = banknifty_historical[0]

            self.latest_niftyhistorical = nifty_historical[-2]
            self.latest_bankniftyhistorical = banknifty_historical[-2]

            if (
                self.nifty_latestlow == None
                or self.latest_niftyhistorical["low"] != self.nifty_latestlow
            ):
                self.nifty_latestlow = self.latest_niftyhistorical["low"]

            if (
                self.nifty_latesthigh == None
                or self.latest_niftyhistorical["high"] != self.nifty_latesthigh
            ):
                self.nifty_latesthigh = self.latest_niftyhistorical["high"]

            if (
                self.nifty_latestopen == None
                or self.latest_niftyhistorical["open"] != self.nifty_latestopen
            ):
                self.nifty_latestopen = self.latest_niftyhistorical["open"]

            if (
                self.nifty_latestclose == None
                or self.latest_niftyhistorical["close"] != self.nifty_latestclose
            ):
                self.nifty_latestclose = self.latest_niftyhistorical["close"]

            if (
                self.banknifty_latestlow == None
                or self.latest_bankniftyhistorical["low"] != self.banknifty_latestlow
            ):
                self.banknifty_latestlow = self.latest_bankniftyhistorical["low"]

            if (
                self.banknifty_latesthigh == None
                or self.latest_bankniftyhistorical["high"] != self.banknifty_latesthigh
            ):
                self.banknifty_latesthigh = self.latest_bankniftyhistorical["high"]

            if (
                self.banknifty_latestopen == None
                or self.latest_bankniftyhistorical["open"] != self.banknifty_latestopen
            ):
                self.banknifty_latestopen = self.latest_bankniftyhistorical["open"]

            if (
                self.banknifty_latestclose == None
                or self.latest_bankniftyhistorical["close"]
                != self.banknifty_latestclose
            ):
                self.banknifty_latestclose = self.latest_bankniftyhistorical["close"]

            time.sleep(10)

    def entryStrategy(self):
        today = datetime.date.today()

        while True:
            if (
                datetime.datetime.now().time() < datetime.time(9, 31)
                or datetime.datetime.now().time() > datetime.time(15, 10)
                or self.isValuesNone()
            ):
                continue

            nifty_live = self.getLiveData("NSE:NIFTY 50")
            banknifty_live = self.getLiveData("NSE:NIFTY BANK")

            ce_ticker_nifty = self.data["index"]["NSE:NIFTY 50"]["ce_ticker"]
            ce_ticker_banknifty = self.data["index"]["NSE:NIFTY BANK"]["ce_ticker"]

            pe_ticker_nifty = self.data["index"]["NSE:NIFTY 50"]["pe_ticker"]
            pe_ticker_banknifty = self.data["index"]["NSE:NIFTY BANK"]["pe_ticker"]

            # CE TICKER
            if (
                nifty_live["last_price"] > self.nifty_first5min_ohlc["high"]
                and self.nifty_latestclose > self.nifty_latestopen
                and abs(self.nifty_latestopen - self.nifty_latestclose)
                >= 0.5 * (self.nifty_latesthigh - self.nifty_latestlow)
            ):
                trade = self.generateMarketOrderBuyIndexOption(
                    ce_ticker_nifty, 50, "ENTRY"
                )
                self.sendTrade(trade)

            if (
                banknifty_live["last_price"] > self.banknifty_first5min_ohlc["high"]
                and self.banknifty_latestclose > self.banknifty_latestopen
                and abs(self.banknifty_latestopen - self.banknifty_latestclose)
                >= 0.5 * (self.banknifty_latesthigh - self.banknifty_latestlow)
            ):
                trade = self.generateMarketOrderBuyIndexOption(
                    ce_ticker_banknifty, 50, "ENTRY"
                )
                self.sendTrade(trade)

            # PE TICKER
            if (
                nifty_live["last_price"] < self.nifty_first5min_ohlc["low"]
                and self.nifty_latestclose < self.nifty_latestopen
                and abs(self.nifty_latestopen - self.nifty_latestclose)
                >= 0.5 * (self.nifty_latesthigh - self.nifty_latestlow)
            ):
                trade = self.generateMarketOrderBuyIndexOption(
                    pe_ticker_nifty, 50, "ENTRY"
                )
                self.sendTrade(trade)

            if (
                banknifty_live["last_price"] < self.banknifty_first5min_ohlc["low"]
                and self.banknifty_latestclose < self.banknifty_latestopen
                and abs(self.banknifty_latestopen - self.banknifty_latestclose)
                >= 0.5 * (self.banknifty_latesthigh - self.banknifty_latestlow)
            ):

                trade = self.generateMarketOrderBuyIndexOption(
                    pe_ticker_banknifty, 50, "ENTRY"
                )
                self.sendTrade(trade)

            time.sleep(300)

    def exitStrategy(self):

        while True:
            orders = self.getAllOrders()

            for order in orders:
                ticker = order["ticker"]
                entryprice = self.averageEntryprice(order["data"])
                livedata = self.getLiveData(ticker)
                nifty_live = self.getLiveData("NSE:NIFTY 50")
                banknifty_live = self.getLiveData("NSE:NIFTY BANK")
                profit_price = entryprice * 110 / 100

                print(datetime.datetime.now(), "current time")
                print(nifty_live["last_price"], "nifty current price")
                print(self.nifty_first5min_ohlc["high"], "nifty first fiveminute high")
                print(self.nifty_first5min_ohlc["low"], "nifty first fiveminute low")
                print(self.nifty_latestopen, "nifty latest open")
                print(self.nifty_latesthigh, "nifty latest high")
                print(self.nifty_latestlow, "nifty latest low")
                print(self.nifty_latestclose, "nifty latest close")
                print(
                    abs(self.nifty_latestopen - self.nifty_latestclose),
                    "niftyopen-nifty close",
                )
                print(
                    abs(self.nifty_latesthigh - self.nifty_latestlow),
                    "niftyhigh-nifty low",
                )

                print(banknifty_live["last_price"], "banknifty current price")
                print(
                    self.banknifty_first5min_ohlc["high"],
                    "banknifty first fiveminute high",
                )
                print(
                    self.banknifty_first5min_ohlc["low"],
                    "banknifty first fiveminute low",
                )
                print(self.banknifty_latestopen, "banknifty latest open")
                print(self.banknifty_latesthigh, "banknifty latest high")
                print(self.banknifty_latestlow, "banknifty latest low")
                print(self.banknifty_latestclose, "banknifty latest close")
                print(
                    abs(self.banknifty_latestopen - self.banknifty_latestclose),
                    "bankniftyopen-banknifty close",
                )
                print(
                    abs(self.banknifty_latesthigh - self.banknifty_latestlow),
                    "bankniftyhigh-banknifty low",
                )
                print(self.nifty_profitcount, "nifty profit count")
                print(self.nifty_losscount, "nifty loss count")
                print(self.banknifty_profitcount, "banknifty profit count")
                print(self.banknifty_losscount, "banknifty loss count")

                if "BANK" in ticker:
                    ticker_type = "BANKNIFTY"
                else:
                    ticker_type = "NIFTY"

                print(ticker_type, ticker)

                if ticker_type == "BANKNIFTY" and "CE" in ticker:
                    if (
                        self.banknifty_latestlow != None
                        and
                        # and banknifty_live["last_price"] < self.banknifty_first5min_ohlc['low'] and
                        banknifty_live["last_price"] < self.banknifty_latestlow
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        self.banknifty_losscount += 1
                        continue

                if ticker_type == "NIFTY" and "CE" in ticker:
                    if (
                        self.nifty_latestlow != None
                        # and nifty_live["last_price"] < self.nifty_first_5min_ohlc['low']
                        and nifty_live["last_price"] < self.nifty_latestlow
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        self.nifty_losscount += 1
                        continue

                if ticker_type == "BANKNIFTY" and "PE" in ticker:
                    if (
                        self.banknifty_latesthigh != None
                        # and banknifty_live["last_price"] > self.banknifty_first_5min_ohlc['high']
                        and banknifty_live["last_price"] > self.banknifty_latesthigh
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                        self.banknifty_losscount += 1
                        continue

                if ticker_type == "NIFTY" and "PE" in ticker:
                    if (
                        self.nifty_latesthigh != None
                        and nifty_live["last_price"] > self.nifty_latesthigh
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                        self.nifty_losscount += 1
                        continue

                if (
                    livedata["last_price"] >= profit_price
                    # or livedata["last_price"] <= loss_price
                    or datetime.datetime.now().time() >= datetime.time(15, 10)
                ):
                    print(profit_price, " profit")
                    trade = self.generateMarketOrderSellIndexOption(ticker, 50, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)

                    if ticker_type == "NIFTY":
                        self.nifty_profitcount += 1
                    else:
                        self.banknifty_profitcount += 1

                    continue

            time.sleep(10)

    def start(self):
        Thread(target=self.calculateValues).start()
        super().start()


def main():
    app = BullBear(name="bull_bear_index")
    app.start()
