import json, threading, os, requests, redis
import time
from flask import Flask

ZERODHA_SERVER = os.environ["ZERODHA_WORKER_HOST"]
REDIS_SERVER = os.environ["REDIS_HOST"]

r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379)

app = Flask(__name__)

# root url
@app.route("/")
def home():
    return "", 200


def get_liveData(tickers):
    while True:
        live_data = requests.post(
            f"http://{ZERODHA_SERVER}/get/quote", json={"tickers": tickers}
        ).json()

        for ticker in live_data:
            tick = ticker
            r_ticker.set(tick, json.dumps(live_data[ticker], default=str))

        time.sleep(1)


def main():
    data = json.loads(open("/app/data/tickers.json", "r").read())

    stocks = list(data["tickers"].keys())

    stocks_options = []
    for stock in data["tickers"]:
        stocks_options.append(data["tickers"][stock]["ce_ticker"])
        stocks_options.append(data["tickers"][stock]["pe_ticker"])

    index_options = []
    for stock in data["index"]:
        index_options.append(data["index"][stock]["ce_ticker"])
        index_options.append(data["index"][stock]["pe_ticker"])

    index = list(data["index"].keys())

    tickers = stocks_options + index_options + stocks + index

    t = threading.Thread(target=get_liveData, args=[tickers])
    t.setDaemon(True)
    t.start()

    t = threading.Thread(target=app.run, args=["0.0.0.0", 8888])
    t.start()
