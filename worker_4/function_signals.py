import datetime
from kiteconnect import KiteConnect
import json
import datetime
from zerodha_functions import *
import redis

def loss_for_buyticker(position):
    average_price=position['average_price']
    last_price=position['last_price']
    buy_quantity=position['buy_quantity']
    total_buy_price=buy_quantity*average_price
    current_value=buy_quantity*last_price
    if current_value<total_buy_price:
        loss=current_value-total_buy_price
        loss_percent=(loss*total_buy_price)/100
    else:
        loss_percent=0
    return abs(loss_percent)

def loss_for_sellticker(position):
    average_price=position['average_price']
    last_price=position['last_price']
    sell_quantity=position['sell_quantity']
    total_sell_price=sell_quantity*average_price
    current_value=sell_quantity*last_price
    if current_value>total_sell_price:
        loss=total_sell_price-current_value
        loss_percent=(loss*total_sell_price)/100
    else:
        loss_percent=0
    return abs(loss_percent)
        

def scalp_buy(symbol, quantity, n, kite : KiteConnect, redis_host='redis_pubsub', redis_port=6379):
    x = datetime.time(6,45)
    total_quantity = quantity
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            positions = json.loads(message['data'])
            # print(positions)
            # print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x:
                market_buy_order(
                    kite,
                    symbol,
                    kite.EXCHANGE_NSE,
                    quantity
                )
                total_quantity += quantity
                print(f'[***] Buy ORDER PLACED {symbol} [***]')



def scalp_sell(symbol, quantity, n, kite : KiteConnect, redis_host='redis_pubsub', redis_port=6379):
    x = datetime.time(6,45)
    total_quantity = quantity
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            positions = json.loads(message['data'])
            # print(positions)
            # print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x:
                market_sell_order(
                    kite,
                    symbol,
                    kite.EXCHANGE_NSE,
                    quantity
                )
                total_quantity += quantity
                print(f'[***] Sell ORDER PLACED {symbol} [***]')
