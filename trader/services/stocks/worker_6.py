from interfaces.tradeapp import TradeApp
import datetime, time, json

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
                
                for ticker in self.ticker:

                    live_data = self.getLiveData(ticker)
                    
                    if ticker not in self.ohlc_ticker:
                        t = datetime.date.today()
                        historical_data = self.getHistoricalData(ticker, t, t, '5minute')
                        historical_data = historical_data.set_index('date')
                        o, h, l, c, v = historical_data.between_time('9:30', '9:30').values[0]
                        
                        self.ohlc_ticker[ticker] = {
                            'ohlc': {
                                'open': o, 'high': h, 'low': l, 'close': c
                            },
                            'high': h,
                            'low':  l
                        }

                    ohlc = self.ohlc_ticker['ohlc']
                    high = self.ohlc_ticker['high']
                    low = self.ohlc_ticker['low']

                    current_price = live_data['last_price']

                    if current_price > high and ticker not in self.entered_tickers:
                        if 'CE' in ticker:
                            # buy the ticker
                            entry_conditions = {
                                'ohlc': ohlc,
                                'current_price': current_price 
                            }

                            print(json.dumps(entry_conditions, indent=2))
                            trade = self.generateLimitBuyStockOptionTrade(ticker, self.quantity, 'ENTRY_STOCK_OPT')
                            self.sendTrade(trade)
                            self.entered_tickers.add(ticker)
                    elif current_price < low and ticker not in self.entered_tickers:
                        if 'PE' in ticker:
                            # buy the ticker
                            entry_conditions = {
                                'ohlc': ohlc,
                                'current_price': current_price 
                            }

                            print(json.dumps(entry_conditions, indent=2))
                            trade = self.generateLimitBuyStockOptionTrade(ticker, self.quantity, 'ENTRY_STOCK_OPT')
                            self.sendTrade(trade)
                            self.entered_tickers.add(ticker)
            else:
                break

            time.sleep(300)

    def exitStrategy(self):
        while True:
            orders = self.getAllOrders()
            for order_ in orders:
                ticker = order_['ticker']
                live_data = self.getLiveData(ticker)

                orders_list = order_['data']
                entry_price = self.averageEntryprice(orders_list)
                pnl = self.getPnl(entry_price, live_data['last_price'])



                if 'CE' in ticker:
                    ohlc = live_data['ohlc']
                    low = ohlc['low']
                    current_price = live_data['last_price']

                    exit_contitions = {
                        'ohlc': ohlc,
                        'current_price': current_price
                    }
                    print(json.dumps(exit_contitions, indent=2))
                        
                    if current_price < low or pnl>=5:
                        trade = self.generateLimitSellStockOptionTrade(ticker, self.quantity, 'EXIT')
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        self.entered_tickers.remove(ticker)
                elif 'PE' in ticker or pnl>=5:
                    ohlc = live_data['ohlc']
                    high = ohlc['high']
                    current_price = live_data['last_price']
                    
                    if current_price > high:
                        trade = self.generateLimitSellStockOptionTrade(ticker, self.quantity, 'EXIT')
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        self.entered_tickers.remove(ticker)
            
            time.sleep(10)
            


def main():
    app = Worker6(name='worker_6')
    app.start()