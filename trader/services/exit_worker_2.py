from .utils import RedisOrderDictonary, RedisWorker5Dict, calculate_pnl_order
import time, threading, datetime, os
from .function_signals import send_trade

PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']
PUBLISHER_URI_INDEX_FUT = os.environ['PUBLISHER_URI_INDEX_FUT']

def exit_process():
    profit = {
        
    }
    
    # run the exit process loop
    while True:
        orders = RedisOrderDictonary().get_all()
        ticker_pairs = RedisWorker5Dict().get_all()
        
        for ticker_pair in ticker_pairs:
            ticker_a, ticker_b = ticker_pair.split("-")

            # calculate pnl for ticker a and ticker b
            pnl_a, exchange_a = calculate_pnl_order(orders, ticker_a)
            pnl_b, exchange_b = calculate_pnl_order(orders, ticker_b)
            
            if ticker_a == {} or ticker_b == {} or exchange_a != exchange_b:
                continue
            
            profit[f'{ticker_a}-{ticker_b}'] = {
                'buy': pnl_a['buy'] + pnl_b['buy'],
                'sell': pnl_a['sell'] + pnl_b['sell']
            }
            
            ticker = f'{ticker_a}-{ticker_b}'
            exchange = exchange_a
            
            if 'FUT' in ticker:
                uri = PUBLISHER_URI_INDEX_FUT
            else:
                uri = PUBLISHER_URI_INDEX_OPT

            
            if profit[ticker]['buy'] != 0:
                if profit[ticker]['buy'] > 4 or datetime.datetime.now().time() >= datetime.time(15, 25):
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
                if profit[ticker]['sell'] > 4 or datetime.datetime.now().date() >= datetime.time(15, 25):
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
        
        # sleep for 10 seconds
        time.sleep(10)


def main():
    t_exit = threading.Thread(target=exit_process)
    t_exit.start()