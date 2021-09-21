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

class Worker9(TradeApp):

    entered_tickers = set()
    
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
                    else:
                        continue

                    
                    if live_data['buy_quantity'] > live_data['sell_quantity'] and self.tickers[ticker]['ce_ticker'] not in self.entered_tickers:
                        trade = self.generateLimitOrderBuyStockOption(self.tickers[ticker]['ce_ticker'], 'ENTRY_STOCK')
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]['ce_ticker'])
                        print(json.dumps({
                            'buy_quantity': live_data['buy_quantity'],
                            'sell_quantity': live_data['sell_quantity'],
                            'ticker': self.tickers[ticker]['ce_ticker']
                        }, indent=2))
                        # self.insertOrder(ticker, trade)

                    elif live_data['sell_quantity'] > live_data['buy_quantity'] and self.tickers[ticker]['pe_ticker'] not in self.entered_tickers:
                        trade = self.generateLimitOrderBuyStockOption(self.tickers[ticker]['pe_ticker'], 'ENTRY_STOCK')
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]['pe_ticker'])
                        # self.insertOrder(ticker, trade)
                        
                        print('-'*10 + 'ENTRY CONDITION' + '-'*10)
                        print(json.dumps({
                            'buy_quantity': live_data['buy_quantity'],
                            'sell_quantity': live_data['sell_quantity'],
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
                # ticker = self.derivative_map[derivative]
                entry_price = self.averageEntryprice(order['data'])

                # live_data = self.getLiveData(ticker)
                live_data_der = self.getLiveData(derivative)
                
                ohlc = live_data_der['ohlc']

                pnl = self.getPnl(entry_price, live_data_der['last_price'])
                if pnl >= 4 or live_data_der['last_price'] < ohlc['low']:
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
    app = Worker9(name='worker_9')
    app.start()