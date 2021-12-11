import datetime, time
from interfaces.tradeapp import TradeApp


class BullBear(TradeApp):
    nifty_first_5min_ohlc = None
    banknifty_first_5min_ohlc = None

    nifty_high = None
    nifty_low = None

    banknifty_high = None
    banknifty_low = None

    def entryStrategy(self):
        today = datetime.date.today()

        while True:
            if datetime.datetime.now().time() < datetime.time(9, 20):
                continue

            nifty_historical = self.getHistoricalDataDict(
                "NSE:NIFTY 50", today, today, "5minute"
            )

            banknifty_historical = self.getHistoricalDataDict(
                "NSE:NIFTY BANK", today, today, "5minute"
            )

            if self.nifty_first_5min_ohlc == None:
                self.nifty_first_5min_ohlc = nifty_historical[0]

            if self.banknifty_first_5min_ohlc == None:
                self.banknifty_first_5min_ohlc = banknifty_historical[0]

            latest_nifty_historical = nifty_historical.pop()
            latest_banknifty_historical = banknifty_historical.pop()

            if (
                self.nifty_low == None
                or latest_nifty_historical["low"] < self.nifty_low
            ):
                self.nifty_low = latest_nifty_historical["low"]

            if (
                self.nifty_high == None
                or latest_nifty_historical["high"] > self.nifty_high
            ):
                self.nifty_high = latest_nifty_historical["high"]

            if (
                self.banknifty_low == None
                or latest_banknifty_historical["low"] < self.banknifty_low
            ):
                self.banknifty_low = latest_banknifty_historical["low"]

            if (
                self.banknifty_high == None
                or latest_banknifty_historical["high"] > self.banknifty_high
            ):
                self.banknifty_high = latest_banknifty_historical["high"]

            nifty_live = self.getLiveData("NSE:NIFTY 50")
            banknifty_live = self.getLiveData("NSE:NIFTY BANK")

            ce_ticker_nifty = self.data["index"]["NSE:NIFTY 50"]["ce_ticker"]
            ce_ticker_banknifty = self.data["index"]["NSE:NIFTY BANK"]["ce_ticker"]

            pe_ticker_nifty = self.data["index"]["NSE:NIFTY 50"]["pe_ticker"]
            pe_ticker_banknifty = self.data["index"]["NSE:NIFTY BANK"]["pe_ticker"]

            # CE TICKER
            if nifty_live["last_price"] > self.nifty_first_5min_ohlc["high"]:
                trade = self.generateMarketOrderBuyIndexOption(
                    ce_ticker_nifty, 50, "ENTRY"
                )
                self.sendTrade(trade)

            if banknifty_live["last_price"] > self.banknifty_first_5min_ohlc["high"]:
                trade = self.generateMarketOrderBuyIndexOption(
                    ce_ticker_banknifty, 50, "ENTRY"
                )
                self.sendTrade(trade)

            # PE TICKER
            if nifty_live["last_price"] < self.nifty_first_5min_ohlc["low"]:
                trade = self.generateMarketOrderBuyIndexOption(
                    pe_ticker_nifty, 50, "ENTRY"
                )
                self.sendTrade(trade)

            if banknifty_live["last_price"] < self.banknifty_first_5min_ohlc["low"]:
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
                entryprice = self.averageEntryprice(orders["data"])
                livedata = self.getLiveData(ticker)
                nifty_live = self.getLiveData("NSE:NIFTY 50")
                banknifty_live = self.getLiveData("NSE:NIFTY BANK")
                profit_price = entryprice * 110 / 100

                if "BANK" in ticker:
                    ticker_type = "BANKNIFTY"
                else:
                    ticker_type = "NIFTY"

                if ticker_type == "BANKNIFTY" and "CE" in ticker:
                    if (
                        self.banknifty_low != None
                        and banknifty_live["last_price"] < self.banknifty_low
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                if ticker_type == "NIFTY" and "CE" in ticker:
                    if (
                        self.nifty_low != None
                        and nifty_live["last_price"] < self.nifty_low
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                if ticker_type == "BANKNIFTY" and "PE" in ticker:
                    if (
                        self.banknifty_high != None
                        and banknifty_live["last_price"] > self.banknifty_high
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                if ticker_type == "NIFTY" and "PE" in ticker:
                    if (
                        self.nifty_high != None
                        and nifty_live["last_price"] > self.nifty_high
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                if (
                    livedata["last_price"] >= profit_price
                    # or livedata["last_price"] <= loss_price
                    or datetime.datetime.now().time() >= datetime.time(15, 10)
                ):
                    print(profit_price, " profit")
                    trade = self.generateMarketOrderSellIndexOption(ticker, 50, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)

            time.sleep(10)
