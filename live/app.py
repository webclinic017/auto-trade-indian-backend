from datetime import timedelta
from kiteconnect import KiteTicker, KiteConnect
from utils.auth import get_key_token
from threading import Thread
from flask import Flask
import os, json, redis

# get the api_key and access_token
api_key, access_token = get_key_token(os.environ["AUTH_TOKEN"])

# kiteticker
kws = KiteTicker(api_key=api_key, access_token=access_token)
# kite connect
kite = KiteConnect(api_key=api_key, access_token=access_token)

# first make the mapping of ticker --> token and token --> ticker
instruments = kite.instruments()
token_map = {}
ticker_map = {}

for instrument in instruments:
    token_map[instrument["tradingsymbol"]] = instrument
    ticker_map[instrument["instrument_token"]] = instrument


# redis connection
rdb = redis.Redis(host="redis_server")

# callbacks on websockets
def on_connect(ws, response):
    print("connection opened to websocket")

    ws.subscribe([256265, 260105])
    ws.set_mode(ws.MODE_FULL, [256265, 260105])


def on_close(ws, code, reason):
    print(reason)
    ws.stop()


def on_error(ws, code, reason):
    print(code, reason)


def appendTickers(ticks):
    for tick in ticks:
        ticker = ticker_map[tick["instrument_token"]]["tradingsymbol"]
        # print(tick)

        rdb.set(ticker, json.dumps(tick, default=str), timedelta(seconds=5))


def on_ticks(ws, ticks):
    Thread(target=appendTickers, args=[ticks]).start()


kws.on_connect = on_connect
kws.on_ticks = on_ticks
kws.on_close = on_close
kws.on_error = on_error

app = Flask(__name__)


@app.route("/")
def index():
    return "", 200


@app.route("/subscribe/<int:token>")
def subscribe(token):
    kws.subscribe([token])
    kws.set_mode(kws.MODE_FULL, [token])

    return "", 200


Thread(target=app.run, args=["0.0.0.0", 80]).start()
kws.connect()
