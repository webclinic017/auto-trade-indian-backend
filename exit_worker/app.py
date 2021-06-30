from flask.app import Flask
import pika, os, json, requests, time, threading, redis
from websocket import WebSocketApp


class RedisDictonary:
    def __init__(self):
        self.r = redis.StrictRedis(host='redis_server', port=6379, decode_responses=True)
        orders = self.r.get('orders')
        if orders == None:
            self.r.set('orders', json.dumps({}))
    
    def insert(self, key, data):
        orders = json.loads(self.r.get('orders'))
        
        if key in orders:
            orders[key].append(data)
        else:
            orders[key] = [data]
        self.r.set('orders', json.dumps(orders))
    
    
    def clear(self, key):
        orders = json.loads(self.r.get('orders'))
        del orders[key]
        self.r.set('orders', json.dumps(orders))
        
    
    def get(self, key):
        orders = json.loads(self.r.get('orders'))
        return orders[key]

    def get_all(self):
        orders = json.loads(self.r.get('orders'))
        return orders
    
    def get_tickers(self):
        orders = self.get_all()
        
        if orders == {}:
            return []
        
        tickers = []
        list(map(lambda x : f'NFO:{x}', orders.keys()))
        
        for order in orders:
            order_ = orders[order][0]
            tickers.append(order_['exchange'] + ":" + order_["tradingsymbol"])
        
        return tickers


def send_trade(trade):
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbit_mq'))
    channel = connection.channel()
    channel.queue_declare(queue='zerodha_worker')
    
    # publish trade to zerodha worker queue
    channel.basic_publish(
        exchange='',
        routing_key='zerodha_worker',
        body=json.dumps(trade).encode()
    )
    connection.close()


TOKEN_SERVER = os.environ['WS_HOST']
ORDERS_URI = f'ws://{TOKEN_SERVER}/ws/orders'


def on_message(ws, message):
    
    order = json.loads(message)
    
    if order['status'] == 'COMPLETE' and order['tag'] == 'ENTRY':
        RedisDictonary().insert(order['tradingsymbol'], order)
        print(RedisDictonary().get_all())
    


def on_open(ws):
    print('CONNECTION OPEN')

def exit_process():
        
    profit = {
        
    }
    
    while True:
        orders = RedisDictonary().get_all()
        tickers = RedisDictonary().get_tickers()
        ltp_dict = requests.post('http://zerodha_worker/get/ltp', json={'tickers': tickers}).json()['ltp']
        print(ltp_dict)
        
        for ticker in orders:
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
                ltp = ltp_dict[f'{exchange}:{ticker}']['last_price']
                
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

                profit[ticker] = {
                    
                        'buy':profit_percentage_buy,
                        'sell':profit_percentage_sell
                }
                
                print(profit)

                if profit[ticker]['buy'] != 0:
                    if profit[ticker]['buy'] > 4:
                        print(f'Exit {ticker} by SELLING it')
                        if exchange == 'NFO':
                            trade = {
                                'endpoint': '/place/market_order/sell',
                                'trading_symbol': ticker,
                                'exchange': exchange,
                                'quantity': total_trade_buy_quantity,
                                'tag': 'ENTRY'
                            }
                            
                            RedisDictonary().clear(ticker)
                            send_trade(trade)
                
                if profit[ticker]['sell'] != 0:
                    if profit[ticker]['sell'] > 4:
                        print(f'Exit {ticker} by BUYING it')
                        if exchange == 'NFO':
                            trade = {
                                'endpoint': '/place/market_order/buy',
                                'trading_symbol': ticker,
                                'exchange': exchange,
                                'quantity': total_trade_sell_quantity,
                                'tag': 'ENTRY'
                            }
                            
                            RedisDictonary().clear(ticker)
                            send_trade(trade)
        
        # sleep for 10 seconds
        time.sleep(10)


ws = WebSocketApp(ORDERS_URI, on_message=on_message, on_open=on_open)
app = Flask(__name__)

@app.route('/')
def index():
    return ""


t_socket = threading.Thread(target=ws.run_forever)
t_socket.start()

time.sleep(5)
t = threading.Thread(target=app.run, args=['0.0.0.0', 80])
t.start()

t_exit = threading.Thread(target=exit_process)
t_exit.start()



