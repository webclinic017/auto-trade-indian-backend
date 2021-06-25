from pymongo import MongoClient
from functions_db import get_key_token
from flask import Flask, jsonify, request
from zerodha_functions import *
import threading, os, pika, json, kiteconnect, requests

mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

token_map = mongo_clients['tokens']['tokens_map'].find_one()

worker = 'worker_5'

zerodha_id = os.environ['USERNAME']
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])


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
    data = request.json
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
    data = request.json
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
    data = request.json
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
    data = request.json
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


t = threading.Thread(target=app.run, args=['0.0.0.0', 80])
t.start()

queue_list = [
    
]

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq')
    )
    channel = connection.channel()
    channel.queue_declare(queue='zerodha_worker')
    for queue in queue_list:
        channel.queue_declare(queue=queue)
    
    def callback(ch, method, properties, body):
        print('[**] ORDER RECEIVED [**]')
        json_data = json.loads(body.decode('utf-8'))
        end_point = json_data['endpoint']
        message = requests.post('http://zerodha_worker' + end_point, data=json_data).json()['message']
        
        print(f'MESSAGE : {message}')
        print('ORDER')
        print(json.dumps(json_data, indent=2))
        
    
    
    channel.basic_consume(queue='zerodha_worker', on_message_callback=callback, auto_ack=True)
    print('WAITING FOR ORDERS')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()