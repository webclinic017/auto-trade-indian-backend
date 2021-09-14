# from websocket import WebSocketApp
import json, threading, os, requests, redis
import time
from flask import Flask

ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
# ZERODHA_CONSUMER = os.environ['ZERODHA_CONSUMER']
# TOKEN_SERVER = os.environ['WS_HOST']
REDIS_SERVER = os.environ['REDIS_HOST']

r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379)

app = Flask(__name__)

# root url
@app.route('/')
def home():
    return '', 200

# def on_message_ticker(ws, message):
#     data = json.loads(message)
#     # print(data)
#     r_ticker.set(data['instrument_token'], message)

def get_liveData(tickers):
    while True:
        live_data = requests.post(f'http://{ZERODHA_SERVER}/get/quote', json={
            'tickers': tickers
        }).json()
        
        for ticker in live_data:
            tick = ticker.split(':')[1]
            r_ticker.set(tick, json.dumps(live_data[ticker], default=str))
        
        time.sleep(1)

def main():
    data = json.loads(open('/app/data/tickers.json', 'r').read())
    
    stocks_options = []
    for tick in data['tickers']:
        for stock in data['tickers'][tick]:
            stocks_options.append(f'NFO:{stock}')

    index = []
    for tick in data['index']:
        index.append(f'NSE:{tick}')
        
    stocks = list(map(lambda x : f'NSE:{x}', list(data['tickers'].keys())))
    
    tickers = stocks_options + index + stocks

    t = threading.Thread(target=get_liveData, args=[tickers])
    t.setDaemon(True)
    t.start()
    
    # tickers = list(data['tickers'].keys()) + data['index']
    # # seperate live data for index and stocks
    
    # # print(tickers)
    # token_map = requests.get(f'http://{ZERODHA_SERVER}/get/token_map').json()
    
    # for ticker in tickers:
    #     token = token_map[ticker]['instrument_token']
    #     ws = WebSocketApp(f'ws://{TOKEN_SERVER}/ws/ticker/{token}', on_message=on_message_ticker)
    #     requests.get(f'http://{ZERODHA_CONSUMER}/subscribe/{token}')
    #     t = threading.Thread(target=ws.run_forever)
    #     t.start()
    
    t = threading.Thread(target=app.run, args=['0.0.0.0', 8888])
    t.start()