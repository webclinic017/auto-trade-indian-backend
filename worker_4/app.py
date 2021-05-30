from kiteconnect.connect import KiteConnect
from pymongo import MongoClient
from functions_db import get_key_token
from function_signals import *
import datetime
import os
import threading
import time

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

mongo = MongoClient('mongodb://db')
db = mongo['intraday'+str(datetime.date.today())]
collection = mongo['orders']

mongo_clients = mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

zerodha_id = os.environ['USERNAME']
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])

kite = KiteConnect(api_key=api_key, access_token=access_token)

scalp_buy_investment = int(os.environ['SCALP_BUY_INVESTMENT'])
scalp_sell_investment = int(os.environ['SCALP_SELL_INVESTMENT'])

#10557186
tickers_buy = ['NIFTY2160315500CE']

tickers_sell = []

n = 900
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

print('Worder 4 started')

for ticker in tickers_buy:
    t = threading.Thread(target=scalp_buy, args=[ticker, buy_quantity, n, kite])
    t.start()

for ticker in tickers_sell:
    t = threading.Thread(target=scalp_sell, args=[ticker, sell_quantity, n, kite])
    t.start()
    
import redis
import json

r = redis.StrictRedis(host='redis_pubsub', port=6379, decode_responses=True)

while True:
    positions = kite.positions()
    data = json.dumps(positions)
    
    r.publish('positions', data)
    time.sleep(n)