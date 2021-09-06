from interfaces.tradeapp import TradeApp
import time, json, threading, datetime
from collections import defaultdict


class Worker4(TradeApp):
    
    tickers = ["BANKNIFTY2190936800PE","BANKNIFTY2190936900CE" ,"NIFTY2190917400CE","NIFTY2190917300PE"]
    buy_quantity = 1
    sell_quantity = 1
    
    def scalpBuy(self, ticker, data):
        rsi, slope = self.getRSISlope(ticker)
        live_data = self.getLiveData(ticker)
        ltp = live_data['last_price']
        
        log = {
            'rsi': rsi,
            'slope': slope,
            'ticker': ticker,
            'ltp': ltp,
            'cheaper_option': data['cheaper_option']
        }
        
        print(json.dumps(log, indent=2))
        if rsi > 40 and slope > 0:
            trade = self.generateIndexOptionBuyTrade(ticker, self.buy_quantity, 'ENTRY_INDEX')
            self.sendTrade(trade)
            return
    
    # strategy for entry
    def entryStrategy(self):
        while True:
            latest_nifty = self.getDataIndexTicker('NIFTY')
            latest_banknifty = self.getDataIndexTicker('BANKNIFTY')
            
            if latest_nifty['data'] == 0 or latest_banknifty['data'] == 0:
                time.sleep(10)
                continue
            
            latest_nifty = latest_nifty['data'].pop()
            latest_banknifty = latest_banknifty['data'].pop()
            
            for ticker in self.tickers:
                if 'BANKNIFTY' in ticker:
                    data = latest_banknifty
                else:
                    data = latest_nifty
                threading.Thread(target=self.scalpBuy, args=[ticker, data]).start()
            
            time.sleep(310)
            
    
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
    app = Worker4(name='worker_4')
    app.start()