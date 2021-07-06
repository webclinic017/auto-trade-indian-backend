from flask.app import Flask
import pika, os, json, time, threading, redis, requests
from websocket import WebSocketApp

r_ticker = redis.StrictRedis(host='redis_server_index', port=6379, decode_responses=True)

PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']
PUBLISHER_URI_INDEX_FUT = os.environ['PUBLISHER_URI_INDEX_FUT']

class RedisDictonary:
    def __init__(self):
        self.r = redis.StrictRedis(host='redis_server_index', port=6379, decode_responses=True)
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
    pika.ConnectionParameters(host='rabbit_mq_index'))
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
tickers_streamed = {}



def on_message(ws, message):
    
    order = json.loads(message)
    
    if order['status'] == 'COMPLETE' and order['tag'] == 'ENTRY_INDEX':
        
        if order['tradingsymbol'] not in tickers_streamed:
            token = order['instrument_token']
            t = threading.Thread(target=requests.get, args=[f'http://exit_worker_index/stream_ticker/{token}'])
            t.start()
            tickers_streamed[token] = True
            
        RedisDictonary().insert(order['tradingsymbol'], order)
        print(RedisDictonary().get_all())
    
        

def on_open(ws):
    print('CONNECTION OPEN')

def exit_process():
        
    profit = {
        
    }
    
    while True:
        orders = RedisDictonary().get_all()
        # tickers = RedisDictonary().get_tickers()
        # ltp_dict = requests.post('http://zerodha_worker/get/ltp', json={'tickers': tickers}).json()['ltp']
        # ltp_dict = r_ticker.get('')
        # print(ltp_dict)
        
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
                # ltp = ltp_dict[f'{exchange}:{ticker}']['last_price']
                try:
                    ltp = json.loads(r_ticker.get(order['instrument_token']))
                except:
                    continue
                
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

                profit[ticker] = {
                    
                        'buy':profit_percentage_buy,
                        'sell':profit_percentage_sell
                }
                
                print(profit)

                if 'FUT' in ticker:
                    uri = PUBLISHER_URI_INDEX_FUT
                else:
                    uri = PUBLISHER_URI_INDEX_OPT


                if profit[ticker]['buy'] != 0:
                    if profit[ticker]['buy'] > 4:
                        print(f'Exit {ticker} by SELLING it')
                        if exchange == 'NFO':

                            
                            trade = {
                                'endpoint': '/place/market_order/sell',
                                'trading_symbol': ticker,
                                'exchange': exchange,
                                'quantity': total_trade_buy_quantity,
                                'tag': 'EXIT',
                                'uri': uri
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
                                'tag': 'EXIT',
                                'uri': uri
                            }
                            
                            RedisDictonary().clear(ticker)
                            send_trade(trade)
                
                rsi = requests.get(f'http://zerodha_worker_index/get/rsi/{ticker}/7').json()
                print(rsi)
        
        # sleep for 10 seconds
        time.sleep(10)


ws = WebSocketApp(ORDERS_URI, on_message=on_message, on_open=on_open)
app = Flask(__name__)

def on_message_ticker(ws, message):
    # t = threading.Thread(target=r_ticker.set, args=[ticker, json.dumps(message)])
    # r_ticker.set(ticker, json.dumps(message))
    data = json.loads(message)
    r_ticker.set(data['instrument_token'], message)

@app.route('/stream_ticker/<token>')
def index(token):
    ws = WebSocketApp(f'ws://{TOKEN_SERVER}/ws/ticker/{token}', on_message=on_message_ticker)
    t = threading.Thread(target=ws.run_forever)
    t.start()
    requests.get(f'http://zerodha_consumer_1/subscribe/{token}')
    return ""


t_socket = threading.Thread(target=ws.run_forever)
t_socket.start()

time.sleep(5)
t = threading.Thread(target=app.run, args=['0.0.0.0', 80])
t.start()

t_exit = threading.Thread(target=exit_process)
t_exit.start()



