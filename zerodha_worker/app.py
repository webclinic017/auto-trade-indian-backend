from pymongo import MongoClient
from functions_db import get_key_token
from flask import Flask, jsonify, request
from zerodha_functions import *
from functions_signals import compareResult, gen_data
import threading, os, pika, json, kiteconnect, requests, datetime, websocket
import math
import pandas as pd
import talib as tb # type: ignore
import numpy as np
import statsmodels.api as sm


# send_notification({
#     'notification': {
#         'title': 'ORDER PLACED HEDGE',
#         'body': json_data['trading_symbol'],
#     },
#     'trade': json_data 
# }, json_data['uri'])

def send_notification(data, uri):
    try:
        ws_publisher = websocket.create_connection(uri)
        ws_publisher.send(json.dumps(data))
        ws_publisher.close()
    except:
        pass


mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')


zerodha_id = os.environ['USERNAME']
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])

print(api_key, access_token)

DATE_FORMAT = '%Y-%M-%d'
# kite object
kite = kiteconnect.KiteConnect(api_key=api_key, access_token=access_token)

instruments = kite.instruments()
token_map = {}
for instrument in instruments:
    token_map[instrument['tradingsymbol']] = instrument


# print(token_map[instrument['tradingsymbol']])

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
            tag = data.get('tag', None)
            order_id = market_buy_order(kite, data['trading_symbol'], exchange, data['quantity'], tag)
            
            send_notification({
                'notification': {
                    'title': 'ORDER PLACED HEDGE',
                    'body': data['trading_symbol'],
                },
                'trade': data 
            }, data['uri'])
            
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
            tag = data.get('tag', None)
            order_id = market_sell_order(kite, data['trading_symbol'], exchange, data['quantity'], tag)
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
            tag = data.get('tag', None)
            order_id = limit_buy_order(kite, data['trading_symbol'], exchange, data['quantity'], data['price'], tag)
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
            tag = data.get('tag', None)
            order_id = limit_sell_order(kite, data['trading_symbol'], exchange, data['quantity'], data['price'], tag)
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

# get ema
@app.route('/get/ema/<symbol>')
def get_ema(symbol):
    token = token_map[symbol]['instrument_token']
    tday = datetime.date.today()
    fday = tday - datetime.timedelta(days=4)
    df = requests.post('http://zerodha_worker_index/get/historical_data', json={
        'fdate':str(fday),
        'tdate':str(tday),
        'token': token,
        'interval':'5minute'
    }).json()
    
    df = pd.DataFrame(df)
    df['volume_ema'] = tb.EMA(df['volume'], 7)
    ema = df.tail(1)['volume_ema'].values[0]
    
    return jsonify({
        'ema': ema
    })

# get rsi
@app.route('/get/rsi/<symbol>/<n>')
def get_rsi(symbol, n):
    n = int(n)
    token = token_map[symbol]['instrument_token']
    # print(token)
    tday = datetime.date.today()
    fday = tday - datetime.timedelta(days=4)
    df = requests.post('http://zerodha_worker_index/get/historical_data', json={
        'fdate':str(fday),
        'tdate':str(tday),
        'token': token,
        'interval':'15minute'
    }).json()
    
    df = pd.DataFrame(df)
    # print(df)
    
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
    try:
        quote = kite.quote(data)
        return jsonify(quote)
    except:
        return jsonify({})

# get ltp
@app.route('/get/ltp', methods=['POST'])
def get_ltp():
    tickers = request.get_json()['tickers']
    
    if len(tickers) == 0:
        return jsonify({'ltp':[]})
    
    ltp = kite.ltp(tickers)
    
    return jsonify({'ltp':ltp})

# generate the comparision file
@app.route('/compare_results', methods=['POST'])
def compare_results():
    data = request.get_json()
    cur = data['raw']['data'].pop()
    prev = data['raw']['data'].pop()
    latest_compare = compareResult(prev, cur)
    return jsonify(latest_compare)

# generate the calculations data
@app.route('/gen_data', methods=['POST'])
def generate_data():
    data = request.get_json()
    json_data = data['data']
    expiry = data['expiry']
    data = gen_data(json_data, expiry)
    return jsonify(data)

# get atr
@app.route('/get/atr/<symbol>')
def get_atr(symbol):
    token = token_map[symbol]['instrument_token']
    tday = datetime.date.today()
    fday = datetime.date.today() - datetime.timedelta(days=4)
    
    df = requests.post('http://zerodha_worker_index/get/historical_data', json={
        'fdate':str(fday),
        'tdate':str(tday),
        'token': token,
        'interval':'5minute'
    }).json()
    
    df = pd.DataFrame(df)
    df['TR'] = df['high'] - df['low']
    df['atr'] = tb.ATR(df["high"], df["low"], df["close"], 14)
    df_atr = df.tail(1)

    atr = int(list(x for x in df_atr['atr'])[0])
    tr = int(list(x for x in df_atr['TR'])[0])
    atr = atr if atr != None else tr
    atr = atr+(0.1*atr)

    return jsonify({
        'atr':atr
    })

# get ema_5813
@app.route('/get/ema_5813/<symbol>')
def ema_5813(symbol):
    token = token_map[symbol]['instrument_token']
    tday = datetime.date.today()
    fday = datetime.date.today()-datetime.timedelta(days=4)
    
    df = requests.post('http://zerodha_worker_index/get/historical_data', json={
        'fdate':str(fday),
        'tdate':str(tday),
        'token': token,
        'interval':'2minute'
    }).json()
    
    df = pd.DataFrame(df)
    df['ema_close5'] = tb.EMA(df["close"], 5)
    df['slope_5'] = (df['ema_close5']-df['ema_close5'].shift(1))/2
    df['ema_close8'] = tb.EMA(df["close"], 8)
    df['slope_8'] = (df['ema_close8']-df['ema_close8'].shift(1))/2
    df['ema_close13'] = tb.EMA(df["close"], 13)
    df['slope_13'] = (df['ema_close13']-df['ema_close13'].shift(1))/2
    df['ema_close20'] = tb.EMA(df["close"], 20)
    df['slope_20'] = (df['ema_close20']-df['ema_close20'].shift(1))/2

    df_ema_5813 = df.tail(1)
    ema_5 = int(list(x for x in df_ema_5813['ema_close5'])[0])
    ema_8 = int(list(x for x in df_ema_5813['ema_close8'])[0])
    ema_13 = int(list(x for x in df_ema_5813['ema_close13'])[0])
    ema_20 = int(list(x for x in df_ema_5813['ema_close20'])[0])

    slope_5 = (list(x for x in df_ema_5813['slope_5'])[0])
    slope_8 = (list(x for x in df_ema_5813['slope_8'])[0])
    slope_13 = (list(x for x in df_ema_5813['slope_13'])[0])
    slope_20 = (list(x for x in df_ema_5813['slope_20'])[0])
    cond1 = (ema_5 > ema_8) and (ema_8 > ema_13) and (ema_13 > ema_20)
    cond2 = (slope_5 >= 0.7) and (slope_8 >= 0.7) and (
        slope_13 >= 0.7) and (slope_20 >= 0.7)
    if cond1 and cond2:
        requirement = 1
    else:
        requirement = 0

    # requirement = cond1 and cond2
    print("ema for 581320 are" + ""+"" + symbol +
          str(ema_5), str(ema_8), str(ema_13), str(ema_20))
    print("slopes of 581320 are" + ""+"" + symbol + str(slope_5),
          str(slope_8), str(slope_13), str(slope_20))
    
    return jsonify({
        'requirement': requirement 
    })


# get slope
@app.route('/get/slope/<symbol>/<n>')
def slope(symbol, n):
    n = int(n)
    token = token_map[symbol]['instrument_token']
    tday = datetime.date.today()
    fday = datetime.date.today()-datetime.timedelta(days=4)
    
    df = requests.post('http://zerodha_worker_index/get/historical_data', json={
        'fdate':str(fday),
        'tdate':str(tday),
        'token': token,
        'interval':'2minute'
    }).json()
    
    df = pd.DataFrame(df)
    df_slope=df.copy()
    df_slope = df_slope.iloc[-1*n:,:]
    y = ((df_slope["open"] + df_slope["close"])/2).values
    x = np.array(range(n))
    y_scaled = (y - y.min())/(y.max() - y.min())
    x_scaled = (x - x.min())/(x.max() - x.min())
    x_scaled = sm.add_constant(x_scaled)
    # print(x_scaled.shape)
    # print(y_scaled.shape)
    model = sm.OLS(y_scaled,x_scaled)
    results = model.fit()
    slope = np.rad2deg(np.arctan(results.params[-1]))
    trend = None
    # slope = 1
    df["up"] = np.where(df["low"]>=df["low"].shift(1),1,0)
    df["dn"] = np.where(df["high"]<=df["high"].shift(1),1,0)
    if df["close"].values[-1] > df["open"].values[-1]:
        if df["up"][-1*n:].sum() >= 0.7*n:
            trend="uptrend"
    elif df["open"].values[-1] > df["close"].values[-1]:
        if df["dn"].iloc[-1*n:].sum() >= 0.7*n:
            trend= "downtrend"
    else:
        trend=None
    
    # print("(slope, trend) ", end="")
    print(slope, trend)
    
    return jsonify({
        'slope':slope,
        'trend':trend
    })


if __name__ == '__main__':
    app.run('0.0.0.0', 80)