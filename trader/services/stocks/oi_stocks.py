from interfaces.tradeapp import TradeApp
import datetime
import time


class openintereststocks(TradeApp):

    entered_tickers = set()

    def entryStrategy(self):

        while True:
            now = datetime.datetime.now().time()
            if now >= datetime.time(9, 30) and now <= datetime.time(12, 30):
                for ticker in self.tickers:

                    try:
                        live_data = self.getLiveData(ticker)
                        live_data_ce = self.getLiveData(
                            self.tickers[ticker]["ce_ticker"]
                        )
                        live_data_pe = self.getLiveData(
                            self.tickers[ticker]["pe_ticker"]
                        )
                    except:
                        continue

                    if (
                        self.tickers[ticker]["total_power"] > 500
                        and live_data["last_price"] > self.tickers[ticker]["ltp"]
                        and live_data["last_price"] < self.tickers[ticker]["ce_target1"]
                        and self.tickers[ticker]["ce_ticker"]
                        not in self.entered_tickers
                    ):
                        buy = live_data_ce["depth"]["buy"][0]["price"]
                        sell = live_data_ce["depth"]["sell"][0]["price"]
                        diff_percent = (abs(sell - buy) / buy) * 100
                        print('diff_percent in oi_stocks',ticker,diff_percent)
                        if diff_percent < 5:
                            trade = self.generateLimitOrderBuyStockOption(
                                self.tickers[ticker]["ce_ticker"], "ENTRY"
                            )
                            self.sendTrade(trade)
                            self.entered_tickers.add(self.tickers[ticker]["ce_ticker"])

                    elif (
                        self.tickers[ticker]["total_power"] < -500
                        and live_data["last_price"] < self.tickers[ticker]["ltp"]
                        and live_data["last_price"] > self.tickers[ticker]["pe_target1"]
                        and self.tickers[ticker]["pe_ticker"]
                        not in self.entered_tickers
                    ):
                        buy = live_data_pe["depth"]["buy"][0]["price"]
                        sell = live_data_pe["depth"]["sell"][0]["price"]
                        diff_percent = (abs(sell - buy) / buy) * 100
                        print('diff_percent in oi_stocks',ticker,diff_percent)

                        if diff_percent < 5:
                            trade = self.generateLimitOrderBuyStockOption(
                                self.tickers[ticker]["pe_ticker"], "ENTRY"
                            )
                            self.sendTrade(trade)
                            self.entered_tickers.add(self.tickers[ticker]["pe_ticker"])
                time.sleep(300)
            else:
                time.sleep(1)

    def exitStrategy(self):

        while True:
            orders = self.getAllOrders()

            for order in orders:
                derivative = order["ticker"]
                ticker = self.derivative_map[derivative]

                live_ticker = self.getLiveData(ticker)
                live_derivative = self.getLiveData(derivative)
                orders_list=order["data"]
                entry_price=self.averageEntryprice(orders_list)
                profit = entry_price * ((100 + 10) / 100)
                loss = entry_price * ((100 - 5) / 100)

                if "CE" in derivative:
                    if (
                        live_ticker["last_price"] >= self.tickers[ticker]["ce_target2"]
                        or live_ticker["last_price"] < self.tickers[ticker]["ltp"]
                    ):
                        trade = self.generateLimitOrderSellStockOption(
                            derivative, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(derivative)
                
                elif "PE" in derivative:
                    if (
                        live_ticker["last_price"] <= self.tickers[ticker]["pe_target2"]
                        or live_ticker["last_price"] > self.tickers[ticker]["ltp"]
                    ):
                        trade = self.generateLimitOrderSellStockOption(
                            derivative, "EXIT"
                        )
                        self.sendTrade(trade)
                        self.deleteOrder(derivative)


                elif datetime.datetime.now() >= datetime.time(15, 10) or live_derivative['last_price'] >= profit:
                    trade = self.generateLimitOrderSellStockOption(derivative, "EXIT")
                    self.sendTrade(trade)
                    self.deleteOrder(derivative)

            time.sleep(10)

def main():
    app=openintereststocks(name='oi_stocks')
    app.start()
