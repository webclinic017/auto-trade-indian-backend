import json
from zerodha_functions import *
import websocket
from kiteconnect import KiteConnect
from pymongo import MongoClient
import requests
import os
import time
import redis

mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

token_map = mongo_clients['tokens']['tokens_map'].find_one()


PUBLISHER_HOST = os.environ['PUBLISHER_HOST']
PUBLISHER_PATH = os.environ['PUBLISHER_PATH']

PUBLISHER_URI = f'{PUBLISHER_HOST}{PUBLISHER_PATH}'


redis_host = 'redis_pubsub'
redis_port = 6379
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)


def send_notification(data):
    try:
        ws_publisher = websocket.create_connection(PUBLISHER_URI)
        ws_publisher.send(json.dumps(data))
        ws_publisher.close()
    except:
        pass

def start_trade(kite : KiteConnect, document, quantity):
    flag = False
    
    CE_KEY = 'CE_Stikes'
    PE_KEY = 'PE_Stikes'
    PERCENTAGE = 5/100
    
    ce_documents = document[CE_KEY]
    pe_documents = document[PE_KEY]
    
    for strike in ce_documents:
        ltp_ce = ce_documents[strike]['lastPrice']
        min_ltp_ce = ltp_ce*(1-PERCENTAGE)
        max_ltp_ce = ltp_ce*(1+PERCENTAGE)
        
        for strike_ in pe_documents:
            ltp_pe = pe_documents[strike_]['lastPrice']
            
            if ltp_pe >= min_ltp_ce and ltp_pe <= max_ltp_ce:
                print(ce_documents[strike]['weekly_Options_CE'], pe_documents[strike_]['weekly_Options_PE'])
                symbol = ce_documents[strike]['weekly_Options_CE']
                order_id = market_buy_order(
                    kite=kite,
                    quantity=quantity,
                    tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_NFO
                )
                
                time.sleep(1)
                order_details = kite.order_history(order_id).pop()
                data = r.get(f'{symbol}_ORDERS')
                if data == None:
                    data = []
                else:
                    data = json.loads(data)
                data.append(order_details)
                r.set(f'{symbol}_ORDERS', json.dumps(data, default=str))
                
                token = token_map[symbol]['token']
                requests.get(f'http://exit_worker/start_exit_streamer/{token}/{symbol}')
                send_notification({
                    'notification': {
                        'title': 'ORDER PLACED HEDGE',
                        'body': ce_documents[strike]['weekly_Options_CE']
                    },
                    'trade': {
                        'endpoint': '/place/market_order/buy',
                        'trading_symbol': ce_documents[strike]['weekly_Options_CE'],
                        'exchange': 'NFO',
                    }
                })
                
                symbol = pe_documents[strike_]['weekly_Options_PE']
                order_id = market_buy_order(
                    kite=kite,
                    tradingsymbol=symbol,
                    quantity=quantity,
                    exchange=kite.EXCHANGE_NFO
                )
                
                time.sleep(1)
                order_details = kite.order_history(order_id).pop()
                data = r.get(f'{symbol}_ORDERS')
                if data == None:
                    data = []
                else:
                    data = json.loads(data)
                data.append(order_details)
                r.set(f'{symbol}_ORDERS', json.dumps(data, default=str))
                
                token = token_map[symbol]['token']
                requests.get(f'http://exit_worker/start_exit_streamer/{token}/{symbol}')
                send_notification({
                    'notification': {
                        'title': 'ORDER PLACED HEDGE',
                        'body': pe_documents[strike_]['weekly_Options_PE']
                    },
                    'trade': {
                        'endpoint': '/place/market_order/buy',
                        'trading_symbol': pe_documents[strike_]['weekly_Options_PE'],
                        'exchange': 'NFO',
                    }
                })

                flag = True

                return
    
    if flag:
        return
        
        
    for strike in pe_documents:
        ltp_pe = pe_documents[strike]['lastPrice']
        min_ltp_pe = ltp_pe*(1-PERCENTAGE)
        max_ltp_pe = ltp_pe*(1+PERCENTAGE)
        
        for strike_ in ce_documents:
            ltp_ce = ce_documents[strike_]['lastPrice']
            
            if ltp_ce >= min_ltp_pe and ltp_ce <= max_ltp_pe:
                print(ce_documents[strike_]['weekly_Options_CE'], pe_documents[strike]['weekly_Options_PE'])
                symbol = ce_documents[strike_]['weekly_Options_CE']
                order_id = market_buy_order(
                    kite=kite,
                    tradingsymbol=symbol,
                    quantity=quantity,
                    exchange=kite.EXCHANGE_NFO
                )
                
                time.sleep(1)
                order_details = kite.order_history(order_id).pop()
                data = r.get(f'{symbol}_ORDERS')
                if data == None:
                    data = []
                else:
                    data = json.loads(data)
                data.append(order_details)
                r.set(f'{symbol}_ORDERS', json.dumps(data, default=str))
                
                token = token_map[symbol]['token']
                requests.get(f'http://exit_worker/start_exit_streamer/{token}/{symbol}')
                send_notification({
                    'notification': {
                        'title': 'ORDER PLACED HEDGE',
                        'body': ce_documents[strike_]['weekly_Options_CE']
                    },
                    'trade': {
                        'endpoint': '/place/market_order/buy',
                        'trading_symbol': ce_documents[strike_]['weekly_Options_CE'],
                        'exchange': 'NFO',
                    }
                })
                
                
                symbol = pe_documents[strike]['weekly_Options_PE']
                order_id = market_buy_order(
                    kite=kite,
                    tradingsymbol=symbol,
                    quantity=quantity,
                    exchange=kite.EXCHANGE_NFO
                )
                
                time.sleep(1)
                order_details = kite.order_history(order_id).pop()
                data = r.get(f'{symbol}_ORDERS')
                if data == None:
                    data = []
                else:
                    data = json.loads(data)
                data.append(order_details)
                r.set(f'{symbol}_ORDERS', json.dumps(data, default=str))
                
                token = token_map[symbol]['token']
                requests.get(f'http://exit_worker/start_exit_streamer/{token}/{symbol}')
                send_notification({
                    'notification': {
                        'title': 'ORDER PLACED HEDGE',
                        'body': pe_documents[strike]['weekly_Options_PE']
                    },
                    'trade': {
                        'endpoint': '/place/market_order/buy',
                        'trading_symbol': pe_documents[strike]['weekly_Options_PE'],
                        'exchange': 'NFO',
                    }
                })
                
                return
    
    return