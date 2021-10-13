from kiteconnect import KiteTicker
import requests, os, json, redis

# ZERODHA WORKER
ZERODHA_SERVER = os.environ["ZERODHA_WORKER_HOST"]
REDIS_SERVER = os.environ["REDIS_HOST"]

# get the api_key and access_token
credentials = requests.get(f"http://{ZERODHA_SERVER}/get_api_key_token").json()
api_key, access_token = credentials["api_key"], credentials["access_token"]


# first make the mapping of ticker --> token
token_map = requests.get(f"http://{ZERODHA_SERVER}/get/token_map").json()

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

# kiteticker
kws = KiteTicker(api_key=api_key, access_token=access_token)

# redis connection
rdb = redis.Redis(host=REDIS_SERVER)

# callbacks on websockets
def on_connect(ws, response):
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL, tokens)


def on_close(ws, code, reason):
    print(reason)
    ws.stop()


def on_ticks(ws, ticks):

    for tick in ticks:
        ticker = ticker_map[tick["instrument_token"]]
        rdb.set(ticker, json.dumps(tick, default=str))


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
