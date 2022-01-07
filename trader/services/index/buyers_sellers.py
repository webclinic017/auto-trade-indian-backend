from interfaces.tradeapp import TradeApp
import math
import random
import time
import datetime
from interfaces.constants import TRADE_ENV

'''
NIFTY 50 -> {'tradable': False, 'mode': 'full', 'instrument_token': 256265, 'last_price': 17354.05, 'ohlc': {'high': 17400.8, 'low': 17238.5, 'open': 17244.5, 'close': 17203.95}, 'change': 0.8724740539236544, 'exchange_timestamp': '2021-12-31 18:25:52'}

BANKNIFTY2210635300CE
'''

class BuyersSellers(TradeApp):

    def __init__(self, name, year, month, week):
        super().__init__(name)
        self.year = year
        self.month = month
        self.week = week

    def getBuySellDiff(self):
        nifty_live = self.getLiveData('NSE:NIFTY 50')
        nifty_atm = (math.ceil(nifty_live['last_price'])//50)*50

        ce_tickers = []
        pe_tickers = []

        for i in range(1,5):
            ce_ticker = 'NSE:NIFTY' + self.year + self.month + self.week + str(i * 50 + nifty_atm) + 'CE'
            ce_tickers.append(ce_ticker)

            pe_ticker = 'NSE:NIFTY' + self.year + self.month + self.week + str(nifty_atm - i*50) + 'PE'
            pe_tickers.append(pe_ticker)

        
        ce_tickers.append('NSE:NIFTY' + self.year + self.month + self.week + str(nifty_atm) + 'CE')
        pe_tickers.append('NSE:NIFTY' + self.year + self.month + self.week + str(nifty_atm) + 'PE')

        diff_buy_sell_ce = []
        diff_buy_sell_pe = []

        for ticker in ce_tickers:
            if TRADE_ENV == 'prod':
                ticker_live = self.getLiveData(ticker)

                diff_buy_sell = ticker_live['total_buy_quantity'] - ticker_live['total_sell_quantity']
                print(ticker, diff_buy_sell)
                diff_buy_sell_ce.append(diff_buy_sell)
                print('total', diff_buy_sell_ce)

            else:
                diff_buy_sell_ce.append(random.randint(80, 100))

        for ticker in pe_tickers:
            if TRADE_ENV == 'prod':
                ticker_live = self.getLiveData(ticker)

                diff_buy_sell = ticker_live['total_buy_quantity'] - ticker_live['total_sell_quantity']
                diff_buy_sell_pe.append(diff_buy_sell)
            else:
                diff_buy_sell_pe.append(random.randint(80, 100))

        diff_ce = sum(diff_buy_sell_ce)
        diff_pe = sum(diff_buy_sell_pe)
        print('totalce',diff_ce,)
        print('totalpe',diff_pe)


        return diff_ce, diff_pe, ce_tickers, pe_tickers

    def entryStrategy(self):
        while True:

            if (
                datetime.datetime.now().time() < datetime.time(9, 33, 3)
                or datetime.datetime.now().time() > datetime.time(15, 10)
               
            ):
                continue

            try:
                diff_ce, diff_pe, ce_tickers, pe_tickers = self.getBuySellDiff()
            except Exception as e:
                print(e)
                time.sleep(60)
                continue

            if diff_ce>0 and diff_ce > diff_pe:
                for ticker in ce_tickers:
                    print('BUY:', ticker)

                    trade = self.generateMarketOrderBuyIndexOption(
                        ticker,
                        50,
                        'ENTRY'
                    )
                    self.sendTrade(trade)
            elif diff_pe>0 and diff_pe>diff_ce:
                for ticker in pe_tickers:
                    trade = self.generateMarketOrderBuyIndexOption(
                        ticker,
                        50,
                        'ENTRY'
                    )
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
                        'last_price': random.randint(80, 100)
                    }
                
                profit_price = 110/100 * average_entry_price

                diff_ce, diff_pe, _, _ = self.getBuySellDiff()

                ticker_type = ''

                if 'CE' in ticker:
                    ticker_type = 'CE'
                else:
                    ticker_type = 'PE'

                if ticker_type == 'CE':
                    if diff_ce < diff_pe:
                        trade = self.generateMarketOrderSellIndexOption(
                            ticker,
                            1,
                            'EXIT'
                        )
                        self.sendTrade(trade)
                        continue

                if ticker_type == 'PE':
                    if diff_pe < diff_ce:
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
    app = BuyersSellers(name='buyers_sellers', year=year, week=week, month=month)
    app.start()