import datetime
from entities.zerodha import HistoricalDataInterval
from interfaces.tradeapp import TradeApp
import time


class ExampleStrategy(TradeApp):
    today = datetime.date.today() - datetime.timedelta(3)

    def entryStrategy(self):
        while True:
            nifty_live = self.getLiveData("NSE:NIFTY 50")
            bank_nifty_live = self.getLiveData("NSE:NIFTY BANK")

            print(nifty_live.last_price)
            print(bank_nifty_live.last_price)

            print(nifty_live.depth.buy)
            print(bank_nifty_live.depth.buy)

            count = 0

            for historical_tick in self.getHistoricalDataDict(
                "NSE:NIFTY 50",
                self.today,
                self.today,
                HistoricalDataInterval.INTERVAL_5_MINUTE,
            ):

                print(historical_tick)

                count += 1

                if count == 3:
                    break

            time.sleep(10)

    def exitStrategy(self):
        return
