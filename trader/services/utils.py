import redis, os, json

REDIS_SERVER = os.environ['REDIS_HOST']

r_ticker = redis.StrictRedis(host=REDIS_SERVER, port=6379, decode_responses=True)

class RedisOrderDictonary:
    def __init__(self):
        # initialize the redis object
        self.r = redis.StrictRedis(host=REDIS_SERVER, port=6379, decode_responses=True)
        orders = self.r.get('orders')
        
        if orders == None:
            # initialize the orders with empty dictonary
            self.r.set('orders', json.dumps({}))
    
    # method to insert the data into the redis database
    def insert(self, key, data):
        # get the orders
        orders = json.loads(self.r.get('orders'))
        
        # insert the order into the database
        if key in orders:
            orders[key].append(data)
        else:
            orders[key] = [data]
        
        # insert the values into the database again
        self.r.set('orders', json.dumps(orders))
    
    # method to clear the orders of a ticker
    def clear(self, key):
        orders = json.loads(self.r.get('orders'))
        # delete the key from the dictonary
        del orders[key]
        # set the orders
        self.r.set('orders', json.dumps(orders))
    
    # get orders for a particular ticker
    def get(self, key):
        orders = json.loads(self.r.get('orders'))
        return orders[key]
    
    # get all orders
    def get_all(self):
        orders = json.loads(self.r.get('orders'))
        return orders

class RedisWorker5Dict:
    def __init__(self):
        self.r = redis.StrictRedis(host=REDIS_SERVER, port=6379, decode_responses=True)
        
        ticker_pairs = self.r.get('ticker_pairs')
        
        # if the value dosent exist in the database initialize it with empty list
        if ticker_pairs == None:
            self.r.set('ticker_pairs', '[]')
    
    # insert the new pair into the database 
    def insert(self, ticker_pair):
        tickers = set(json.loads(self.r.get('ticker_pairs')))
        tickers.add(ticker_pair)
        self.r.set('ticker_pairs', json.dumps(list(tickers)))
    
    # remove the pair from the database
    def remove(self, ticker_pair):
        tickers = json.loads(self.r.get('ticker_pairs'))
        
        # try to remove the element from the pairs if exists
        try:
            tickers.remove(ticker_pair)
        except:
            pass
        
        # set the tickers back
        self.r.set(json.dumps(tickers))
    
    # get all pairs from the db
    def get_all(self):
        pairs = json.loads(self.r.get('ticker_pairs'))
        return pairs


def calculate_pnl_order(orders, ticker):
    
    if ticker not in orders:
        return None, None, 0, 0, False
    
    if len(orders[ticker]) > 0:
        total_trade_buy_quantity = 0
        total_trade_buy_price = 0
        
        total_trade_sell_quantity = 0
        total_trade_sell_price = 0
        
        
        count_buy = 0
        count_sell = 0
        
        for order in orders[ticker]:
            
            if order['transaction_type'] == 'BUY':
                total_trade_buy_quantity += order['filled_quantity']
                total_trade_buy_price += order['average_price']*order['filled_quantity']
                count_buy += 1
                
            if order['transaction_type'] == 'SELL':
                total_trade_sell_quantity += order['filled_quantity']
                total_trade_sell_price += order['average_price']*order['filled_quantity']
                count_sell += 1
            
        
        
        exchange = order['exchange']
        
        try:
            ltp = json.loads(r_ticker.get(order['instrument_token']))
        except:
            return {}
        
        print(ltp)
        ltp = ltp['last_price']
        
        try:
            total_current_buy_price=total_trade_buy_quantity*ltp
            profit_percentage_buy=(100*(total_current_buy_price-total_trade_buy_price))/float(total_trade_buy_price)
        except:
            profit_percentage_buy = 0
            
        
        try:
            total_current_sell_price=total_trade_sell_quantity*ltp
            profit_percentage_sell=(100*(total_current_sell_price-total_trade_sell_price))/float(total_trade_sell_price)
        except:
            profit_percentage_sell = 0

        profit = {
            
                'buy':profit_percentage_buy,
                'sell':profit_percentage_sell
        }
    
        return profit, exchange, total_trade_buy_quantity, total_trade_sell_quantity, True