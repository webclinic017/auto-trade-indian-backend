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

                Gainers=nse.get_top_fno_gainers()
                # Gainers=pd.DataFrame(Gainers)
                Losers=nse.get_top_fno_losers()
                # Losers=pd.DataFrame(Losers)
                
                g=[]
                
                for item in Gainers:
                    #g.append(item['symbol'])
                    g.append("NSE:"+item['symbol'])
                # print('gainers', g)

                l=[]

                for item in Losers:
                    #g.append(item['symbol'])
                    l.append("NSE:"+item['symbol'])
                # print('losers', l)


                for ticker in g or l:
                    try:
                        live_data=self.getLiveData(ticker)
                        ce_ticker = self.tickers[ticker]['ce_ticker']
                        pe_ticker = self.tickers[ticker]['pe_ticker']
                        live_ce = self.getLiveData(ce_ticker)
                        live_pe = self.getLiveData(pe_ticker)
                    except:
                        continue

                    
                    if live_data['buy_quantity'] >= 1.5*live_data['sell_quantity'] and self.tickers[ticker]['ce_ticker'] not in self.entered_tickers and self.price_diff(live_ce['depth']['sell'][0]['price'], live_ce['depth']['buy'][0]['price']) < 5:
                        # print(self.tickers[ticker]['ce_ticker'])
                        trade = self.generateLimitOrderBuyStockOption(self.tickers[ticker]['ce_ticker'], 'ENTRY_STOCK')
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]['ce_ticker'])
                        print({
                            'buy_quantity': live_data['buy_quantity'],
                            'sell_quantity': live_data['sell_quantity'],
                            'ticker': self.tickers[ticker]['ce_ticker']
                        })
                        # self.insertOrder(ticker, trade)

                    elif live_data['sell_quantity'] >= 1.5* live_data['buy_quantity'] and self.tickers[ticker]['pe_ticker'] not in self.entered_tickers and self.price_diff(live_ce['depth']['sell'][0]['price'], live_ce['depth']['buy'][0]['price']) < 5:
                        # print(self.tickers[ticker]['pe_ticker'])
                        trade = self.generateLimitOrderBuyStockOption(self.tickers[ticker]['pe_ticker'], 'ENTRY_STOCK')
                        self.sendTrade(trade)
                        self.entered_tickers.add(self.tickers[ticker]['pe_ticker'])
                        # self.insertOrder(ticker, trade)
                        
                        print('-'*10 + 'ENTRY CONDITION' + '-'*10)
                        print({
                            'buy_quantity': live_data['buy_quantity'],
                            'sell_quantity': live_data['sell_quantity'],
                            'ticker': self.tickers[ticker]['pe_ticker']
                        })
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
                if pnl >= 10 or live_data_der['last_price'] < ohlc['low'] or datetime.datetime.now().time() >= datetime.time(15, 25) or pnl<=-5:
                    print('-'*10 + 'EXIT' + '-'*10)
                    print({
                        'ticker': derivative,
                        'pnl': pnl,
                    })
                    print('-'*10 + 'EXIT' + '-'*10)

                    trade = self.generateLimitOrderSellStockOption(derivative, 'EXIT')
                    self.sendTrade(trade)
                    # self.entered_tickers.remove(derivative)
                    self.deleteOrder(derivative)
            
            time.sleep(10)


def main():
    app = Worker9(name='worker_9')
    app.start()