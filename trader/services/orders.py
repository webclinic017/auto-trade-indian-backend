from flask import Flask, request
import os, json, time, threading, redis, requests, datetime
from websocket import WebSocketApp
from pymongo import MongoClient

from .utils import RedisOrderDictonary

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

TOKEN_SERVER = os.environ['WS_HOST']
ORDERS_URI = f'ws://{TOKEN_SERVER}/ws/orders'
EXIT_SERVER = os.environ['ORDERS_HOST']
REDIS_SERVER = os.environ['REDIS_HOST']
ZERODHA_CONSUMER = os.environ['ZERODHA_CONSUMER']
MONGO_DB_URI = os.environ['MONGO_URI']

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
        RedisOrderDictonary().insert(order['tradingsymbol'], order)

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

@app.route('/receive_order', methods=['POST'])
def receive_order():
    data = request.get_json()
    
    if data['tag'] == 'EXIT':
        return "", 200
    
    if data['trading_symbol'] not in tickers_streamed:
        token = data['instrument_token']
        requests.get(f'http://{EXIT_SERVER}/stream_ticker/{token}')
        tickers_streamed[data['trading_symbol']] = True
     
    RedisOrderDictonary().insert(data['trading_symbol'], data)
    return '', 200

# thread for saving the holded orders to the database
# def save_orders():
#     while True:
#         if datetime.datetime.now().time() > datetime.time(15, 30):
#             try:
#                 mongo = MongoClient(MONGO_DB_URI)
#                 date = str(datetime.date.today())
#                 db = mongo['orders']
#                 collection = db['orders_' + date]
#                 orders = RedisOrderDictonary().get_all()
#                 collection.insert_one({'orders':orders, 'status':0})
#                 break
#             except:
#                 break
        
#         time.sleep(10)

# thread for loading the order
def load_orders():
    orders = RedisOrderDictonary().get_all()
    
    for ticker in orders:
        order = orders[ticker][0]
        token = order['instrument_token']
        requests.get(f'http://{EXIT_SERVER}/stream_ticker/{token}')
        tickers_streamed[token] = True
        
    
    # mongo = MongoClient(MONGO_DB_URI)
    # date = str(datetime.date.today() - datetime.timedelta(days=1))
    # db = mongo['orders']
    # collection = db['orders_' + date]
    # orders = collection.find({})
    
    # if orders['status'] == 0:
    #     for ticker in orders:
    #         RedisOrderDictonary().insert(ticker, orders[ticker])
    #         order = orders[ticker]
    #         token = order['instrument_token']
    #         requests.get(f'http://{EXIT_SERVER}/stream_ticker/{token}')
    #         tickers_streamed[token] = True
        
    #     collection.update_one({'_id':orders['_id']}, {'status':1})
    

def main():
    # load all the holded orders
    try:
        load_orders()
    except:
        pass
    
    # start the orders websocket thread 
    # t_socket = threading.Thread(target=ws.run_forever)
    # t_socket.start()
    
    time.sleep(5)
    
    # start the flask server
    t = threading.Thread(target=app.run, args=['0.0.0.0', 8888])
    t.start()
    
    # run the database saving service
    # t = threading.Thread(target=save_orders)
    # t.start()