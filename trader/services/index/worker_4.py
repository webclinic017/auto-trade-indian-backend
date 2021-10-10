from interfaces.tradeapp import TradeApp
import time, json, threading, datetime
from collections import defaultdict
import datetime, time
import os

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()


class Worker4(TradeApp):

    NIFTY_QTY = 50
    BANK_NIFTY_QTY = 25

    def scalpBuy(self, ticker):
        rsi, slope = self.getRSISlope(ticker)
        live_data = self.getLiveData(ticker)

        ltp = live_data["last_price"]
        now = datetime.datetime.now().time()

        if "BANKNIFTY" in ticker:
            quantity = self.BANK_NIFTY_QTY
        else:
            quantity = self.NIFTY_QTY

        log = {
            "rsi": rsi,
            "slope": slope,
            "ticker": ticker,
            "ltp": ltp,
        }

        print(json.dumps(log, indent=2))
        if rsi >= 40 and slope >= 0 and now >= datetime.time(9, 30):
            trade = self.generateMarketOrderBuyIndexOption(ticker, quantity, "ENTRY")
            self.sendTrade(trade)
            return

    # strategy for entry
    def entryStrategy(self):
        while True:
            for ticker in self.index_tickers:
                threading.Thread(target=self.scalpBuy, args=[ticker]).start()

            time.sleep(310)

    # strategy for exit
    def exitStrategy(self):
        m = defaultdict(int)
        acc = defaultdict(list)
        acc_drop = defaultdict(int)

        iterations = 0

        while True:
            orders = self.getAllOrders()

            for order_ in orders:
                ticker = order_["ticker"]

                entry_price = self.averageEntryprice(order_["data"])
                # print("Entry_Price", entry_price)

                try:
                    ticker_data = self.getLiveData(ticker)
                except:
                    continue

                try:
                    rsi, rsi_slope = self.getRSISlope(ticker)
                except:
                    rsi, rsi_slope = 999, 999

                # print(ticker_data)
                ltp = ticker_data["last_price"]

                cur_accleration = (ltp - m[ticker]) / 100
                # m[ticker] = ltp
                acc[ticker].append(cur_accleration)
                prev_acc = None

                if iterations >= 2:
                    acc[ticker] = acc[ticker][len(acc[ticker]) - 7 :]
                    # prev_acc = sum(acc[ticker]) / len(acc[ticker])
                    try:
                        prev_acc = acc[ticker][-2]
                    except:
                        prev_acc = cur_accleration
                else:
                    prev_acc = cur_accleration

                if cur_accleration < prev_acc:
                    acc_drop[ticker] += 1
                else:
                    acc_drop[ticker] = 0

                flag = False

                if acc_drop[ticker] >= 5:
                    flag = True
                    acc_drop[ticker] = 0

                delta_acceleration = ((cur_accleration - prev_acc) / prev_acc) * 100

                pnl = self.getPnl(entry_price, ticker_data)
                print(
                    {
                        "entry_price": entry_price,
                        "pnl": pnl,
                        "accleration": cur_accleration,
                        "prev_acc": prev_acc,
                        "ticker": ticker,
                        "rsi_slope": rsi_slope,
                        "rsi": rsi,
                        "delta_acc": delta_acceleration,
                        "acc_drop": flag,
                        "acc_drop_count": acc_drop[ticker],
                    }
                )

                if (
                    ((ltp - entry_price) / ltp) * 100 >= 4
                    or rsi < 30
                    or datetime.datetime.now().time() >= datetime.time(21, 25)
                ):  #  rsi_slope < 0 or (delta_acceleration <= -2) or flag:
                    # send a exit signal
                    trade = self.generateMarketOrderSellIndexOption(
                        order_["ticker"], 1, "EXIT"
                    )

                    self.sendTrade(trade)

                    self.deleteOrder(ticker)

                    print("-" * 10 + " EXIT CONDITIONS " + "-" * 10)
                    exit_cond = {
                        "pnl": pnl,
                        "rsi": rsi,
                        "slope": rsi_slope,
                        "ticker": ticker,
                        "accleration": cur_accleration,
                        "prev_acc": prev_acc,
                        "delta_acc": delta_acceleration,
                        "acc_drop": flag,
                        "acc_drop_count": acc_drop[ticker],
                    }
                    print(json.dumps(exit_cond, indent=3))
                    print("-" * (10 + 17 + 10))

            iterations += 1
            time.sleep(10)


def main():
    app = Worker4(name="worker_4_index")
    app.start()
