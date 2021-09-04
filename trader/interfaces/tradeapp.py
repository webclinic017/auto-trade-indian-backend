import redis, json, threading, datetime, requests, os
from pymongo import MongoClient

ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']

class TradeApp:
    
    def __init__(self, name):
        self.redis = redis.StrictRedis(host='redis_server_index', port=6379)
        self.mongo = MongoClient(host='db', port=27017)
        self.name = name
        
        # create a collection for storing all the orders for that particular collection
        date = datetime.date.today()
        self.orders_db = self.mongo['orders' + str(date)]
        self.orders_collection = self.orders_db[self.name]
        
        # database for index
        self.data_db = self.mongo['intraday_' + str(date)]
        self.index_collection = self.data_db['index_master']
        
    # get the live data for the particular ticker
    def getLiveData(self, ticker):
        data = self.redis.get(ticker)
        return json.loads(data)
    
    # insert the order into the database
    def insertOrder(self, order):
        result = self.orders_collection.insert_one(order)
        return result.inserted_id
    
    # get the all orders
    def getAllOrders(self):
        orders = self.orders_collection.find({})
        return orders
    
    # get one particular order
    def getOrder(self, ticker):
        order = self.orders_collection.find_one({'ticker':ticker})
        return order
    
    # update the order by ticker
    def updateOrder(self, ticker, update):
        return self.orders_collection.update_one({'ticker':ticker}, update, True)
    
    
    def getDataIndexTicker(self, ticker):
        data = self.index_collection.find_one({'ticker':ticker})
        data['_id'] = str(data['_id'])
        return data
    
    # function to get rsi and slope
    def getRSISlope(self, ticker):
        data = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{ticker}/7').json()
        return data['last_rsi'], data['last_slope']
    
    # generate the trade dictonary for index options buy
    def generateIndexOptionBuyTrade(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/market_order/buy',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': quantity,
            'tag': tag,
            'uri': PUBLISHER_URI_INDEX_OPT,
            'ltp': live_data[ticker]
        }
        return trade

    # generate the trade dictonary for index option sell
    def generateIndexOptionSellTrade(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/market_order/sell',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': quantity,
            'tag': tag,
            'uri': PUBLISHER_URI_INDEX_OPT,
            'ltp': live_data[ticker]
        }
        return trade
    
    # function to send the trade
    def sendTrade(self, trade):
        if datetime.datetime.now().time() >= datetime.time(18, 00):
            print('\ncant enter now\n')
            return False, {}
        
        response = requests.post(f'http://{ZERODHA_SERVER}' + trade['endpoint'], json=trade)
        status, data = response.ok, response.json()        
        return status, data
    
    
    # method for the entry condition
    def entryStrategy(self):
        '''override this method'''
        pass
    
    # method for the exit condition
    def exitStrategy(self):
        '''override this method'''
        pass
    
    def start(self):
        # create the threads for the entry and exit
        entry_strategy = threading.Thread(target=self.entryStrategy); exit_startegy = threading.Thread(target=self.exitStrategy)
        # start the threads
        entry_strategy.start(); exit_startegy.start()