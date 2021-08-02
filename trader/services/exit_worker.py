import os, json, time, threading, redis, requests, datetime
from .function_signals import send_trade
from .utils import RedisOrderDictonary, calculate_pnl_order

os.environ['TZ'] = 'Asia/Kolkata'
time.tzset()

r_ticker = redis.StrictRedis(host='redis_server_index', port=6379, decode_responses=True)

PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']
PUBLISHER_URI_INDEX_FUT = os.environ['PUBLISHER_URI_INDEX_FUT']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
REDIS_SERVER = os.environ['REDIS_HOST']
EXIT_SERVER = os.environ['EXIT_HOST']
ZERODHA_CONSUMER = os.environ['ZERODHA_CONSUMER']


def exit_process(): 
    profit = {
        
    }
    while True:
        orders = RedisOrderDictonary().get_all()
        
        for ticker in orders:
            pnl, exchange, total_trade_buy_quantity, total_trade_sell_quantity, status = calculate_pnl_order(orders, ticker)

            if pnl == {} or not status:
                continue
            
            profit[ticker] = pnl
            
            print(profit)

            if 'FUT' in ticker:
                uri = PUBLISHER_URI_INDEX_FUT
            else:
                uri = PUBLISHER_URI_INDEX_OPT

            try:
                rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{ticker}/7').json()['last_rsi']
                print(rsi)
            except:
                rsi = 999

            if profit[ticker]['buy'] != 0:
                if profit[ticker]['buy'] > 4 or rsi < 30 or datetime.datetime.now().time() >= datetime.time(15, 25):
                    print(f'Exit {ticker} by SELLING it')
                    if exchange == 'NFO':
                        
                        if total_trade_buy_quantity >= 4500:
                            total_trade_buy_quantity = 4500
                        
                        trade = {
                            'endpoint': '/place/market_order/sell',
                            'trading_symbol': ticker,
                            'exchange': exchange,
                            'quantity': total_trade_buy_quantity,
                            'tag': 'EXIT',
                            'uri': uri
                        }
                        
                        orders_list = RedisOrderDictonary().get(ticker)
                        trades_to_exit = []
                        trades_to_keep = []
                        total_quantity = 0

                        for order in orders_list:
                            total_quantity += order['filled_quantity']
                            
                            if total_quantity <= 4500:
                                trades_to_exit.append(order)
                            else:
                                trades_to_keep.append(order)
                        
                        
                        RedisOrderDictonary().clear(ticker)
                        RedisOrderDictonary().set(ticker, trades_to_keep)
                        send_trade(trade)
            
            if profit[ticker]['sell'] != 0:
                if profit[ticker]['sell'] > 4 or rsi < 30 or datetime.datetime.now().date() >= datetime.time(15, 25):
                    print(f'Exit {ticker} by BUYING it')
                    if exchange == 'NFO':
                        
                        if total_trade_sell_quantity >= 4500:
                            total_trade_sell_quantity = 4500
                        
                        trade = {
                            'endpoint': '/place/market_order/buy',
                            'trading_symbol': ticker,
                            'exchange': exchange,
                            'quantity': total_trade_sell_quantity,
                            'tag': 'EXIT',
                            'uri': uri
                        }
                        orders_list = RedisOrderDictonary().get(ticker)
                        trades_to_exit = []
                        trades_to_keep = []
                        total_quantity = 0

                        for order in orders_list:
                            total_quantity += order['filled_quantity']
                            
                            if total_quantity <= 4500:
                                trades_to_exit.append(order)
                            else:
                                trades_to_keep.append(order)
                        
                        
                        RedisOrderDictonary().clear(ticker)
                        RedisOrderDictonary().set(ticker, trades_to_keep)
                        send_trade(trade)
                
                # rsi = requests.get(f'http://zerodha_worker_index/get/rsi/{ticker}/7').json()
                # print(rsi)
                
        # sleep for 10 seconds
        time.sleep(10)

def main():
    t_exit = threading.Thread(target=exit_process)
    t_exit.start()