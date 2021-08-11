from .function_signals import *
import os
import threading
import time, datetime
from pymongo import MongoClient

ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
REDIS_SERVER = os.environ['REDIS_HOST']
MONGO_DB_URI = os.environ['MONGO_URI']
today = str(datetime.date.today())

def main():
    os.environ['TZ'] = 'Asia/Kolkata'
    time.tzset()

    mongo = MongoClient(MONGO_DB_URI)
    db = mongo['intraday_' + today]
    collection = db['index_master']

    scalp_buy_investment = int(os.environ['SCALP_BUY_INVESTMENT'])
    scalp_sell_investment = int(os.environ['SCALP_SELL_INVESTMENT'])

    tickers_buy = ['BANKNIFTY2180534900CE','BANKNIFTY2180534600PE','NIFTY2180516000CE','NIFTY2180515900PE']
    tickers_sell = []

    buy_quantity_depth = {}
    sell_quantity_depth = {}

    buy_tickers_quote = list(map(lambda x : f'NFO:{x}', tickers_buy+tickers_sell))
    quote_buy = requests.post(f'http://{ZERODHA_SERVER}/get/quote', json={'tickers':buy_tickers_quote}).json()
    print(quote_buy)

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
        buy_quantity = 50
    if sell_quantity < 1:
        sell_quantity = 1

    print('Worker 4 started')
    print(buy_quantity)

    for ticker in tickers_buy:
        t = threading.Thread(target=scalp_buy, args=[ticker, buy_quantity, n])
        print(f"starting thread for {ticker} worker 4 scalp buy")
        t.start()

    for ticker in tickers_sell:
        t = threading.Thread(target=scalp_sell, args=[ticker, sell_quantity, n])
        print(f"starting thread for {ticker} worker 4 scalp sell")
        t.start()
        
    import redis
    import json

    r = redis.StrictRedis(host=REDIS_SERVER, port=6379, decode_responses=True)

    while True:
        
        # pull the latest documents
        latest_doc_nifty = collection.find_one({'ticker': 'NIFTY'}, {'$slice':{-1}})
        latest_doc_banknifty = collection.find_one({'ticker': 'BANKNIFTY'}, {'$slice':{-1}})
        
        positions = requests.get(f'http://{ZERODHA_SERVER}/get/positions').json()
        data = json.dumps(positions)
        r.publish('positions', data)
        time.sleep(n)