from flask import Flask
import os, json, time, threading, redis, requests
from websocket import WebSocketApp

from .utils import RedisDictonary

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

TOKEN_SERVER = os.environ['WS_HOST']
ORDERS_URI = f'ws://{TOKEN_SERVER}/ws/orders'
EXIT_SERVER = os.environ['EXIT_HOST']
REDIS_SERVER = os.environ['REDIS_HOST']
ZERODHA_CONSUMER = os.environ['ZERODHA_CONSUMER']

tickers_streamed = {}



def on_message(ws, message):
    order = json.loads(message)
    
    # only insert the completed orders
    if order['status'] == 'COMPLETE' and order['tag'] == 'ENTRY_INDEX':
        if order['tradingsymbol'] not in tickers_streamed:
            token = order['instrument_token']
            t = threading.Thread(target=requests.get, args=[f'http://{EXIT_SERVER}/stream_ticker/{token}'])
            t.start()
            tickers_streamed[token] = True
    
        # insert into redis database here
        RedisDictonary().insert(order['tradingsymbol'], order)

def on_open():
    print('CONNECTION OPENED')
    
# open connection for the redis server
r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379)

# listen for the live ticker data
def on_message_ticker(ws, message):
    data = json.loads(message)
    r_ticker.set(data['instrument_token'], message)

# websocket for reteriving live orders
ws = WebSocketApp(ORDERS_URI, on_message=on_message, on_open=on_open)

# flask application to initiate the streaming of tickers
app = Flask(__name__)

# root url
@app.route('/')
def home():
    return '', 200

# start the streaming of live ticker
@app.route('/stream_ticker/<token>')
def index(token):
    ws = WebSocketApp(f'ws://{TOKEN_SERVER}/ws/ticker/{token}', on_message=on_message_ticker)
    t = threading.Thread(target=ws.run_forever)
    t.start()
    requests.get(f'http://{ZERODHA_CONSUMER}/subscribe/{token}')
    return "", 200

def main():
    # start the orders websocket thread 
    t_socket = threading.Thread(target=ws.run_forever)
    t_socket.start()
    
    time.sleep(5)
    
    # start the flask server
    t = threading.Thread(target=app.run, args=['0.0.0.0', 8888])
    t.start()