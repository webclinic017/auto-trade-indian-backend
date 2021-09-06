from interfaces.tradeapp import TradeApp
import datetime, time, json, os

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

class Worker6(TradeApp):

    tickers = ['RELIANCE21SEP2460CE','HINDALCO21SEP470CE','TATASTEEL21SEP1420PE','ASIANPAINT21SEP3300PE']
    quantity = 1

    entered_tickers = set()
    ohlc_ticker = {}

    def entryStrategy(self):
        # logic for entry
        while True:
            now = datetime.datetime.now().time()
            if now >= datetime.time(9, 30):
                
                for ticker in self.tickers:

                    live_data = self.getLiveData(ticker)
                    
                    if ticker not in self.ohlc_ticker:
                        t = datetime.date.today()
                        historical_data = self.getHistoricalData(ticker, t, t, 'minute')
                        # print(historical_data)
                        # print(historical_data.loc[0, ['open','high','low','close']].values)
                        o, h, l, c = historical_data.loc[0, ['open','high','low','close']].values
                        
                        self.ohlc_ticker[ticker] = {
                            'ohlc': {
                                'open': o, 'high': h, 'low': l, 'close': c
                            },
                            'high': h,
                            'low':  l
                        }
                    
                    self.ohlc_ticker[ticker]['current_price'] = live_data['last_price']
                    print(self.ohlc_ticker[ticker])

                    ohlc = self.ohlc_ticker[ticker]['ohlc']
                    high = self.ohlc_ticker[ticker]['high']
                    low = self.ohlc_ticker[ticker]['low']

                    current_price = live_data['last_price']

                    if current_price > high and ticker not in self.entered_tickers:
                        entry_conditions = {
                            'ohlc': ohlc,
                            'current_price': current_price 
                        }

                        print(json.dumps(entry_conditions, indent=2))
                        trade = self.generateLimitOrderBuyStockOption(ticker, 'ENTRY_STOCK_OPT')
                        self.sendTrade(trade)
                        self.entered_tickers.add(ticker)

            time.sleep(300)

    def exitStrategy(self):
        while True:
            orders = self.getAllOrders()
            for order_ in orders:
                ticker = order_['ticker']

                if ticker not in self.ohlc_ticker:
                    continue

                try:
                    live_data = self.getLiveData(ticker)
                except:
                    continue

                current_price = live_data['last_price']

                orders_list = order_['data']
                entry_price = self.averageEntryprice(orders_list)
                pnl = self.getPnl(entry_price, live_data['last_price'])


                exit_contitions = {
                    'ohlc': self.ohlc_ticker[ticker]['ohlc'],
                    'current_price': current_price
                }
                print(json.dumps(exit_contitions, indent=2))

                # if 'CE' in ticker:
                ohlc = live_data['ohlc']
                low = ohlc['low']
                current_price = live_data['last_price']

                if current_price < low or pnl>=5:
                    trade = self.generateLimitOrderSellStockOption(ticker, 'EXIT')
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)
                    self.entered_tickers.remove(ticker)
            
            time.sleep(10)
            


def main():
    app = Worker6(name='worker_6')
    app.start()