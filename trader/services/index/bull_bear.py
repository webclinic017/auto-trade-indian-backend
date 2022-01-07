import datetime
import time
from interfaces.tradeapp import TradeApp


class BullBearV2(TradeApp):
    today = datetime.date.today()

    nifty_losscount = 0
    banknifty_losscount = 0
    nifty_profitcount = 0
    banknifty_profitcount = 0

    def entryStrategy(self):
        while True:

            if datetime.datetime.now().time() < datetime.time(
                9, 30, 3
            ) or datetime.datetime.now().time() > datetime.time(15, 10):
                continue

            nifty_historical = self.getHistoricalData(
                "NSE:NIFTY 50", self.today, self.today, "5minute"
            )
            banknifty_historical = self.getHistoricalData(
                "NSE:NIFTY BANK", self.today, self.today, "5minute"
            )

            # nifty_first_5min['open'] or ['low'] or ['high'] or ['close']
            nifty_first_5min = nifty_historical.loc[0, :]
            # banknifty_first_5min['open'] or ['low'] or ['high'] or ['close']
            banknifty_first_5min = banknifty_historical.loc[0, :]

            nifty_live = self.getLiveData("NSE:NIFTY 50")
            banknifty_live = self.getLiveData("NSE:NIFTY BANK")

            # nifty_buy_quantity = nifty_live["total_buy_quantity"]
            # nifty_sell_quantity = nifty_live["total_sell_quantity"]

            # banknifty_buy_quantity = banknifty_live["total_buy_quantity"]
            # banknifty_sell_quantity = banknifty_live["total_sell_quantity"]

            nifty_latest_5min = nifty_historical.loc[len(nifty_historical) - 1, :]
            banknifty_latest_5min = banknifty_historical.loc[
                len(banknifty_historical) - 1, :
            ]

            ce_ticker_nifty = self.data["index"]["NSE:NIFTY 50"]["ce_ticker"]
            ce_ticker_banknifty = self.data["index"]["NSE:NIFTY BANK"]["ce_ticker"]

            pe_ticker_nifty = self.data["index"]["NSE:NIFTY 50"]["pe_ticker"]
            pe_ticker_banknifty = self.data["index"]["NSE:NIFTY BANK"]["pe_ticker"]

            # CE TICKER
            if (
                nifty_live["last_price"] > nifty_first_5min["high"]
                and nifty_latest_5min["close"] > nifty_latest_5min["open"]
                and abs(nifty_latest_5min["open"] - nifty_latest_5min["close"])
                >= 0.5 * (nifty_latest_5min["high"] - nifty_latest_5min["low"])
            ):
                ticker = ce_ticker_nifty
                ticker_live = self.getLiveData(ticker)

                buy_quantity = ticker_live["total_buy_quantity"]
                sell_quantity = ticker_live["total_sell_quantity"]

                if buy_quantity > sell_quantity:
                    trade = self.generateMarketOrderBuyIndexOption(
                        ce_ticker_nifty, 50, "ENTRY"
                    )
                    self.sendTrade(trade)

            if (
                banknifty_live["last_price"] > banknifty_first_5min["high"]
                and banknifty_latest_5min["close"] > banknifty_latest_5min["open"]
                and abs(banknifty_latest_5min["open"] - banknifty_latest_5min["close"])
                >= 0.5 * (banknifty_latest_5min["high"] - banknifty_latest_5min["low"])
            ):

                ticker = ce_ticker_banknifty
                ticker_live = self.getLiveData(ticker)

                buy_quantity = ticker_live["total_buy_quantity"]
                sell_quantity = ticker_live["total_sell_quantity"]

                if buy_quantity > sell_quantity:
                    trade = self.generateMarketOrderBuyIndexOption(
                        ce_ticker_banknifty, 50, "ENTRY"
                    )
                    self.sendTrade(trade)

            # PE TICKER
            if (
                nifty_live["last_price"] < nifty_first_5min["low"]
                and nifty_latest_5min["close"] < nifty_latest_5min["open"]
                and abs(nifty_latest_5min["open"] - nifty_latest_5min["close"])
                >= 0.5 * (nifty_latest_5min["high"] - nifty_latest_5min["low"])
            ):

                ticker = pe_ticker_nifty
                ticker_live = self.getLiveData(ticker)

                buy_quantity = ticker_live["total_buy_quantity"]
                sell_quantity = ticker_live["total_sell_quantity"]

                if buy_quantity > sell_quantity:
                    trade = self.generateMarketOrderBuyIndexOption(
                        pe_ticker_nifty, 50, "ENTRY"
                    )
                    self.sendTrade(trade)

            if (
                banknifty_live["last_price"] < banknifty_first_5min["low"]
                and banknifty_latest_5min["close"] < banknifty_latest_5min["open"]
                and abs(banknifty_latest_5min["open"] - banknifty_latest_5min["close"])
                >= 0.5 * (banknifty_latest_5min["high"] - banknifty_latest_5min["low"])
            ):

                ticker = pe_ticker_banknifty
                ticker_live = self.getLiveData(ticker)

                buy_quantity = ticker_live["total_buy_quantity"]
                sell_quantity = ticker_live["total_sell_quantity"]

                if buy_quantity > sell_quantity:
                    trade = self.generateMarketOrderBuyIndexOption(
                        pe_ticker_banknifty, 50, "ENTRY"
                    )
                    self.sendTrade(trade)

            time.sleep(300)

    def exitStrategy(self):
        while True:
            if datetime.datetime.now().time() < datetime.time(9, 30):
                continue

            orders = self.getAllOrders()

            nifty_historical = self.getHistoricalData(
                "NSE:NIFTY 50", self.today, self.today, "5minute"
            )
            banknifty_historical = self.getHistoricalData(
                "NSE:NIFTY BANK", self.today, self.today, "5minute"
            )

            nifty_latest_5min = nifty_historical.loc[len(nifty_historical) - 1, :]
            banknifty_latest_5min = banknifty_historical.loc[
                len(banknifty_historical) - 1, :
            ]

            for order in orders:
                ticker = order["ticker"]
                entryprice = self.averageEntryprice(order["data"])
                livedata = self.getLiveData(ticker)
                nifty_live = self.getLiveData("NSE:NIFTY 50")
                banknifty_live = self.getLiveData("NSE:NIFTY BANK")
                profit_price = entryprice * 110 / 100

                if "BANK" in ticker:
                    ticker_type = "BANKNIFTY"
                else:
                    ticker_type = "NIFTY"

                print(ticker_type, ticker)

                if ticker_type == "BANKNIFTY" and "CE" in ticker:
                    if (
                        # and banknifty_live["last_price"] < self.banknifty_first5min_ohlc['low'] and
                        banknifty_live["last_price"]
                        < banknifty_latest_5min["low"]
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )

                        print(datetime.datetime.now())
                        print("*****NIFTY*****")
                        print(nifty_historical.head())
                        print("-" * 20)
                        print(nifty_historical.tail())

                        print("*****NIFTY BANK*****")
                        print(banknifty_historical.head())
                        print("-" * 20)
                        print(banknifty_historical.tail())

                        print("\n\n\n*****EXIT CONDITIONS*****\n\n\n")
                        print(
                            "banknifty live: ",
                            banknifty_live["last_price"],
                            " banknifty latestlow: ",
                            banknifty_latest_5min["low"],
                        )
                        print("\n\n\n*****EXIT CONDITIONS*****\n\n\n")

                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        self.banknifty_losscount += 1
                        time.sleep(10)
                        continue

                if ticker_type == "NIFTY" and "CE" in ticker:
                    if (
                        # and nifty_live["last_price"] < self.nifty_first_5min_ohlc['low']
                        nifty_live["last_price"]
                        < nifty_latest_5min["low"]
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )

                        print(datetime.datetime.now())
                        print("*****NIFTY*****")
                        print(nifty_historical.head())
                        print("-" * 20)
                        print(nifty_historical.tail())

                        print("*****NIFTY BANK*****")
                        print(banknifty_historical.head())
                        print("-" * 20)
                        print(banknifty_historical.tail())

                        print("\n\n\n*****EXIT CONDITIONS*****\n\n\n")
                        print(
                            "nifty live: ",
                            nifty_live["last_price"],
                            " nifty latestlow: ",
                            nifty_latest_5min["low"],
                        )
                        print("\n\n\n*****EXIT CONDITIONS*****\n\n\n")

                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        self.nifty_losscount += 1
                        time.sleep(10)
                        continue

                if ticker_type == "BANKNIFTY" and "PE" in ticker:
                    if (
                        # and banknifty_live["last_price"] > self.banknifty_first_5min_ohlc['high']
                        banknifty_live["last_price"]
                        > banknifty_latest_5min["high"]
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )

                        print(datetime.datetime.now())
                        print("*****NIFTY*****")
                        print(nifty_historical.head())
                        print("-" * 20)
                        print(nifty_historical.tail())

                        print("*****NIFTY BANK*****")
                        print(banknifty_historical.head())
                        print("-" * 20)
                        print(banknifty_historical.tail())

                        print("\n\n\n*****EXIT CONDITIONS*****\n\n\n")
                        print(
                            "banknifty live: ",
                            banknifty_live["last_price"],
                            " banknifty latesthigh: ",
                            banknifty_latest_5min["high"],
                        )
                        print("\n\n\n*****EXIT CONDITIONS*****\n\n\n")

                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                        self.banknifty_losscount += 1
                        time.sleep(10)
                        continue

                if ticker_type == "NIFTY" and "PE" in ticker:
                    if nifty_live["last_price"] > nifty_latest_5min["high"]:
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )

                        print(datetime.datetime.now())
                        print("*****NIFTY*****")
                        print(nifty_historical.head())
                        print("-" * 20)
                        print(nifty_historical.tail())

                        print("*****NIFTY BANK*****")
                        print(banknifty_historical.head())
                        print("-" * 20)
                        print(banknifty_historical.tail())

                        print("\n\n\n*****EXIT CONDITIONS*****\n\n\n")
                        print(
                            "nifty live: ",
                            nifty_live["last_price"],
                            " nifty latesthigh: ",
                            nifty_latest_5min["high"],
                        )
                        print("\n\n\n*****EXIT CONDITIONS*****\n\n\n")

                        self.sendTrade(trade)
                        self.deleteOrder(ticker)

                        self.nifty_losscount += 1
                        time.sleep(10)
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

                    time.sleep(10)
                    continue

            time.sleep(20)


def main():
    app = BullBearV2(name="bull_bear2")
    app.start()
