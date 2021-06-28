import pika, os, json, requests, time, threading
from websocket import WebSocketApp
from collections import defaultdict

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


TOKEN_SERVER = os.environ['TOKEN_SERVER']
ORDERS_URI = f'ws://{TOKEN_SERVER}/ws/orders'

orders = defaultdict(list)
tickers = set()

def stocket_process():
    
    def on_message(ws, message):
        order = json.loads(message)
        orders[order['tradingsymbol']].append(order)
        tickers.add(f"{order['exchange']}:{order['tradingsymbol']}")
    
    
    ws = WebSocketApp(ORDERS_URI, on_message=on_message)
    ws.run_forever()


def exit_process():
    
    profit = {
        
    }
    
    while True:
        ltp_dict = requests.post('http://zerodha_worker/get/ltp', json={'tickers':list(tickers)}).json()['ltp']
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

                if profit[ticker]['buy'] != 0:
                    if profit[ticker]['buy'] > 4:
                        print(f'Exit {ticker} by SELLING it')
                        if exchange == 'NFO':
                            trade = {
                                'endpoint': '/place/market_order/sell',
                                'trading_symbol': ticker,
                                'exchange': exchange,
                                'quantity': total_trade_buy_quantity
                            }
                            
                            orders[ticker] = []
                            send_trade(trade)
                
                if profit[ticker]['sell'] != 0:
                    if profit[ticker]['buy'] > 4:
                        print(f'Exit {ticker} by BUYING it')
                        if exchange == 'NFO':
                            trade = {
                                'endpoint': '/place/market_order/buy',
                                'trading_symbol': ticker,
                                'exchange': exchange,
                                'quantity': total_trade_sell_quantity
                            }
                            
                            orders[ticker] = []
                            send_trade(trade)
        
        # sleep for 10 seconds
        time.sleep(10)


if __name__:
    t_socket = threading.Thread(target=stocket_process)
    t_exit = threading.Thread(target=exit_process)

    t_socket.start()
    t_exit.start()
