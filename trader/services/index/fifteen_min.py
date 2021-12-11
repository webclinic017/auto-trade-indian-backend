# fifteen min strategy
from interfaces.tradeapp import TradeApp
import datetime, time


class FifteenMinIndex(TradeApp):
    nifty_15min_ohlc = None
    banknifty_15min_ohlc = None
    entered_tickers = set()

    def entryStrategy(self):
        today = datetime.date.today()

        while True:
            if datetime.datetime.now().time() < datetime.time(9, 20):
                continue

            if self.nifty_15min_ohlc == None or self.banknifty_15min_ohlc == None:
                nifty_historical = self.getHistoricalDataDict(
                    "NSE:NIFTY 50", today, today, "15minute"
                )

                banknifty_historical = self.getHistoricalDataDict(
                    "NSE:NIFTY BANK", today, today, "15minute"
                )

                self.nifty_15min_ohlc = nifty_historical[0]
                self.banknifty_15min_ohlc = banknifty_historical[0]

            nifty_live = self.getLiveData("NSE:NIFTY 50")
            banknifty_live = self.getLiveData("NSE:NIFTY BANK")

            ce_ticker_nifty = self.data["index"]["NSE:NIFTY 50"]["ce_ticker"]
            ce_ticker_banknifty = self.data["index"]["NSE:NIFTY BANK"]["ce_ticker"]

            pe_ticker_nifty = self.data["index"]["NSE:NIFTY 50"]["pe_ticker"]
            pe_ticker_banknifty = self.data["index"]["NSE:NIFTY BANK"]["pe_ticker"]

            # FOR CE TICKER
            if nifty_live["last_price"] > self.nifty_15min_ohlc["high"] and (
                ce_ticker_nifty not in self.entered_tickers
            ):
                trade = self.generateMarketOrderBuyIndexOption(
                    ce_ticker_nifty, 50, "ENTRY"
                )

                self.sendTrade(trade)
                self.entered_tickers.add(ce_ticker_nifty)

            if banknifty_live["last_price"] > self.banknifty_15min_ohlc["high"] and (
                ce_ticker_banknifty not in self.entered_tickers
            ):
                trade = self.generateMarketOrderBuyIndexOption(
                    ce_ticker_banknifty, 50, "ENTRY"
                )

                self.sendTrade(trade)
                self.entered_tickers.add(ce_ticker_banknifty)

            # FOR PE TICKER
            if nifty_live["last_price"] < self.nifty_15min_ohlc["low"] and (
                pe_ticker_nifty not in self.entered_tickers
            ):
                trade = self.generateMarketOrderBuyIndexOption(
                    pe_ticker_nifty, 50, "ENTRY"
                )

                self.sendTrade(trade)
                self.entered_tickers.add(pe_ticker_nifty)

            if banknifty_live["last_price"] < self.banknifty_15min_ohlc["low"] and (
                pe_ticker_banknifty not in self.entered_tickers
            ):
                trade = self.generateMarketOrderBuyIndexOption(
                    pe_ticker_banknifty, 50, "ENTRY"
                )

                self.sendTrade(trade)
                self.entered_tickers.add(pe_ticker_banknifty)

            time.sleep(300)

    def exitStrategy(self):

        while True:
            orders = self.getAllOrders()

            for order in orders:
                ticker = order["ticker"]
                entryprice = self.averageEntryprice(order["data"])
                profit_price = entryprice * 110 / 100

                livedata = self.getLiveData(ticker)
                livedata_nifty = self.getLiveData("NSE:NIFTY 50")
                livedata_banknifty = self.getLiveData("NSE:NIFTY BANK")

                if "BANK" in ticker:
                    ticker_type = "BANKNIFTY"
                else:
                    ticker_type = "NIFTY"

                # BANKNIFTY CE
                if ticker_type == "BANKNIFTY" and "CE" in ticker:
                    if (
                        livedata_banknifty["last_price"]
                        < self.banknifty_15min_ohlc["low"]
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                # BANKNIFTY PE
                if ticker_type == "BANKNIFTY" and "PE" in ticker:
                    if (
                        livedata_banknifty["last_price"]
                        > self.banknifty_15min_ohlc["high"]
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                # NIFTY CE
                if ticker_type == "NIFTY" and "CE" in ticker:
                    if livedata_nifty["last_price"] < self.nifty_15min_ohlc["low"]:
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                # NIFTY PE
                if ticker_type == "NIFTY" and "PE" in ticker:
                    if livedata_nifty["last_price"] > self.nifty_15min_ohlc["high"]:
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                # EXIT FOR PROFIT OR END OF DAY
                if livedata["last_price"] >= profit_price or (
                    datetime.datetime.now().time() >= datetime.time(3, 10)
                ):
                    trade = self.generateMarketOrderSellIndexOption(ticker, 50, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)
                    continue

            time.sleep(10)


def main():
    app = FifteenMinIndex(name="fifteen_min_index")
    app.start()
