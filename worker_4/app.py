from function_signals import *
import os
import threading
import time


os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()


scalp_buy_investment = int(os.environ['SCALP_BUY_INVESTMENT'])
scalp_sell_investment = int(os.environ['SCALP_SELL_INVESTMENT'])


tickers_buy = ['NIFTY2172216000CE']

tickers_sell = []

tickers_sell_depth = list(map(lambda x : f'NFO:{x}', tickers_sell))

buy_quantity_depth = {}
sell_quantity_depth = {}

buy_tickers_quote = list(map(lambda x : f'NFO:{x}', tickers_buy+tickers_sell))
quote_buy = requests.post('http://zerodha_worker_index/get/quote', json={'tickers':buy_tickers_quote}).json()

for ticker in tickers_buy + tickers_sell:
    buy_quantity_depth[ticker] = quote_buy[f'NFO:{ticker}']['buy_quantity']
    sell_quantity_depth[ticker] = quote_buy[f'NFO:{ticker}']['sell_quantity']


n = 300
n_min = 15

try:
    buy_quantity = int((scalp_buy_investment/len(tickers_buy))/3600/n_min)
except:
    buy_quantity = 0

try:
    sell_quantity = int((scalp_sell_investment/len(tickers_sell))/3600/n_min)
except:
    sell_quantity = 0

if buy_quantity < 1:
    buy_quantity = 75

if sell_quantity < 1:
    sell_quantity = 1

print('Worker 4 started')
print(buy_quantity)

for ticker in tickers_buy:
    t = threading.Thread(target=scalp_buy, args=[ticker, buy_quantity, n])
    t.start()

for ticker in tickers_sell:
    t = threading.Thread(target=scalp_sell, args=[ticker, sell_quantity, n])
    t.start()
    
import redis
import json

r = redis.StrictRedis(host='redis_server_index', port=6379, decode_responses=True)

while True:
    positions = requests.get('http://zerodha_worker_index/get/positions').json()
    data = json.dumps(positions)

    r.publish('positions', data)
    time.sleep(n)