from kiteconnect import KiteTicker, KiteConnect
import os, json, redis
from threading import Thread
from interfaces.constants import REDIS


# get the api_key and access_token
api_key, access_token = os.environ["API_KEY"], os.environ["ACCESS_TOKEN"]

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
rdb = redis.Redis(host=REDIS)

# callbacks on websockets
def on_connect(ws, response):
    print("connection opened to websocket")


def on_close(ws, code, reason):
    print(reason)
    ws.stop()


def on_error(ws, code, reason):
    print(code, reason)


def appendTickers(ticks):
    for tick in ticks:
        ticker = ticker_map[tick["instrument_token"]]["tradingsymbol"]
        # print(tick)

        rdb.set(ticker, json.dumps(tick, default=str))


def on_ticks(ws, ticks):
    Thread(target=appendTickers, args=[ticks]).start()


kws.on_connect = on_connect
kws.on_ticks = on_ticks
kws.on_close = on_close
kws.on_error = on_error


def main():
    subscribed_tokens = set()

    kws.connect(threaded=True)

    from flask import Flask
    import logging

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    app = Flask(__name__)

    @app.route("/")
    def index():
        return "", 200

    @app.route("/subscribe/<int:token>")
    def subscribe(token):
        if token not in subscribed_tokens:
            kws.subscribe([token])
            kws.set_mode(kws.MODE_FULL, [token])

            subscribed_tokens.add(token)

        return "", 200

    app.run("0.0.0.0", 8888)
