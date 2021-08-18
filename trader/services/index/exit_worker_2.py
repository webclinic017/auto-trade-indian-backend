from services.utils import RedisOrderDictonary, RedisWorker5Dict
from services.function_signals import send_trade
import json, redis, os, time

REDIS_SERVER = os.environ['REDIS_HOST']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']

r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379)

def main():
    while True:
        orders = RedisOrderDictonary().get_all()
        ticker_pairs = RedisWorker5Dict().get_all()
        
        print(ticker_pairs)
        
        for ticker_pair in ticker_pairs:
            ticker_a, ticker_b = ticker_pair.split("-")
            pnl = {}
            
            if ticker_a in orders and ticker_b in orders:
                # for ticker a
                entry_price = 0
                count = 0
                
                for order_a in orders[ticker_a]:
                    entry_price += order_a['entry_price']
                    count += 1
                
                entry_price /= count
                
                try:
                    ticker_data = ticker_data = json.loads(r_ticker.get(order_a['instrument_token']))
                except:
                    continue
                
                ltp = ticker_data['last_price']
                pnl[ticker_a] = ((ltp-entry_price)/ltp)*100
                
                # for ticker b
                entry_price = 0
                count = 0
                
                for order_b in orders[ticker_b]:
                    entry_price += order_b['entry_price']
                    count += 1
                
                entry_price /= count
                
                try:
                    ticker_data = ticker_data = json.loads(r_ticker.get(order_b['instrument_token']))
                except:
                    continue
                
                ltp = ticker_data['last_price']
                pnl[ticker_b] = ((ltp-entry_price)/ltp)*100
                
            if ticker_a in pnl and ticker_b in pnl:
                if pnl[ticker_a] + pnl[ticker_b] >= 4:
                    
                    # exit the ticker a
                    if 'buy' in order_a['endpoint']:
                        order_a['endpoint'] = order_a['endpoint'].replace('buy', 'sell')
                    else:
                        order_a['endpoint'] = order_a['endpoint'].replace('sell', 'buy')
                    
                    trade = {
                        'endpoint': order_a['endpoint'],
                        'trading_symbol': order_a['trading_symbol'],
                        'exchange': order_a['exchange'],
                        'quantity': order_a['quantity'],
                        'tag': 'EXIT',
                        'uri': order_a['uri']
                    }
                    send_trade(trade)
                    RedisOrderDictonary().clear(order_a['trading_symbol'])
                    
                    # exit the ticker b
                    if 'buy' in order_b['endpoint']:
                        order_b['endpoint'] = order_b['endpoint'].replace('buy', 'sell')
                    else:
                        order_b['endpoint'] = order_b['endpoint'].replace('sell', 'buy')
                    
                    trade = {
                        'endpoint': order_b['endpoint'],
                        'trading_symbol': order_b['trading_symbol'],
                        'exchange': order_b['exchange'],
                        'quantity': order_b['quantity'],
                        'tag': 'EXIT',
                        'uri': order_b['uri']
                    }
                    send_trade(trade)
                    RedisOrderDictonary().clear(order_b['trading_symbol'])
        time.sleep(10)