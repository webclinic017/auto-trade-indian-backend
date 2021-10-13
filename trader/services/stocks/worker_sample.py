# This is the standard strategy from which other strategies can be build

from interfaces.tradeapp import TradeApp
import datetime, time, json, os

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()


class Worker7(TradeApp):
    quantity = 1  # defines the lot size
    entered_tickers = set()
    ohlc_ticker = {}
    exchange = "NFO"

    def entryStrategy(self):

        while True:
            now = datetime.datetime.now().time()
            if now >= datetime.time(9, 30):

                for ticker in self.tickers:

                    if ticker not in self.ohlc_ticker:
                        t = datetime.date.today()
                        try:
                            historical_data = self.getHistoricalData(
                                ticker, t, t, "15minute"
                            )
                        except:
                            continue
                        o, h, l, c = historical_data.loc[
                            0, ["open", "high", "low", "close"]
                        ].values
                        self.ohlc_ticker[ticker] = {"high": h, "low": l}

                    try:
                        live_data = self.getLiveData(
                            ticker
                        )  # this will give live data of stock
                        ce_ticker = self.tickers[ticker]["ce_ticker"]
                        pe_ticker = self.tickers[ticker]["pe_ticker"]
                        live_ce = self.getLiveData(ce_ticker)
                        live_pe = self.getLiveData(pe_ticker)
                    except Exception as e:
                        print(e)
                        continue

                    print(ticker, ce_ticker, pe_ticker)
                    if (
                        (live_data["last_price"] > self.ohlc_ticker[ticker]["high"])
                        and (
                            self.tickers[ticker]["ce_ticker"]
                            not in self.entered_tickers
                        )
                        and self.price_diff(
                            live_ce["depth"]["sell"][0]["price"],
                            live_ce["depth"]["buy"][0]["price"],
                        )
                        < 5
                    ):

                        trade = self.generateLimitOrderBuyStockOption(
                            self.tickers[ticker]["ce_ticker"], "ENTRY"
                        )
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]["ce_ticker"])

                    elif (
                        (live_data["last_price"] < self.ohlc_ticker[ticker]["low"])
                        and (
                            self.tickers[ticker]["pe_ticker"]
                            not in self.entered_tickers
                        )
                        and self.price_diff(
                            live_pe["depth"]["sell"][0]["price"],
                            live_pe["depth"]["buy"][0]["price"],
                        )
                        < 5
                    ):

                        trade = self.generateLimitOrderBuyStockOption(
                            self.tickers[ticker]["pe_ticker"], "ENTRY"
                        )
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]["pe_ticker"])
            time.sleep(300)

    def exitStrategy(self):

        while True:
            orders = self.getAllOrders()
            for order_ in orders:
                derivative = order_[
                    "ticker"
                ]  # here you will get the derivative of ticker
                ticker = self.derivative_map[
                    derivative
                ]  # here you will get the actual ticker

                if ticker not in self.ohlc_ticker:
                    continue

                live_data = self.getLiveData(ticker)
                live_data_der = self.getLiveData(derivative)

                orders_list = order_["data"]
                entry_price = self.averageEntryprice(orders_list)

                profit = entry_price * ((100 + 10) / 100)
                loss = entry_price * ((100 - 5) / 100)

                if (
                    "CE" in derivative
                    and live_data["last_price"] < self.ohlc_ticker[ticker]["low"]
                    or live_data_der["last_price"] >= profit
                    or live_data_der["last_price"] <= loss
                    or datetime.datetime.now().time() >= datetime.time(15, 25)
                ):
                    trade = self.generateLimitOrderSellStockOption(derivative, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(derivative)

                elif (
                    "PE" in derivative
                    and live_data["last_price"] > self.ohlc_ticker[ticker]["high"]
                    or live_data_der["last_price"] >= profit
                    or live_data_der["last_price"] <= loss
                    or datetime.datetime.now().time() >= datetime.time(15, 25)
                ):
                    trade = self.generateLimitOrderSellStockOption(derivative, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(derivative)
            time.sleep(10)


def main():
    app = Worker7(name="worker_sample")
    app.start()
