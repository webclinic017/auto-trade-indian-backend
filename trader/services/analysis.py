import json, os, requests, redis, time, datetime
import pandas as pd
from pymongo import MongoClient

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

mongo = MongoClient(host='db', port=27017)
db = mongo['analysis']
collection = db['workers']

collection.drop()


ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
REDIS_SERVER = os.environ['REDIS_HOST']

r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379)

token_map = requests.get(f'http://{ZERODHA_SERVER}/get/token_map').json()


def getLivePrice(ticker):
    token = token_map[ticker]['instrument_token']
    return json.loads(r_ticker.get(token))


tickers_path = '/app/data/tickers.json'
data = json.loads(open(tickers_path, 'r').read())

tickers = data['tickers']


def main():
    print("analysis service")
    time.sleep(10)
    
    while True:
        now = datetime.datetime.now()
        
        if now.time() >= datetime.time(9, 15):
            for ticker in tickers.keys():
                # print(ticker)
                try:
                    live_data = getLivePrice(ticker)
                except:
                    continue
                
                # worker 7 and 8
                if now.time() <= datetime.time(9,25):
                    if live_data['ohlc']['open'] == live_data['ohlc']['low']:
                        for derivative in tickers[ticker]:
                            if 'CE' in derivative:
                                
                                collection.update_one({'worker':'worker_7'}, {'$push':{'tickers':derivative}}, True)
                                collection.update_one({'worker':'worker_8'}, {'$push':{'tickers':derivative}}, True)
                                
                    
                    if live_data['ohlc']['open'] == live_data['ohlc']['high']:
                        for derivative in tickers[ticker]:
                            if 'PE' in derivative:
                                
                                collection.update_one({'worker':'worker_7'}, {'$push':{'tickers':derivative}}, True)

                # worker 6
                if now.time() > datetime.time(9, 30):
                    high = live_data['ohlc']['high']
                    low = live_data['ohlc']['low']
                    ltp = live_data['last_price']

                    if ltp > high:
                        
                        for derivative in tickers[ticker]:
                            if 'CE' in derivative:
                                collection.update_one({'worker':'worker_6'}, {'$push':{'tickers':derivative}})
                    
                    if ltp < low:
                        
                        for derivative in tickers[ticker]:
                            if 'PE' in derivative:
                                collection.update_one({'worker':'worker_6'}, {'$push':{'tickers':derivative}})


                # worker 9
                if now.time() > datetime.time(9, 30):
                    obv = pd.DataFrame(requests.get(f'http://{ZERODHA_SERVER}/get/obv/{ticker}').json())
                    # print(obv)
                    

                    if obv.tail(1)['obv'].values[0] > obv['obv'].mean():
                        for derivative in tickers[ticker]:
                            if 'CE' in derivative:
                                collection.update_one({'worker':'worker_9'}, {'$push':{'tickers':derivative}})

                    elif obv.tail(1)['obv'].values[0] <= obv['obv'].mean() / 2:
                        for derivative in tickers[ticker]:
                            if 'CE' in derivative:
                                collection.update_one({'worker':'worker_9'}, {'$push':{'tickers':derivative}})

        time.sleep(15)