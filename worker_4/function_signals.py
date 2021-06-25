import datetime
import json
import redis
import requests


token_map = requests.get("http://zerodha_worker/get/token_map").json()

        
def scalp_buy(symbol, quantity, n, redis_host='redis_server', redis_port=6379):
    x = datetime.time(6,45)
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            positions = json.loads(message['data'])
            rsi = requests.get(f'http://zerodha_worker/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']

            print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x:
                if last_rsi > 40:
                    trade = {
                        'endpoint': '/place/market_order/buy',
                        'trading_symbol': symbol,
                        'exchange': 'NFO',
                        'quantity': quantity
                    }
                    
                    # publish trade to zerodha worker queue
                    print(json.dumps(trade, indent=2))


def scalp_sell(symbol, quantity, n, redis_host='redis_server', redis_port=6379):
    x = datetime.time(6,45)
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            positions = json.loads(message['data'])
            # print(positions)
            
            rsi = requests.get(f'http://zerodha_worker/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']
            print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x:
                if last_rsi < 40:
                    trade = {
                        'endpoint': '/place/market_order/sell',
                        'trading_symbol': symbol,
                        'exchange': 'NFO',
                        'quantity': quantity
                    }
                    # publish trade to zerodha_worker queue
                    print(json.dumps(trade, indent=2))