import json, threading, os, requests, redis, time, datetime
import pandas as pd
from pymongo import MongoClient

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

mongo = MongoClient(host='db', port=27017)
db = mongo['analysis']


ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
REDIS_SERVER = os.environ['REDIS_HOST']

r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379)

token_map = requests.get(f'http://{ZERODHA_SERVER}/get/token_map').json()


def getLivePrice(ticker):
    token = token_map[ticker]['instrument_token']
    return json.loads(r_ticker.get(token))


tickers_path = '/app/data/tickers.json'
tickers = json.loads(open(tickers_path, 'r').read())

derivatives = tickers['derivatives']
tickers = tickers['tickers']

def main():
    while True:
        now = datetime.datetime.now()
        print(now)

        if now.time() >= datetime.time(9, 15):
            for ticker in tickers:
                try:
                    live_data = getLivePrice(ticker)
                except:
                    continue
                
                # worker 7 and 8
                if now.time() <= datetime.time(9,22):
                    if live_data['ohlc']['open'] == live_data['ohlc']['low']:
                        for derivative in derivatives:
                            if ticker in derivative and 'CE' in derivative:
                                collection = db['workers']
                                collection.update_one({'worker':'worker_7'}, {'$push':{'tickers':derivative}}, True)
                    
                    if live_data['ohlc']['open'] == live_data['ohlc']['high']:
                        for derivative in derivatives:
                            if ticker in derivative and 'PE' in derivative:
                                collection = db['workers']
                                collection.update_one({'worker':'worker_7'}, {'$push':{'tickers':derivative}}, True)

                # worker 6
                if now.time() > datetime.time(9, 30):
                    high = live_data['ohlc']['high']
                    low = live_data['ohlc']['low']
                    ltp = live_data['last_price']

                    if ltp > high:
                        collection = db['workers']

                        for derivative in derivatives:
                            if ticker in derivative and 'CE' in derivative:
                                collection.update_one({'worker':'worker_6'}, {'$push':{'tickers':derivative}})
                    
                    if ltp < low:
                        collection = db['workers']

                        for derivative in derivatives:
                            if ticker in derivative and 'PE' in derivative:
                                collection.update_one({'worker':'worker_6'}, {'$push':{'tickers':derivative}})


                # worker 9
                # take the average OBV of last 7 rows.
                # if current OBV is double or greater  the average OBV CE
                # if current OBV is half or less than half of the average OBV PE
                if now.time() > datetime.time(9, 30):
                    obv = pd.DataFrame(requests.get(f'http://{ZERODHA_SERVER}/get/obv/{ticker}').json())
                    print(obv)

                    if obv['obv'].tail(1)[0, 'obv'] > obv['obv'].mean():
                        for derivative in derivatives:
                            if ticker in derivative and 'CE' in derivative:
                                collection.update_one({'worker':'worker_9'}, {'$push':{'tickers':derivative}})

                    elif obv['obv'].tail(1)[0, 'obv'] <= obv['obv'].mean() / 2:
                        for derivative in derivatives:
                            if ticker in derivative and 'CE' in derivative:
                                collection.update_one({'worker':'worker_9'}, {'$push':{'tickers':derivative}})

        time.sleep(300)