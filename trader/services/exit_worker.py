import redis, os, time, json, datetime, requests
from services.utils import RedisOrderDictonary
from services.function_signals import send_trade

REDIS_SERVER = os.environ['REDIS_HOST']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']


r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379)


def main():
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
            
            try:
                ticker_data = json.loads(r_ticker.get(order['instrument_token']))
            except:
                continue
            
            try:
                data = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{ticker}/7').json()
                rsi = data['last_rsi']
                rsi_slope = data['last_slope']
            except:
                rsi = 999
                rsi_slope = 999
            
            print(ticker_data)
            ltp = ticker_data['last_price']
            print(((ltp - entry_price)/ltp) * 100, '% pnl')
            
            if ((ltp - entry_price)/ltp)* 100 >= 4 or rsi < 30 or rsi_slope < 0 or datetime.datetime.now().time() >= datetime.time(15, 25):
                # send a exit signal
                if 'buy' in order['endpoint']:
                    order['endpoint'] = order['endpoint'].replace('buy', 'sell')
                else:
                    order['endpoint'] = order['endpoint'].replace('sell', 'buy')
                
                trade = {
                    'endpoint': order['endpoint'],
                    'trading_symbol': order['trading_symbol'],
                    'exchange': order['exchange'],
                    'quantity': order['quantity'],
                    'tag': 'EXIT',
                    'uri': order['uri']
                }
                send_trade(trade)
                RedisOrderDictonary().clear(order['trading_symbol'])
            
            
        time.sleep(10)