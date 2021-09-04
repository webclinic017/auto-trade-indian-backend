import redis, os, time, json, datetime, requests
from services.utils import RedisOrderDictonary
from services.function_signals import send_trade
from collections import defaultdict
import random

REDIS_SERVER = os.environ['REDIS_HOST']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']

r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379)


# def second_derivative(arr):
#     result = list(np.diff(np.diff(arr, 1), 1))
#     if len(result) >= 2:
#         return [result.pop(), result.pop()]
#     else:
#         return [1,1]

TEST_MODE = False

def main():
    m = defaultdict(int)
    acc = defaultdict(list)
    acc_drop = defaultdict(int)

    iterations = 0

    while True:
        orders = RedisOrderDictonary().get_all()
        print(orders)
        
        for ticker in orders:
            entry_price = 0
            count = 0
            
            for order in orders[ticker]:
                entry_price += order['entry_price']
                count += 1    
            
            entry_price /= count
            # print("Entry_Price", entry_price)
            
            try:
                ticker_data = json.loads(r_ticker.get(order['instrument_token']))
            except:
                continue
            
            # print(ticker_data)

            try:
                data = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{ticker}/7').json()
                rsi = data['last_rsi']
                rsi_slope = data['last_slope']
            except:
                rsi = 999
                rsi_slope = 999
            
            # print(ticker_data)
            ltp = ticker_data['last_price']

           
            
            if TEST_MODE:
                ltp += random.random() * random.choice((1,-1))
            
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
           
            # previous_acc = 0

            # if len(acc[ticker]) >= 7:
            #     a = sum(acc[ticker]) / len(acc[ticker])
            #     previous_acc = a
            #     if cur_accleration >= 4*a and cur_accleration < 0:
            #         flag_acc = True
            #         acc[ticker] = []
            #     else:
            #         acc[ticker].pop(0)
            #         acc[ticker].append(cur_accleration)
            # else:
            #     acc[ticker].append(cur_accleration)

            flag = False

            if acc_drop[ticker] >= 5:
                flag = True
                acc_drop[ticker] = 0

            delta_acceleration = ((cur_accleration-prev_acc)/cur_accleration)*100

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
                'acc_drop': flag
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
                send_trade(trade)
                RedisOrderDictonary().clear(order['trading_symbol'])
                print("-"*10 + " EXIT CONDITIONS " + "-"*10)
                exit_cond = {
                    'pnl': pnl,
                    'rsi': rsi,
                    'slope': rsi_slope,
                    'ticker': ticker,
                    'accleration': cur_accleration,
                    'prev_acc': prev_acc,
                    'acc_drop': flag,
                }
                print(json.dumps(exit_cond, indent=3))
                print("-"*(10+17+10))
            
        
        iterations += 1
        time.sleep(10)