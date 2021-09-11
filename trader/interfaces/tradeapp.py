import redis, json, threading, datetime, requests, os
from pymongo import MongoClient
import pandas as pd

ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']
PUBLISHER_URI_STOCK_OPT = os.environ['PUBLISHER_URI_STOCK_OPT']
PUBLISHER_URI_STOCKS = os.environ['PUBLISHER_URI_STOCKS']
PUBLISHER_URI_STOCK_FUT = os.environ['PUBLISHER_URI_STOCK_FUT']


class TradeApp:
    
    def __init__(self, name):
        self.redis = redis.StrictRedis(host='redis_server_index', port=6379)
        self.mongo = MongoClient(host='db', port=27017)
        self.name = name
        self.token_map = requests.get(f'http://{ZERODHA_SERVER}/get/token_map').json()
        # create a collection for storing all the orders for that particular collection
        date = datetime.date.today()
        self.orders_db = self.mongo['orders_' + str(date)]
        self.orders_collection = self.orders_db[self.name]
        
        # this step is to clear all the database orders at the initialization step
        self.orders_collection.delete_many({})
        
        # database for index
        self.data_db = self.mongo['intraday_' + str(date)]
        self.index_collection  = self.data_db['index_master']
        self.stock_collection  = self.data_db['stock_master']        
        self.ticker_collection = self.mongo['analysis']
        self.derivative_map = open('/app/data/tickers.json', 'r').read()['deriatives']
        
    
    # get the live data for the particular ticker
    def getLiveData(self, ticker_der):
        ticker = self.derivative_map[ticker_der]
        data = self.redis.get(self.token_map[ticker]['instrument_token'])
        return json.loads(data)
    
    # get the tickers for the particular worker
    def getTickers(self):
        try:
            data = self.ticker_collection.find({'worker':self.name})['data']
        except:
            data = []
            
        return set(data)
    
    # insert the order into the database
    def insertOrder(self, ticker, order):
        result = self.orders_collection.update_one({'ticker':ticker}, {'$push': {'data':order}}, True)
        return result
    
    # get the all orders
    def getAllOrders(self):
        orders = self.orders_collection.find({})
        return list(orders)
    
    # delete the order document
    def deleteOrder(self, ticker):
        self.orders_collection.delete_one({'ticker':ticker})
    
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
    
    def getDataStockTicker(self, ticker):
        data = self.stock_collection.find_one({'ticker':ticker})
        data['_id'] = str(data['_id'])
        return data
    
    # function to get rsi and slope
    def getRSISlope(self, ticker):
        data = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{ticker}/7').json()
        return data['last_rsi'], data['last_slope']
    
    # historical data
    def getHistoricalData(self, ticker, fdate, tdate, interval):
        token = self.token_map[ticker]['instrument_token']
        data = requests.post(f'http://{ZERODHA_SERVER}/get/historical_data', json={
            'fdate': str(fdate),
            'tdate': str(tdate),
            'token': token,
            'interval': interval
        }).json()

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df

    # market order buy for index option
    def generateMarketOrderBuyIndexOption(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/market_order/buy',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': quantity,
            'tag': tag,
            'uri': PUBLISHER_URI_INDEX_OPT,
            'entry_price': live_data['last_price']
        }
        return trade

    # market order sell for index option
    def generateMarketOrderSellIndexOption(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/market_order/sell',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': quantity,
            'tag': tag,
            'uri': PUBLISHER_URI_INDEX_OPT,
            'entry_price': live_data['last_price']
        }
        return trade

    
    # limit order buy for stock options
    def generateLimitOrderBuyStockOption(self, ticker, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/limit_order/buy',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': self.token_map[ticker]['lot_size'],
            'tag': tag,
            'price': live_data['depth']['sell'][1]['price'],
            'uri': PUBLISHER_URI_STOCK_OPT,
            'ltp': live_data['last_price'],
            'entry_price': live_data['last_price']
        }
        return trade
    
    # limit order sell for stock options
    def generateLimitOrderSellStockOption(self, ticker, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/limit_order/sell',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': self.token_map[ticker]['lot_size'],
            'tag': tag,
            'price': live_data['depth']['sell'][1]['price'],
            'uri': PUBLISHER_URI_STOCK_OPT,
            'ltp': live_data['last_price'],
            'entry_price': live_data['last_price']
        }
        return trade
        
    # limit order buy for stocks
    def generateLimitOrderBuyStock(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/limit_order/buy',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': quantity,
            'tag': tag,
            'price': live_data['depth']['sell'][1]['price'],
            'uri': PUBLISHER_URI_STOCKS,
            'ltp': live_data['last_price'],
            'entry_price': live_data['last_price']
        }
        return trade
    
    # limit order sell for stocks
    def generateLimitOrderSellStock(self, ticker, quantity, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/limit_order/sell',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': quantity,
            'tag': tag,
            'price': live_data['depth']['sell'][1]['price'],
            'uri': PUBLISHER_URI_STOCKS,
            'ltp': live_data['last_price'],
            'entry_price': live_data['last_price']
        }
        return trade
    
    # limit order buy for stock futures
    def generateLimitOrderBuyStockFuture(self, ticker, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/limit_order/buy',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': self.token_map[ticker]['lot_size'],
            'tag': tag,
            'price': live_data['depth']['sell'][1]['price'],
            'uri': PUBLISHER_URI_STOCK_FUT,
            'ltp': live_data['last_price'],
            'entry_price': live_data['last_price']
        }
        return trade
    
    # limit order sell for stock futures
    def generateLimitOrderSellStockFuture(self, ticker, tag):
        live_data = self.getLiveData(ticker)
        trade = {
            'endpoint': '/place/limit_order/sell',
            'trading_symbol': ticker,
            'exchange': 'NFO',
            'quantity': self.token_map[ticker]['lot_size'],
            'tag': tag,
            'price': live_data['depth']['sell'][1]['price'],
            'uri': PUBLISHER_URI_STOCK_FUT,
            'ltp': live_data['last_price'],
            'entry_price': live_data['last_price']
        }
        return trade

    # function to send the trade
    def sendTrade(self, trade):
        if datetime.datetime.now().time() >= datetime.time(18, 00):
            print('\ncant enter now\n')
            return False, {}
        
        response = requests.post(f'http://{ZERODHA_SERVER}' + trade['endpoint'], json=trade)
        status, data = response.ok, response.json()        
        
        if status:
            self.insertOrder(trade['trading_symbol'], trade)
        
        return status, data
    

    # function for average entry price
    def averageEntryprice(self, orders):
        total = 0
        count = 0

        for order in orders:
            total += order['entry_price']
            count += 1

        return total/count
    
    # function ffor pnl
    def getPnl(self, entry_price,live_price):
        pnl=((live_price-entry_price)/entry_price)*100
        return pnl


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
        print(f'starting threads {self.name}')
        entry_strategy = threading.Thread(target=self.entryStrategy); exit_startegy = threading.Thread(target=self.exitStrategy)
        # start the threads
        entry_strategy.start(); exit_startegy.start()
        entry_strategy.join(); exit_startegy.join()