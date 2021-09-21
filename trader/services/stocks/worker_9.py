# Top gainers and Losers Strategy
'''
Description
extract the top gainers and losers list from NSE which is a list
in this strategy we will trade only the list of traders that are mentioned
'''
from interfaces.tradeapp import TradeApp
import datetime, time, json
from nsetools import Nse
nse = Nse()

class Worker7(TradeApp):

    entered_tickers = set()
    ohlc_tickers = {}
    
    def entryStrategy(self):
        while True:
            now = datetime.datetime.now()
            # print(now)

            if now.time() >= datetime.time(hour=9, minute=25):# and now.time() <= datetime.time(hour=9, minute=22):

                Gainers=nse.get_top_gainers()
                # Gainers=pd.DataFrame(Gainers)
                Losers=nse.get_top_losers()
                # Losers=pd.DataFrame(Losers)
                
                g=[]
                
                for item in Gainers:
                    #g.append(item['symbol'])
                    g.append("NSE:"+item['symbol'])

                l=[]

                for item in Losers:
                    #g.append(item['symbol'])
                    l.append("NSE:"+item['symbol'])

                for ticker in self.tickers:
                    if ticker in g or l:
                        try:
                            live_data = self.getLiveData(ticker)
                        except:
                            continue

                    buy_quantity=0,
                    sell_quantity=1915

                    if ticker not in self.ohlc_tickers:
                        self.ohlc_tickers[ticker] = list(live_data['buy_quantity'],live_data('sell_quantity'))
                    
                    ohlc = self.ohlc_tickers[ticker]
                    
                    if ohlc['open'] == ohlc['low'] and self.tickers[ticker]['ce_ticker'] not in self.entered_tickers:
                        trade = self.generateLimitOrderBuyStockOption(self.tickers[ticker]['ce_ticker'], 'ENTRY_STOCK')
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]['ce_ticker'])
                        print(json.dumps({
                            'ohlc': ohlc,
                            'ticker': self.tickers[ticker]['ce_ticker']
                        }, indent=2))
                        # self.insertOrder(ticker, trade)

                    elif ohlc['open'] == ohlc['high'] and self.tickers[ticker]['pe_ticker'] not in self.entered_tickers:
                        trade = self.generateLimitOrderBuyStockOption(self.tickers[ticker]['pe_ticker'], 'ENTRY_STOCK')
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]['pe_ticker'])
                        # self.insertOrder(ticker, trade)
                        
                        print('-'*10 + 'ENTRY CONDITION' + '-'*10)
                        print(json.dumps({
                            'ohlc': ohlc,
                            'ticker': self.tickers[ticker]['pe_ticker']
                        }, indent=2))
                        print('-'*10 + 'ENTRY CONDITION' + '-'*10)
            else:
                print("Cant enter Worker 7")


            time.sleep(5)


    def exitStrategy(self):
        while True:
            orders = self.getAllOrders()
            
            for order in orders:
                print(order)
                derivative = order['ticker']
                ticker = self.derivative_map[derivative]
                entry_price = self.averageEntryprice(order['data'])
                original_ticker = self.derivative_map[ticker]

                live_data = self.getLiveData(original_ticker)
                live_data_der = self.getLiveData(derivative)
                
                ohlc = self.ohlc_tickers[ticker]

                pnl = self.getPnl(entry_price, live_data_der['last_price'])
                if pnl >= 4 or live_data['last_price'] < ohlc['low']:
                    print('-'*10 + 'EXIT' + '-'*10)
                    print(json.dumps({
                        'ticker': derivative,
                        'pnl': pnl,
                    }, indent=2))
                    print('-'*10 + 'EXIT' + '-'*10)

                    trade = self.generateLimitOrderSellStockOption(derivative, 'EXIT')
                    self.sendTrade(trade)
                    self.entered_tickers.discard(derivative)
                    self.deleteOrder(derivative)
            
            time.sleep(10)


def main():
    app = Worker7(name='worker_7')
    app.start()