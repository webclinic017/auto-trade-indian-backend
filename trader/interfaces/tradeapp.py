import redis, json, threading, datetime, requests, os
from pymongo import MongoClient
import pandas as pd
from kiteconnect import KiteConnect
import talib as tb  # type: ignore
import numpy as np
import math
import websocket

from interfaces.constants import (
    LIMIT_ORDER_BUY,
    LIMIT_ORDER_SELL,
    MARKET_ORDER_BUY,
    MARKET_ORDER_SELL,
    MONGO,
    PUBLISHER,
    QUOTE,
    REDIS,
)


class TradeApp:
    def __init__(self, name):
        self.redis = redis.StrictRedis(host=REDIS, port=6379)
        self.mongo = MongoClient(host=MONGO, port=27017)
        self.name = name

        self.kite = KiteConnect(os.environ["API_KEY"], os.environ["ACCESS_TOKEN"])

        # generate the token map
        instruments = self.kite.instruments()
        self.token_map = {}
        for instrument in instruments:
            self.token_map[instrument["tradingsymbol"]] = instrument

        # create a collection for storing all the orders for that particular collection
        date = datetime.date.today()
        self.orders_db = self.mongo["orders_" + str(date)]
        self.orders_collection = self.orders_db[self.name + "_orders"]
        self.orders_collection_cache = self.orders_db[self.name]

        # this step is to clear all the database orders at the initialization step
        self.orders_collection_cache.delete_many({})

        # database for index
        self.data_db = self.mongo["intraday_" + str(date)]
        self.index_collection = self.data_db["index_master"]
        self.stock_collection = self.data_db["stock_master"]
        self.ticker_collection = self.mongo["analysis"]["workers"]
        self.data = json.loads(open("/app/data/tickers.json", "r").read())
        self.derivative_map = self.data["derivative_map"]

        self.stock_tickers = list(self.data["tickers"].keys())
        self.stock_option_tickers = list(self.derivative_map.keys())
        self.index_tickers = []

        for tick in self.data["index"]:
            self.index_tickers.append(self.data["index"][tick]["ce_ticker"])
            self.index_tickers.append(self.data["index"][tick]["pe_ticker"])

        self.tickers = self.data["tickers"]

    # publish the notification to the end users
    def sendNotification(self, trade):
        socket = websocket.create_connection(trade["uri"])

        trade.pop("uri")

        socket.send(json.dumps(trade))
        socket.close()

        return

    # get the live data for the particular ticker
    def getLiveData(self, ticker):
        # print(ticker)
        data = self.redis.get(ticker)
        # print(data)
        return json.loads(data)

    # get the quote for a ticker
    def getQuote(self, exchange, ticker):
        data = requests.post(
            QUOTE,
            json={"tickers": [f"{exchange}:{ticker}"]},
        ).json()
        print(data)
        return data[f"{exchange}:{ticker}"]

    # create a completed order
    def createOrder(self, order):
        order["timestamp"] = str(datetime.datetime.now())
        self.orders_collection.insert(order)

    # insert the order into the database
    def insertOrder(self, ticker, order):
        result = self.orders_collection_cache.update_one(
            {"ticker": ticker}, {"$push": {"data": order}}, True
        )
        return result

    # get the all orders
    def getAllOrders(self):
        orders = self.orders_collection_cache.find({})
        return list(orders)

    # delete the order document
    def deleteOrder(self, ticker):
        self.orders_collection_cache.delete_one({"ticker": ticker})

    # get one particular order
    def getOrder(self, ticker):
        order = self.orders_collection_cache.find_one({"ticker": ticker})
        return order

    # update the order by ticker
    def updateOrder(self, ticker, update):
        return self.orders_collection_cache.update_one({"ticker": ticker}, update, True)

    def getDataIndexTicker(self, ticker):
        data = self.index_collection.find_one({"ticker": ticker})
        data["_id"] = str(data["_id"])
        return data

    def getDataStockTicker(self, ticker):
        data = self.stock_collection.find_one({"ticker": ticker})
        data["_id"] = str(data["_id"])
        return data

    # function to get rsi and slope
    def getRSISlope(self, ticker):

        tdate = datetime.date.today()
        fdate = tdate - datetime.timedelta(4)

        df = self.getHistoricalData(ticker, fdate, tdate, "15minute")

        df["rsi"] = tb.RSI(df["close"], 14)
        df_slope = df.copy()
        df_slope = df_slope.iloc[-1 * 7 :, :]
        df_slope["slope"] = tb.LINEARREG_SLOPE(df["rsi"], 7)
        df_slope["slope_deg"] = df_slope["slope"].apply(math.atan).apply(np.rad2deg)

        last_rsi, last_deg = (
            df_slope.tail(1)["rsi"].values[0],
            df_slope.tail(1)["slope_deg"].values[0],
        )

        return last_rsi, last_deg

    # historical data
    def getHistoricalData(self, ticker, fdate, tdate, interval):
        ticker = ticker.split(":")[1]
        token = self.token_map[ticker]["instrument_token"]

        data = self.kite.historical_data(token, fdate, tdate, interval)
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        return df

    # market order buy for index option
    def generateMarketOrderBuyIndexOption(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        ticker = ticker.split(":")[1]
        trade = {
            "endpoint": MARKET_ORDER_BUY,
            "trading_symbol": ticker,
            "exchange": "NFO",
            "quantity": quantity,
            "tag": tag,
            "uri": PUBLISHER,
            "entry_price": live_data["last_price"],
            "price": live_data["depth"]["sell"][1]["price"],
            "type": "INDEXOPT",
        }
        return trade

    # market order sell for index option
    def generateMarketOrderSellIndexOption(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        ticker = ticker.split(":")[1]
        trade = {
            "endpoint": MARKET_ORDER_SELL,
            "trading_symbol": ticker,
            "exchange": "NFO",
            "quantity": quantity,
            "tag": tag,
            "uri": PUBLISHER,
            "entry_price": live_data["last_price"],
            "price": live_data["depth"]["buy"][1]["price"],
            "type": "INDEXOPT",
        }
        return trade

    # limit order buy for stock options
    def generateLimitOrderBuyStockOption(self, ticker, tag):
        live_data = self.getLiveData(ticker)
        ticker = ticker.split(":")[1]
        trade = {
            "endpoint": LIMIT_ORDER_BUY,
            "trading_symbol": ticker,
            "exchange": "NFO",
            "quantity": self.token_map[ticker]["lot_size"],
            "tag": tag,
            "price": live_data["depth"]["sell"][1]["price"],
            "uri": PUBLISHER,
            "ltp": live_data["last_price"],
            "entry_price": live_data["last_price"],
            "type": "STOCKOPT",
        }
        return trade

    # limit order sell for stock options
    def generateLimitOrderSellStockOption(self, ticker, tag):
        live_data = self.getLiveData(ticker)
        ticker = ticker.split(":")[1]
        trade = {
            "endpoint": LIMIT_ORDER_SELL,
            "trading_symbol": ticker,
            "exchange": "NFO",
            "quantity": self.token_map[ticker]["lot_size"],
            "tag": tag,
            "price": live_data["depth"]["buy"][1]["price"],
            "uri": PUBLISHER,
            "ltp": live_data["last_price"],
            "entry_price": live_data["last_price"],
            "type": "STOCKOPT",
        }
        return trade

    # limit order buy for stocks
    def generateLimitOrderBuyStock(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        ticker = ticker.split(":")[1]
        trade = {
            "endpoint": LIMIT_ORDER_BUY,
            "trading_symbol": ticker,
            "exchange": "NFO",
            "quantity": quantity,
            "tag": tag,
            "price": live_data["depth"]["sell"][1]["price"],
            "uri": PUBLISHER,
            "ltp": live_data["last_price"],
            "entry_price": live_data["last_price"],
            "type": "STOCK",
        }
        return trade

    # limit order sell for stocks
    def generateLimitOrderSellStock(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        ticker = ticker.split(":")[1]
        trade = {
            "endpoint": LIMIT_ORDER_SELL,
            "trading_symbol": ticker,
            "exchange": "NFO",
            "quantity": quantity,
            "tag": tag,
            "price": live_data["depth"]["buy"][1]["price"],
            "uri": PUBLISHER,
            "ltp": live_data["last_price"],
            "entry_price": live_data["last_price"],
            "type": "STOCK",
        }
        return trade

    # limit order buy for stock futures
    def generateLimitOrderBuyStockFuture(self, ticker, tag):
        live_data = self.getLiveData(ticker)
        ticker = ticker.split(":")[1]
        trade = {
            "endpoint": LIMIT_ORDER_BUY,
            "trading_symbol": ticker,
            "exchange": "NFO",
            "quantity": self.token_map[ticker]["lot_size"],
            "tag": tag,
            "price": live_data["depth"]["sell"][1]["price"],
            "uri": PUBLISHER,
            "ltp": live_data["last_price"],
            "entry_price": live_data["last_price"],
            "type": "STOCKFUT",
        }
        return trade

    # limit order sell for stock futures
    def generateLimitOrderSellStockFuture(self, ticker, tag):
        ticker = ticker.split(":")[1]
        live_data = self.getLiveData(ticker)
        trade = {
            "endpoint": LIMIT_ORDER_SELL,
            "trading_symbol": ticker,
            "exchange": "NFO",
            "quantity": self.token_map[ticker]["lot_size"],
            "tag": tag,
            "price": live_data["depth"]["buy"][1]["price"],
            "uri": PUBLISHER,
            "ltp": live_data["last_price"],
            "entry_price": live_data["last_price"],
            "type": "STOCKFUT",
        }
        return trade

    # function to send the trade
    def sendTrade(self, trade):
        self.sendNotification(trade)

        print(json.dumps(trade, indent=2, default=str))

        self.insertOrder(trade["exchange"] + ":" + trade["trading_symbol"], trade)
        self.createOrder(trade)

        return

    # function for average entry price
    def averageEntryprice(self, orders):
        total = 0
        count = 0

        for order in orders:
            total += order["entry_price"]
            count += 1

        return total / count

    # function ffor pnl
    def getPnl(self, entry_price, live_price):
        try:
            pnl = ((live_price - entry_price) / entry_price) * 100
        except:
            pnl = 0
        return pnl

    def price_diff(self, bidprice, offerprice):
        pricediff = (offerprice - bidprice) * 100 / 100
        return abs(pricediff)

    # method for the entry condition
    def entryStrategy(self):
        """override this method"""
        raise NotImplementedError

    # method for the exit condition
    def exitStrategy(self):
        """override this method"""
        raise NotImplementedError

    def start(self):
        # create the threads for the entry and exit
        print(f"starting threads {self.name}")
        entry_strategy = threading.Thread(target=self.entryStrategy)
        exit_startegy = threading.Thread(target=self.exitStrategy)
        # start the threads
        entry_strategy.start()
        exit_startegy.start()
        entry_strategy.join()
        exit_startegy.join()
