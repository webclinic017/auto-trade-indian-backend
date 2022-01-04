from interfaces.tradeapp import TradeApp
import math
import random
import time
from interfaces.constants import TRADE_ENV
import datetime

'''
NIFTY 50 -> {'tradable': False, 'mode': 'full', 'instrument_token': 256265, 'last_price': 17354.05, 'ohlc': {'high': 17400.8, 'low': 17238.5, 'open': 17244.5, 'close': 17203.95}, 'change': 0.8724740539236544, 'exchange_timestamp': '2021-12-31 18:25:52'}

BANKNIFTY2210635300CE
'''

class CostlyCheap(TradeApp):

    def __init__(self, name, year, month, week):
        super().__init__(name)
        self.year = year
        self.month = month
        self.week = week

    def getCostlyCheap(self):
        nifty_live = self.getLiveData('NSE:NIFTY 50')
        print(nifty_live['last_price'])

        ce_price = math.floor(nifty_live['last_price'])
        pe_price = math.floor(nifty_live['last_price'])

        while ce_price % 50 != 0:
            ce_price -= 1
        
        while pe_price % 50 != 0:
            pe_price += 1
        
        ce_ticker = 'NSE:NIFTY' + self.year + self.month + self.week + str(ce_price) + 'CE'
        pe_ticker = 'NSE:NIFTY' + self.year + self.month + self.week + str(pe_price) + 'PE'

        if TRADE_ENV == 'prod':
            ce_live = self.getLiveData(ce_ticker)
            pe_ticker = self.getLiveData(pe_ticker)
        else:
            ce_live = {
                'last_price': random.randint(1, 100)
            }

            pe_live = {
                'last_price': random.randint(1, 100)
            }

        print(ce_live)
        print(pe_live)

        ce_diff = abs(ce_live['last_price'] - abs(nifty_live['last_price'] - ce_price))
        pe_diff = abs(pe_live['last_price'] - abs(nifty_live['last_price'] - pe_price))

        print(ce_ticker, pe_ticker)
        print(ce_diff, pe_diff)

        if ce_diff > pe_diff:
            costly = ce_ticker
            cheap = pe_ticker
        else:
            costly = pe_ticker
            cheap = ce_ticker

        return costly, cheap

    def entryStrategy(self):
        while True:

            if (
                datetime.datetime.now().time() < datetime.time(9, 33, 3)
                or datetime.datetime.now().time() > datetime.time(15, 10)
               
            ):
                continue

            costly, cheap = self.getCostlyCheap()

            print('COSTLY', costly)
            print('CHEAP', cheap)

            trade = self.generateMarketOrderBuyIndexOption(cheap, 1, 'ENTRY')
            self.sendTrade(trade)

            time.sleep(900)


    def exitStrategy(self):
        while True:
            orders = self.getAllOrders()

            for order in orders:
                ticker = order['ticker']
                average_entry_price = self.averageEntryprice(order['data'])
                
                if TRADE_ENV == 'prod':
                    ticker_live = self.getLiveData(ticker)
                else:
                    ticker_live = {
                        'last_price': random.randint(1, 100)
                    }
                
                profit_price = 110/100 * average_entry_price

                
                ticker_type = ''

                if 'CE' in ticker:
                    ticker_type = 'CE'
                else:
                    ticker_type = 'PE'


                costly, _ = self.getCostlyCheap()

                if ticker_type in costly:
                    trade = self.generateMarketOrderSellIndexOption(
                        ticker,
                        1,
                        'EXIT'
                    )
                    self.sendTrade(trade)
                    continue

                if ticker_live['last_price'] >= profit_price:
                    trade = self.generateMarketOrderSellIndexOption(
                        ticker,
                        1,
                        'EXIT'
                    )
                    self.sendTrade(trade)
                    continue
            

            time.sleep(10)

def main(year, month, week):
    app = CostlyCheap(name='buyers_sellers', year=year, week=week, month=month)
    app.start()