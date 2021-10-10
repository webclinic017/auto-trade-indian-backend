# first 1 min strategy
from interfaces.tradeapp import TradeApp
import datetime, time, json


class Worker7(TradeApp):

    entered_tickers = set()
    ohlc_tickers = {}

    def entryStrategy(self):
        while True:
            now = datetime.datetime.now()
            # print(now)

            if now.time() >= datetime.time(
                hour=9, minute=21
            ) and now.time() <= datetime.time(hour=9, minute=22):

                for ticker in self.tickers:
                    try:
                        live_data = self.getLiveData(ticker)
                    except:
                        continue

                    if ticker not in self.ohlc_tickers:
                        self.ohlc_tickers[ticker] = live_data["ohlc"]

                    ohlc = self.ohlc_tickers[ticker]

                    if (
                        ohlc["open"] == ohlc["low"]
                        and self.tickers[ticker]["ce_ticker"]
                        not in self.entered_tickers
                    ):
                        trade = self.generateLimitOrderBuyStockOption(
                            self.tickers[ticker]["ce_ticker"], "ENTRY"
                        )
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]["ce_ticker"])
                        print(
                            json.dumps(
                                {
                                    "ohlc": ohlc,
                                    "ticker": self.tickers[ticker]["ce_ticker"],
                                },
                                indent=2,
                            )
                        )
                        # self.insertOrder(ticker, trade)

                    elif (
                        ohlc["open"] == ohlc["high"]
                        and self.tickers[ticker]["pe_ticker"]
                        not in self.entered_tickers
                    ):
                        trade = self.generateLimitOrderBuyStockOption(
                            self.tickers[ticker]["pe_ticker"], "ENTRY"
                        )
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]["pe_ticker"])
                        # self.insertOrder(ticker, trade)

                        print("-" * 10 + "ENTRY CONDITION" + "-" * 10)
                        print(
                            json.dumps(
                                {
                                    "ohlc": ohlc,
                                    "ticker": self.tickers[ticker]["pe_ticker"],
                                },
                                indent=2,
                            )
                        )
                        print("-" * 10 + "ENTRY CONDITION" + "-" * 10)
            else:
                print("Cant enter Worker 7")

            time.sleep(5)

    def exitStrategy(self):
        while True:
            orders = self.getAllOrders()

            for order in orders:
                print(order)
                derivative = order["ticker"]
                ticker = self.derivative_map[derivative]
                entry_price = self.averageEntryprice(order["data"])
                original_ticker = self.derivative_map[ticker]

                live_data = self.getLiveData(original_ticker)
                live_data_der = self.getLiveData(derivative)

                ohlc = self.ohlc_tickers[ticker]

                profit = entry_price * ((100 + 4) / 100)
                if (
                    live_data_der["last_price"] >= profit
                    or live_data["last_price"] < ohlc["low"]
                    or datetime.datetime.now().time() >= datetime.time(15, 25)
                ):
                    print("-" * 10 + "EXIT" + "-" * 10)
                    print(
                        json.dumps(
                            {
                                "ticker": derivative,
                                "profit": profit - live_data_der["last_price"],
                            },
                            indent=2,
                        )
                    )
                    print("-" * 10 + "EXIT" + "-" * 10)

                    trade = self.generateLimitOrderSellStockOption(derivative, "EXIT")
                    self.sendTrade(trade)
                    # self.entered_tickers.discard(derivative)
                    self.deleteOrder(derivative)

            time.sleep(10)


def main():
    app = Worker7(name="worker_7")
    app.start()
