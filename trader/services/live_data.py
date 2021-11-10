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

# first make the mapping of ticker --> token
instruments = kite.instruments()
token_map = {}
for instrument in instruments:
    token_map[instrument["tradingsymbol"]] = instrument

# second make the mapping of token --> ticker
ticker_map = {}
db = json.loads(open("/app/data/tickers.json").read())

for ticker in db["tickers"]:
    trading_symbol = ticker.split(":")[1]
    try:
        ticker_map[token_map[trading_symbol]["instrument_token"]] = ticker
    except:
        pass
    ce_ticker = db["tickers"][ticker]["ce_ticker"].split(":")[1]
    try:
        ticker_map[token_map[ce_ticker]["instrument_token"]] = db["tickers"][ticker][
            "ce_ticker"
        ]
    except:
        pass
    pe_ticker = db["tickers"][ticker]["pe_ticker"].split(":")[1]
    try:
        ticker_map[token_map[pe_ticker]["instrument_token"]] = db["tickers"][ticker][
            "pe_ticker"
        ]
    except:
        pass

for ticker in db["index"]:

    trading_symbol = ticker.split(":")[1]
    try:
        ticker_map[token_map[trading_symbol]["instrument_token"]] = ticker
    except:
        pass

    try:
        ce_ticker = db["index"][ticker]["ce_ticker"].split(":")[1]
        ticker_map[token_map[ce_ticker]["instrument_token"]] = db["index"][ticker][
            "ce_ticker"
        ]
    except:
        pass

    try:
        pe_ticker = db["index"][ticker]["pe_ticker"].split(":")[1]
        ticker_map[token_map[pe_ticker]["instrument_token"]] = db["index"][ticker][
            "pe_ticker"
        ]
    except:
        pass


tokens = list(ticker_map.keys())

# redis connection
rdb = redis.Redis(host=REDIS)

# callbacks on websockets
def on_connect(ws, response):
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL, tokens)


def on_close(ws, code, reason):
    print(reason)
    ws.stop()


def appendTickers(ticks):
    for tick in ticks:
        ticker = ticker_map[tick["instrument_token"]]
        rdb.set(ticker, json.dumps(tick, default=str))


def on_ticks(ws, ticks):
    Thread(target=appendTickers, args=[ticks]).run()


kws.on_connect = on_connect
kws.on_ticks = on_ticks
kws.on_close = on_close


def main():
    kws.connect(threaded=True)

    from flask import Flask

    app = Flask(__name__)

    @app.route("/")
    def index():
        return "", 200

    app.run("0.0.0.0", 8888)
