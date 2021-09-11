from interfaces.tradeapp import TradeApp
import threading, time, datetime, json
from collections import defaultdict

class Worker4(TradeApp):
    
    quantity = 1
    
    def scalpBuy(self, ticker, trade):
        rsi, slope = self.getRSISlope(ticker)
        if rsi > 40 and slope > 0:
            self.sendTrade(trade)
    
    
    # entry logic
    def entryStrategy(self):
        while True:
            now = datetime.datetime.now().time()
            
            if now > datetime.time(9, 15):
                # stock options
                for ticker in self.getTickers():
                    trade = self.generateLimitOrderBuyStockOption(ticker, 'ENTRY_STOCK_OPT')
                    t = threading.Thread(target=self.scalpBuy, args=[ticker, trade])
                    t.start()
            
            time.sleep(300)
    
    # strategy for exit
    def exitStrategy(self):
        m        = defaultdict(int)
        acc      = defaultdict(list)
        acc_drop = defaultdict(int)

        iterations = 0

        while True:
            orders = self.getAllOrders()
            
            for order_ in orders:
                ticker = order_['ticker']
                
                entry_price = 0
                count = 0
                
                for order in order_['data']:
                    entry_price += order['entry_price']
                    count += 1    
                
                entry_price /= count
                # print("Entry_Price", entry_price)
                
                try:
                    ticker_data = self.getLiveData(ticker)
                except:
                    continue
                
                # print(ticker_data)

                try:
                    rsi, rsi_slope = self.getRSISlope(ticker)
                except:
                    rsi = 999
                    rsi_slope = 999
                
                # print(ticker_data)
                ltp = ticker_data['last_price']

             
                cur_accleration = (ltp - m[ticker]) / 100
                # m[ticker] = ltp
                acc[ticker].append(cur_accleration)
                prev_acc = None

                if iterations >= 2:
                    acc[ticker] = acc[ticker][len(acc[ticker])-7:]
                    #prev_acc = sum(acc[ticker]) / len(acc[ticker])
                    try:
                        prev_acc=acc[ticker][-2]
                    except:
                        prev_acc= cur_accleration
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

                delta_acceleration = ((cur_accleration-prev_acc)/prev_acc)*100

                pnl = ((ltp - entry_price)/ltp) * 100
                print({
                    'entry_price':entry_price,
                    'pnl': pnl,
                    'accleration': cur_accleration,
                    'prev_acc': prev_acc,
                    'ticker': ticker,
                    'rsi_slope': rsi_slope,
                    'rsi': rsi,
                    'delta_acc':delta_acceleration,
                    'acc_drop': flag,
                    'acc_drop_count':acc_drop[ticker]
                })


                if ((ltp - entry_price)/ltp)* 100 >= 4 or rsi < 30 or rsi_slope < 0 or datetime.datetime.now().time() >= datetime.time(21, 25) or (delta_acceleration <= -2) or flag:
                    # send a exit signal
                    if 'buy' in order['endpoint']:
                        order['endpoint'] = order['endpoint'].replace('buy', 'sell')
                        order['price'] = ticker_data['depth']['buy'][1]['price']
                    else:
                        order['endpoint'] = order['endpoint'].replace('sell', 'buy')
                        order['price'] = ticker_data['depth']['sell'][1]['price']
                    
                    trade = {
                        'endpoint': order['endpoint'],
                        'trading_symbol': order['trading_symbol'],
                        'exchange': order['exchange'],
                        'quantity': order['quantity'],
                        'tag': 'EXIT',
                        'uri': order['uri'],
                        'price': order['price']
                    }
                    
                    self.sendTrade(trade)
                    
                    self.deleteOrder(ticker)
                    
                    print("-"*10 + " EXIT CONDITIONS " + "-"*10)
                    exit_cond = {
                        'pnl': pnl,
                        'rsi': rsi,
                        'slope': rsi_slope,
                        'ticker': ticker,
                        'accleration': cur_accleration,
                        'prev_acc': prev_acc,
                        'delta_acc':delta_acceleration,
                        'acc_drop': flag,
                        'acc_drop_count':acc_drop[ticker]
                    }
                    print(json.dumps(exit_cond, indent=3))
                    print("-"*(10+17+10))
                
            
            iterations += 1
            time.sleep(10)


def main():
    app = Worker4(name='worker_4_stock')
    app.start()
    