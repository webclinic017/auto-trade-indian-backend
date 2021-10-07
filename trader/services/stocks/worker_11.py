# Volume based Strategy
from interfaces.tradeapp import TradeApp
import datetime, time, json, os

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()


class Worker11(TradeApp):
    quantity = 1

    entered_tickers = set()
    # ohlc_ticker = {}
    exchange = "NFO"

    def entryStrategy(self):
        # logic for entry
        while True:
            now = datetime.datetime.now().time()
            if now >= datetime.time(9, 30):

                for ticker in self.tickers:

                    # get the live data of the original ticker
                    try:
                        live_data = self.getLiveData(ticker)
                    except:
                        continue

                    # if ticker not in self.ohlc_ticker:
                    #     t = datetime.date.today()
                    #     try:
                    #         historical_data = self.getHistoricalData(ticker, t, t, '15minute')

                    #     except:
                    #         continue

                    #     o, h, l, c = historical_data.loc[0, ['open','high','low','close']].values
                    #     self.ohlc_ticker[ticker] = {
                    #         'ohlc': {
                    #             'open': o, 'high': h, 'low': l, 'close': c
                    #         },
                    #         'open':o,
                    #         'high': h,
                    #         'low':  l
                    #     }

                    # self.ohlc_ticker[ticker]['current_price'] = live_data['last_price']

                    # ohlc = self.ohlc_ticker[ticker]['ohlc']
                    # open_=self.ohlc_ticker[ticker]['open']
                    # high = self.ohlc_ticker[ticker]['high']
                    # low = self.ohlc_ticker[ticker]['low']

                    current_price = live_data["last_price"]
                    current_volume = live_data["volume"]
                    buy_quantity = live_data["buy_quantity"]
                    sell_quantity = live_data["sell_quantity"]

                    # if open_==low and current_price > high and self.tickers[ticker]['ce_ticker'] not in self.entered_tickers:
                    # if self.tickers[ticker]['total_power']>400 and current_price > self.tickers[ticker]['ltp'] and current_price<self.tickers[ticker]['ce_target1'] and self.tickers[ticker]['ce_ticker'] not in self.entered_tickers:

                    if (
                        current_volume > 1.2 * self.tickers[ticker]["avg_volume"]
                        and current_price > self.tickers[ticker]["prev_high"]
                        and buy_quantity > sell_quantity
                        and self.tickers[ticker]["ce_ticker"]
                        not in self.entered_tickers
                    ):

                        entry_conditions = (
                            {
                                "current_price": current_price,
                                "ticker": self.tickers[ticker]["ce_ticker"],
                            },
                        )

                        print("-" * 10 + "ENTRY CONDITION" + "-" * 10)
                        print(entry_conditions)
                        print("-" * 10 + "ENTRY CONDITION" + "-" * 10)

                        trade = self.generateLimitOrderBuyStockOption(
                            self.tickers[ticker]["ce_ticker"], "ENTRY"
                        )
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]["ce_ticker"])

                    elif (
                        current_volume > 1.2 * self.tickers[ticker]["avg_volume"]
                        and current_price < self.tickers[ticker]["prev_low"]
                        and sell_quantity > buy_quantity
                        and self.tickers[ticker]["pe_ticker"]
                        not in self.entered_tickers
                    ):
                        entry_conditions = {
                            "current_price": current_price,
                            "ticker": self.tickers[ticker]["pe_ticker"],
                        }

                        print("-" * 10 + "ENTRY CONDITION" + "-" * 10)
                        print(entry_conditions)
                        print("-" * 10 + "ENTRY CONDITION" + "-" * 10)

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
                derivative = order_["ticker"]
                ticker = self.derivative_map[derivative]
                master_ticker = self.tickers[ticker]

                if ticker not in self.ohlc_ticker:
                    continue

                live_data = self.getLiveData(ticker)
                live_data_der = self.getLiveData(derivative)

                current_price = live_data["last_price"]

                orders_list = order_["data"]
                entry_price = self.averageEntryprice(orders_list)
                pnl = self.getPnl(entry_price, live_data_der["last_price"])

                exit_contitions = {
                    # 'open': live_data['ohlc']['open'],
                    # 'high': live_data['ohlc']['high'],
                    # 'low': live_data['ohlc']['low'],
                    # 'close': live_data['ohlc']['close'],
                    "ticker": derivative,
                    "current_price": current_price,
                    # 'ohlc_start': self.ohlc_ticker[ticker]['ohlc'],
                    "pnl": pnl,
                }

                # if 'CE' in ticker:
                ohlc = self.ohlc_ticker[ticker]["ohlc"]
                low = ohlc["low"]
                current_price = live_data["last_price"]

                if (
                    "CE" in derivative
                    and current_price < master_ticker["ltp"]
                    or pnl >= 10
                    or datetime.datetime.now().time() >= datetime.time(15, 25)
                ):
                    trade = self.generateLimitOrderSellStockOption(derivative, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(derivative)
                    # self.entered_tickers.remove(derivative)

                    print("-" * 10 + "EXIT CONDITION" + "-" * 10)
                    print(exit_contitions)
                    print("-" * 10 + "EXIT CONDITION" + "-" * 10)

                elif (
                    "PE" in derivative
                    and current_price > master_ticker["ltp"]
                    or pnl >= 10
                    or datetime.datetime.now().time() >= datetime.time(15, 25)
                ):
                    trade = self.generateLimitOrderSellStockOption(derivative, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(derivative)
                    # self.entered_tickers.remove(derivative)

                    print("-" * 10 + "EXIT CONDITION" + "-" * 10)
                    print(exit_contitions)
                    print("-" * 10 + "EXIT CONDITION" + "-" * 10)

            time.sleep(10)


def main():
    app = Worker11(name="worker_11")
    app.start()
