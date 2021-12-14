import os

PUBLISHER = os.environ["PUBLISHER_URI"]
MONGO = os.environ["MONGO_URI"]
RABBIT_MQ = os.environ["RABBIT_MQ_HOST"]
REDIS = os.environ["REDIS_HOST"]
LIVE_DATA = "http://" + os.environ["LIVE_DATA_SERVER"] + "/"
ZERODHA = "http://" + os.environ["ZERODHA_WORKER_HOST"]
TOKEN_MAP = ZERODHA + "/get/token_map"
QUOTE = ZERODHA + "/get/quote"
HISTORICAL_DATA = ZERODHA + "/get/historical_data"


def RSI(ticker, n):
    return ZERODHA + f"/get/rsi/{ticker}/{n}"


MARKET_ORDER_BUY = "/place/market_order/buy"
MARKET_ORDER_SELL = "/place/market_order/sell"
LIMIT_ORDER_BUY = "/place/limit_order/buy"
LIMIT_ORDER_SELL = "/place/limit_order/sell"


def getOrderUrl(path):
    return "https://auto.bittrade.space" + path


AUTH_TOKEN = os.environ["AUTH_TOKEN"]

MODE = os.environ["MODE"]
