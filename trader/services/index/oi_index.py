# Open Interest based for Index
from interfaces.tradeapp import TradeApp
import datetime, time


class OpenInterestIndex(TradeApp):
    def entryStrategy(self):

        self.nifty_gamechanger = self.data["index"]["NSE:NIFTY 50"]["ltp"]
        self.nifty_totalpower = self.data["index"]["NSE:NIFTY 50"]["total_power"]

        self.banknifty_gamechanger = self.data["index"]["NSE:NIFTY BANK"]["ltp"]
        self.banknifty_totalpower = self.data["index"]["NSE:NIFTY BANK"]["total_power"]

        self.nifty_prev_high = self.data["index"]["NSE:NIFTY 50"]["prev_high"]
        self.nifty_prev_low = self.data["index"]["NSE:NIFTY 50"]["prev_low"]

        self.banknifty_prev_high = self.data["index"]["NSE:NIFTY BANK"]["prev_high"]
        self.banknifty_prev_low = self.data["index"]["NSE:NIFTY BANK"]["prev_low"]

        while True:
            # pause until 9 : 20
            if datetime.datetime.now().time() < datetime.time(9, 20):
                continue

            nifty_live = self.getLiveData("NSE:NIFTY 50")
            banknifty_live = self.getLiveData("NSE:NIFTY BANK")
            _, nifty_slope = self.getRSISlope("NSE:NIFTY 50")
            _, banknifty_slope = self.getRSISlope("NSE:NIFTY BANK")
            print("nifty_slope", nifty_slope)

            if (
                nifty_live["last_price"] > self.nifty_prev_low
                and nifty_slope > 0
                and self.nifty_totalpower > 10000
            ):
                ticker = self.data["index"]["NSE:NIFTY 50"]["ce_ticker"]
                print(nifty_slope)
                trade = self.generateMarketOrderBuyIndexOption(ticker, 50, "ENTRY")
                # the below line sends trade to front end
                self.sendTrade(trade)

            if (
                nifty_live["last_price"] < self.nifty_prev_high
                and nifty_slope < 0
                and self.nifty_totalpower < -10000
            ):
                ticker = self.data["index"]["NSE:NIFTY 50"]["pe_ticker"]
                trade = self.generateMarketOrderBuyIndexOption(ticker, 50, "ENTRY")
                # the below line sends trade to front end
                self.sendTrade(trade)

            print("banknifty_slope", banknifty_slope)
            if (
                banknifty_live["last_price"] > self.banknifty_prev_low
                and banknifty_slope > 0
                and self.banknifty_totalpower > 30000
            ):
                ticker = self.data["index"]["NSE:NIFTY BANK"]["ce_ticker"]
                trade = self.generateMarketOrderBuyIndexOption(ticker, 25, "ENTRY")
                # the below line sends trade to front end
                self.sendTrade(trade)

            if (
                banknifty_live["last_price"] < self.banknifty_prev_high
                and banknifty_slope < 0
                and self.banknifty_totalpower < -30000
            ):
                ticker = self.data["index"]["NSE:NIFTY BANK"]["pe_ticker"]
                trade = self.generateMarketOrderBuyIndexOption(ticker, 25, "ENTRY")
                # the below line sends trade to front end
                self.sendTrade(trade)

            time.sleep(300)

    def exitStrategy(self):

        while True:
            orders = self.getAllOrders()

            for order in orders:
                ticker = order["ticker"]
                entryprice = self.averageEntryprice(order["data"])
                profit_price = entryprice * 110 / 100
                # loss_price = entryprice * 95 / 100
                livedata = self.getLiveData(ticker)
                livedata_nifty = self.getLiveData("NSE:NIFTY 50")
                livedata_banknifty = self.getLiveData("NSE:NIFTY BANK")

                if "CE" in ticker:
                    if (
                        livedata_nifty["last_price"] < self.nifty_prev_low
                        and "BANKNIFTY" not in ticker
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                    elif (
                        livedata_banknifty["last_price"] < self.banknifty_prev_low
                        and "BANKNIFTY" in ticker
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 25, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                elif "PE" in ticker:
                    if (
                        livedata_nifty["last_price"] > self.nifty_prev_high
                        and "BANKNIFTY" not in ticker
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 50, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                    elif (
                        livedata_banknifty["last_price"] > self.banknifty_prev_high
                        and "BANKNIFTY" in ticker
                    ):
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker, 25, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
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
                    continue

            time.sleep(10)


def main():
    app = OpenInterestIndex(name="oi_index")
    app.start()
