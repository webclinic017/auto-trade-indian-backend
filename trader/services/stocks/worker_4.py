import os, threading, time, requests
from services.function_signals import *


os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()


scalp_buy_investment = int(os.environ['SCALP_BUY_INVESTMENT'])
scalp_sell_investment = int(os.environ['SCALP_SELL_INVESTMENT'])

# stocks
tickers_buy = [
   
]

tickers_sell = [
    
]

# stock options
tickers_buy_stock_opt = [
    'MARUTI21JUL7500PE','BAJFINANCE21JUL6200CE',
    'HEROMOTOCO21JUL2900CE','SBILIFE21JUL1020CE','INFY21JUL1560PE',
    'SBIN21JUL430PE','HDFCBANK21JUL1540CE','TATAMOTORS21JUL315PE',
    'IBULHSGFIN21JUL270CE','SUNPHARMA21JUL670CE','TCS21JUL3280PE',
    'VEDL21JUL270CE', 'RELIANCE21JUL2120PE' 
]

tickers_sell_stock_opt = [
    
]

# stock futures
tickers_buy_stock_fut = [
    
]

tickers_sell_stock_fut = [
    
]

n = 900
n_min = 15

token_map = requests.get('http://zerodha_worker_index/get/token_map').json()

def main():
    print('Worder 4 started')

    # stocks
    for ticker in tickers_buy:
        t = threading.Thread(target=scalp_buy_stock, args=[ticker, token_map[ticker]['lot_size'], n])
        t.start()

    for ticker in tickers_sell:
        t = threading.Thread(target=scalp_sell_stock, args=[ticker, token_map[ticker]['lot_size'], n])
        t.start()

    # stock options
    for ticker in tickers_buy_stock_opt:
        t = threading.Thread(target=scalp_buy_stock_option, args=[ticker, token_map[ticker]['lot_size'], n])
        t.start()

    for ticker in tickers_sell_stock_opt:
        t = threading.Thread(target=scalp_sell_stock_option, args=[ticker, token_map[ticker]['lot_size'], n])
        t.start()

    # stock futures
    for ticker in tickers_buy_stock_fut:
        t = threading.Thread(target=scalp_buy_stock_fut, args=[ticker, token_map[ticker]['lot_size'], n])
        t.start()

    for ticker in tickers_sell_stock_fut:
        t = threading.Thread(target=scalp_sell_stock_fut, args=[ticker, token_map[ticker]['lot_size'], n])
        t.start()


    import redis
    import json

    r = redis.StrictRedis(host='redis_pubsub', port=6379, decode_responses=True)

    while True:
        # stocks
        positions = requests.get('http://zerodha_worker_index/get/positions').json()
        quote_tickers = tickers_buy_stock_opt + tickers_sell_stock_opt + tickers_buy_stock_fut + tickers_sell_stock_fut
        quote_tickers_ = tickers_buy + tickers_sell
        # stock options
        quote_tickers = list(map(lambda x : f'NFO:{x}', quote_tickers))
        quote_tickers_ = list(map(lambda x : f'NSE:{x}', quote_tickers_))

        quote_tickers = quote_tickers + quote_tickers_
        quotes = requests.post('http://zerodha_worker_index/get/quote', json={'tickers': quote_tickers}).json()
        
        # print(quotes)
        
        data = json.dumps({'positions':positions, 'quotes':quotes})
        r.publish('stock', data)
        
        data = json.dumps(quotes)
        r.publish('stock_option', data)
        r.publish('stock_fut', data)
        
        time.sleep(n)