from interfaces.tradeapp import TradeApp
from nsetools import nse
import datetime, time


class Worker6(TradeApp):

    ohlc_ticker = {}

    NIFTY_QTY = 50
    BANK_NIFTY_QTY = 25

    def entryStrategy(self):
        for ticker in self.index_tickers:

            if datetime.datetime.now().time() < datetime.time(9, 20):
                continue

            t = datetime.date.today()
            if ticker not in self.ohlc_ticker:
                t = datetime.date.today()
                try:
                    historical_data = self.getHistoricalData(ticker, t, t, "15minute")
                except:
                    continue

                o, h, l, c = historical_data.loc[
                    0, ["open", "high", "low", "close"]
                ].values
                self.ohlc_ticker[ticker] = {"open": o, "high": h, "low": l, "close": c}

            live_data = self.getLiveData(ticker)

            if live_data["last_price"] > self.ohlc_ticker[ticker]["high"]:

                if "BANKNIFTY" in ticker:
                    quantity = self.BANK_NIFTY_QTY
                else:
                    quantity = self.NIFTY_QTY

                trade = self.generateMarketOrderBuyIndexOption(
                    ticker, quantity, "ENTRY"
                )
                self.sendTrade(trade)

            time.sleep(300)

    def exitStrategy(self):

        while True:
            orders = self.getAllOrders()

            for order_ in orders:
                ticker = order_["ticker"]
                entry_price = self.averageEntryprice(order_["data"])

                live_data = self.getLiveData(ticker)
                pnl = self.getPnl(entry_price, live_data["last_price"])

                if (
                    pnl >= 10
                    or live_data["last_price"] < self.ohlc_ticker[ticker]["low"]
                ):
                    trade = self.generateMarketOrderSellIndexOption(ticker, 1, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)

            time.sleep(10)


def main():
    app = Worker6(name="worker_6_index")
    app.start()
