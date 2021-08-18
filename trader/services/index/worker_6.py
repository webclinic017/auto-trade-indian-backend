import datetime
from pymongo import MongoClient
from function_signals import send_trade
import os, requests

PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']
PUBLISHER_URI_INDEX_FUT = os.environ['PUBLISHER_URI_INDEX_FUT']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
MONGO_DB_URI = os.environ['MONGO_URI']

nf_quantity = int(os.environ['NF_QUANTITY'])
bf_quantity = int(os.environ['BF_QUANTITY'])

quantity = int(os.environ['W6_QUANTITY'])


today = str(datetime.date.today())
yesterday = str(datetime.date.today() - datetime.timedelta(days=1))

stock_market_end = datetime.time(15, 10, 0)

mongo = MongoClient(MONGO_DB_URI)
db = mongo['intraday_' + today]
collection = db['index_master']
db_ = mongo['intraday_' + yesterday]
collection_ = db_['index_master']

def main():
    while True:
        now = datetime.datetime.now().time()
        
        if now.hour == stock_market_end.hour and now.minute == stock_market_end.minute:
            tickers_list = collection.find({}, {"ticker":True})
            
            for ticker_ in tickers_list:
                ticker = ticker_['ticker']
                doc_today = collection.find_one({'ticker':ticker}, {'data':{'$slice':-1}})
                doc_yesterday = collection.find_one({'ticker':ticker}, {'data':{'$slice':-1}})
                
                if doc_yesterday == None and doc_today == None:
                    print('Needed two documents')
                    continue
                
                data = {"raw":{"data":[doc_yesterday, doc_today]}, "eod":True}
                # compare the results of two documents here
                latest_compare = requests.post(f'http://{ZERODHA_SERVER}/compare_results', json=data).json()
                # logic for auto trade goes here
                
                if (latest_compare['total_power'] > quantity):
                    
                    if latest_compare['symbol'] == 'BANKNIFTY':
                        print("i can buy" , latest_compare['weekly_Options_CE'])
                        trade = {
                            'endpoint': '/place/market_order/buy',
                            'trading_symbol': latest_compare['weekly_Options_CE'],
                            'exchange': 'NFO',
                            'quantity': bf_quantity,
                            'tag': 'ENTRY_INDEX',
                            'uri': PUBLISHER_URI_INDEX_OPT
                        }
                        send_trade(trade)
                        
                        print("i can buy" , latest_compare['futures'])
                        trade = {
                            'endpoint': '/place/market_order/buy',
                            'trading_symbol': latest_compare['futures'],
                            'exchange': 'NFO',
                            'quantity': bf_quantity,
                            'tag': 'ENTRY_INDEX',
                            'uri': PUBLISHER_URI_INDEX_FUT
                        }
                        send_trade(trade)
                        
                    elif latest_compare['symbol'] == 'NIFTY':
                        print("i can buy" , latest_compare['weekly_Options_CE'])
                        trade = {
                            'endpoint': '/place/market_order/buy',
                            'trading_symbol': latest_compare['weekly_Options_CE'],
                            'exchange': 'NFO',
                            'quantity': nf_quantity,
                            'tag': 'ENTRY_INDEX',
                            'uri': PUBLISHER_URI_INDEX_OPT
                        }
                        send_trade(trade)
                        
                        print("i can buy" , latest_compare['futures'])
                        trade = {
                            'endpoint': '/place/market_order/buy',
                            'trading_symbol': latest_compare['futures'],
                            'exchange': 'NFO',
                            'quantity': nf_quantity,
                            'tag': 'ENTRY_INDEX',
                            'uri': PUBLISHER_URI_INDEX_FUT
                        }
                        send_trade(trade)
                        
                elif (latest_compare['total_power'] < -quantity):
                    
                    if latest_compare['symbol'] == 'BANKNIFTY':
                        print("i can buy" , latest_compare['weekly_Options_PE'])
                        trade = {
                            'endpoint': '/place/market_order/buy',
                            'trading_symbol': latest_compare['weekly_Options_PE'],
                            'exchange': 'NFO',
                            'quantity': bf_quantity,
                            'tag': 'ENTRY_INDEX',
                            'uri': PUBLISHER_URI_INDEX_OPT
                        }
                        send_trade(trade)
                        
                        print("i can sell" , latest_compare['futures'])
                        trade = {
                            'endpoint': '/place/market_order/sell',
                            'trading_symbol': latest_compare['futures'],
                            'exchange': 'NFO',
                            'quantity': bf_quantity,
                            'tag': 'ENTRY_INDEX',
                            'uri': PUBLISHER_URI_INDEX_FUT
                        }
                        send_trade(trade)
                        
                    elif latest_compare['symbol'] == 'NIFTY':
                        print("i can buy" , latest_compare['weekly_Options_PE'])
                        trade = {
                            'endpoint': '/place/market_order/buy',
                            'trading_symbol': latest_compare['weekly_Options_PE'],
                            'exchange': 'NFO',
                            'quantity': nf_quantity,
                            'tag': 'ENTRY_INDEX',
                            'uri': PUBLISHER_URI_INDEX_OPT
                        }
                        send_trade(trade)
                        
                        print("i can sell" , latest_compare['futures'])
                        trade = {
                            'endpoint': '/place/market_order/sell',
                            'trading_symbol': latest_compare['futures'],
                            'exchange': 'NFO',
                            'quantity': nf_quantity,
                            'tag': 'ENTRY_INDEX',
                            'uri': PUBLISHER_URI_INDEX_FUT
                        }
                        send_trade(trade)        
            break
                
        continue
