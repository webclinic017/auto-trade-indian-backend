from pymongo import MongoClient
from functions_db import get_key_token
from flask import Flask, jsonify, request
from zerodha_functions import *
import threading, os, pika, json, kiteconnect, requests, datetime, websocket
import math
import pandas as pd
import talib as tb # type: ignore
import numpy as np


PUBLISHER_HOST = os.environ['PUBLISHER_HOST']
PUBLISHER_PATH = os.environ['PUBLISHER_PATH']

PUBLISHER_URI = f'{PUBLISHER_HOST}{PUBLISHER_PATH}'


def send_notification(data):
    # send_notification({
    #     'notification': {
    #         'title': 'ORDER PLACED HEDGE',
    #         'body': ce_documents[strike]['weekly_Options_CE']
    #     },
    #     'trade': trade 
    # })
    try:
        ws_publisher = websocket.create_connection(PUBLISHER_URI)
        ws_publisher.send(json.dumps(data))
        ws_publisher.close()
    except:
        pass




mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

token_map = mongo_clients['tokens']['tokens_map'].find_one()
token_map["_id"] = str(token_map["_id"])

worker = 'worker_5'

zerodha_id = os.environ['USERNAME']
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])


DATE_FORMAT = '%Y-%M-%d'

# kite object
kite = kiteconnect.KiteConnect(api_key=api_key, access_token=access_token)
# start the flask server
app = Flask(__name__)

@app.route('/get_api_key_token')
def get_api_key_token():
    return jsonify({
        'api_key': api_key,
        'access_token': access_token
    })


def check_validity(data):
    assert 'api_key' in data
    assert 'request_token' in data
    assert 'api_secret' in data


def validate_market_api(data):
    assert 'trading_symbol' in data, 'provide trading_symbol'
    assert 'exchange' in data, 'provide exchange'
    assert 'quantity' in data, 'provide quantity'

def validate_limit_api(data):
    assert 'trading_symbol' in data, 'provide trading_symbol'
    assert 'exchange' in data, 'provide exchange'
    assert 'quantity' in data, 'provide quantity'
    assert 'price' in data, 'provide price'
    


# place a market buy order
@app.route('/place/market_order/buy', methods=['POST'])
def place_market_buy_order():
    data = request.get_json()
    try:
        validate_market_api(data)

        if data['exchange'] == 'NFO':
            exchange = kite.EXCHANGE_NFO
        elif data['exchange'] == 'NSE':
            exchange = kite.EXCHANGE_NSE
        else:
            raise Exception('enter a valid exchange, NSE or NFO')
        
        try:
            order_id = market_buy_order(kite, data['trading_symbol'], exchange, data['quantity'])
            return jsonify({
                'message': f'order id is {order_id}'
            }), 200
        except Exception as ex: 
            return jsonify({
                'error': str(ex)
            }), 500
            
    except AssertionError as e:
        return jsonify({
            'error': str(e)
        }), 500

# place a market sell order
@app.route('/place/market_order/sell', methods=['POST'])
def place_market_sell_order():
    data = request.get_json()
    try:
        validate_market_api(data)
        
        if data['exchange'] == 'NFO':
            exchange = kite.EXCHANGE_NFO
        elif data['exchange'] == 'NSE':
            exchange = kite.EXCHANGE_NSE
        else:
            raise Exception('enter a valid exchange, NSE or NFO')
        
        try:
            order_id = market_sell_order(kite, data['trading_symbol'], exchange, data['quantity'])
            return jsonify({
                'message': f'order id is {order_id}'
            }), 200
        except Exception as ex: 
            print(ex)
            return jsonify({
                'error': str(ex)
            }), 500
            
    except AssertionError as e:
        print(e)
        return jsonify({
            'error': str(e)
        }), 500


# place limit buy order
@app.route('/place/limit_order/buy', methods=['POST'])
def place_limit_buy_order():
    data = request.get_json()
    try:
        validate_limit_api(data)
        
        if data['exchange'] == 'NFO':
            exchange = kite.EXCHANGE_NFO
        elif data['exchange'] == 'NSE':
            exchange = kite.EXCHANGE_NSE
        else:
            raise Exception('enter a valid exchange, NSE or NFO')
        
        try:
            order_id = limit_buy_order(kite, data['trading_symbol'], exchange, data['quantity'], data['price'])
            return jsonify({
                'message': f'order id is {order_id}'
            }), 200
        except Exception as ex:
            print(ex)
            return jsonify({
                'error': str(ex)
            }), 500
            
    except AssertionError as e:
        print(e)
        return jsonify({
            'error': str(e)
        }), 500

# place limit sell order
@app.route('/place/limit_order/sell', methods=['POST'])
def place_limit_sell_order():
    data = request.get_json()
    try:
        validate_limit_api(data)
        
        if data['exchange'] == 'NFO':
            exchange = kite.EXCHANGE_NFO
        elif data['exchange'] == 'NSE':
            exchange = kite.EXCHANGE_NSE
        else:
            raise Exception('enter a valid exchange, NSE or NFO')
        
        try:
            order_id = limit_sell_order(kite, data['trading_symbol'], exchange, data['quantity'], data['price'])
            return jsonify({
                'message': f'order id is {order_id}'
            }), 200
        except Exception as ex: 
            print(ex)
            return jsonify({
                'error': str(ex)
            }), 500
            
    except AssertionError as e:
        print(e)
        return jsonify({
            'error': str(e)
        }), 500

# get positions
@app.route('/get/positions')
def get_positions():
    positions = kite.positions()
    return jsonify(positions)

# get the token map
@app.route('/get/token_map')
def get_token_map():
    return jsonify(token_map)

# get historical data
@app.route('/get/historical_data', methods=['POST'])
def get_historical_data():
    data = request.get_json()
    # fdate = datetime.datetime.strptime(data['fdate'], DATE_FORMAT)
    # tdate = datetime.datetime.strptime(data['tdate'], DATE_FORMAT)
    historical_data = kite.historical_data(data['token'], data['fdate'], data['tdate'], data['interval'], False, False)
    return jsonify(historical_data)

# get rsi
@app.route('/get/rsi/<symbol>/<n>')
def get_rsi(symbol, n):
    n = int(n)
    token = token_map[symbol]['token']
    print(token)
    tday = datetime.date.today()
    fday = tday - datetime.timedelta(days=4)
    df = requests.post('http://zerodha_worker/get/historical_data', json={
        'fdate':str(fday),
        'tdate':str(tday),
        'token': token,
        'interval':'15minute'
    }).json()
    
    df = pd.DataFrame(df)
    print(df)
    
    try:
        df['rsi']=tb.RSI(df["close"],14)

        df_slope=df.copy()
        df_slope = df_slope.iloc[-1*n:,:]
        df_slope['slope']=tb.LINEARREG_SLOPE(df["rsi"], n)
        df_slope['slope_deg'] = df_slope['slope'].apply(math.atan).apply(np.rad2deg)
        

        last_rsi, last_deg =  df_slope.tail(1)['rsi'].values[0], df_slope.tail(1)['slope_deg'].values[0]
        print("RSI",last_rsi, "& RSI_Slope", last_deg)
        
        return jsonify({
            'last_rsi':last_rsi, 
            'last_slope': last_deg 
        })
    except:
        return jsonify({
            'last_rsi':0, 
            'last_slope': 0
        })
    

# get the quotes
@app.route('/get/quote', methods=['POST'])
def get_quote():
    data = request.get_json()['tickers']
    quote = kite.quote(data)
    return jsonify(quote)

@app.route('/get/ltp', methods=['POST'])
def get_ltp():
    tickers = request.get_json()['tickers']
    
    if len(tickers) == 0:
        return jsonify({'ltp':[]})
    
    ltp = kite.ltp(tickers)
    
    return jsonify({'ltp':ltp})

# t = threading.Thread(target=app.run, args=['0.0.0.0', 80])
# t.start()


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbit_mq')
)
channel = connection.channel()
channel.queue_declare(queue='zerodha_worker')

def callback(ch, method, properties, body):
    print('[**] ORDER RECEIVED [**]')
    json_data = json.loads(body.decode('utf-8'))
    end_point = json_data['endpoint']
    response = json.dumps(requests.post('http://zerodha_worker' + end_point, json=json_data).json(), indent=2)
    
    print(f'RESPONSE : {response}')
    print('ORDER')
    print(json.dumps(json_data, indent=2))
    


channel.basic_consume(queue='zerodha_worker', on_message_callback=callback, auto_ack=True)
print('WAITING FOR ORDERS')

t = threading.Thread(target=channel.start_consuming)
t.start()


if __name__ == '__main__':
    app.run('0.0.0.0', 80)