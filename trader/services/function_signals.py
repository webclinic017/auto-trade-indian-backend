import datetime, redis, requests, os, json
import logging
from time import sleep
from .utils import RedisWorker5Dict

PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']
PUBLISHER_URI_STOCKS = os.environ['PUBLISHER_URI_STOCKS']
PUBLISHER_URI_STOCK_OPT = os.environ['PUBLISHER_URI_STOCK_OPT']
PUBLISHER_URI_STOCK_FUT = os.environ['PUBLISHER_URI_STOCK_FUT']


ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
REDIS_SERVER = os.environ['REDIS_HOST']
RABBIT_MQ_SERVER = os.environ['RABBIT_MQ_HOST']

TEST_MODE = False

def send_trade(trade):
    if 'ENTRY' in trade['tag']:
        if TEST_MODE:
            if datetime.datetime.now().time() >= datetime.time(21, 00):
                print('\ncant enter now\n')
                return False, {}
        else:
            if datetime.datetime.now().time() >= datetime.time(18, 00):
                print('\ncant enter now\n')
                return False, {}

    response = requests.post(f'http://{ZERODHA_SERVER}' + trade['endpoint'], json=trade)
    status, data = response.ok, response.json()
    
    if not status:
        print(data)
    
    return status, data

def scalp_buy(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(9,53)
     # PE CE 
            # NIFTYCE400
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            data = json.loads(message['data'])
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']
            ltp = data['ltp']['ltp']

            if 'BANKNIFTY' in symbol:
                doc = data['banknifty']['data'].pop()
            else:
                doc = data['nifty']['data'].pop()

            print("-"*10 + " ENTRY CONDITIONS " + "-"*10)
            log = {
                'rsi': last_rsi,
                'slope': last_slope,
                'ticker': symbol,
                'ltp': ltp[f'NFO:{symbol}']['last_price'],
                'cheaper_option': doc['cheaper_option']
            }
            print(json.dumps(log, indent=3))
            print("-"*(10+17+10))            

            print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x and doc is not None:
                if last_rsi > 40 and last_slope > 0: #and (doc['cheaper_option'] in symbol):
                    trade = {
                        'endpoint': '/place/market_order/buy',
                        'trading_symbol': symbol,
                        'exchange': 'NFO',
                        'quantity': quantity,
                        'tag': 'ENTRY_INDEX',
                        'uri': PUBLISHER_URI_INDEX_OPT,
                        'ltp': ltp[f'NFO:{symbol}']['last_price']
                    }
                    
                    send_trade(trade)
                    
def scalp_sell(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            data = json.loads(message['data'])
            ltp = data['ltp']
            print(ltp)
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']

            print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x:
                if last_rsi < 40:
                    trade = {
                        'endpoint': '/place/market_order/sell',
                        'trading_symbol': symbol,
                        'exchange': 'NFO',
                        'quantity': quantity,
                        'tag':'ENTRY_INDEX',
                        'uri': PUBLISHER_URI_INDEX_OPT,
                        'ltp': ltp[f'NFO:{symbol}']['last_price']
                    }
                    
                    # publish trade to zerodha_worker queue
                    send_trade(trade)


redis_host = 'redis_server'
redis_port = 6379
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

# worker 5 logic
def start_trade(document, quantity):
    CE_KEY = 'CE_Stikes'
    PE_KEY = 'PE_Stikes'
    PERCENTAGE = 0.1
    
    ce_documents = document[CE_KEY]
    pe_documents = document[PE_KEY]
    
    pairs = set()
    
    for strike in ce_documents:
        ltp_ce = ce_documents[strike]['lastPrice']
        min_ltp_ce = ltp_ce*(1-PERCENTAGE)
        max_ltp_ce = ltp_ce*(1+PERCENTAGE)
        
        for strike_ in pe_documents:
            ltp_pe = pe_documents[strike_]['lastPrice']
            
            if ltp_pe >= min_ltp_ce and ltp_pe <= max_ltp_ce:
                pairs.add((ce_documents[strike]['weekly_Options_CE'], pe_documents[strike_]['weekly_Options_PE']))
    
        
    for strike in pe_documents:
        ltp_pe = pe_documents[strike]['lastPrice']
        min_ltp_pe = ltp_pe*(1-PERCENTAGE)
        max_ltp_pe = ltp_pe*(1+PERCENTAGE)
        
        for strike_ in ce_documents:
            ltp_ce = ce_documents[strike_]['lastPrice']
            
            if ltp_ce >= min_ltp_pe and ltp_ce <= max_ltp_pe:
                pairs.add((ce_documents[strike_]['weekly_Options_CE'], pe_documents[strike]['weekly_Options_PE']))
                
    
    # remove duplicate elements from the set
    pairs = set(pairs)
    
    for pair in pairs:
        ticker_a, ticker_b = pair
        
        trade_a = {
            'endpoint': '/place/market_order/buy',
            'trading_symbol': ticker_a,
            'exchange': 'NFO',
            'quantity':quantity,
            'tag': 'ENTRY_INDEX',
            'uri': PUBLISHER_URI_INDEX_OPT
        }
    
        # send trade to zerodha_worker
        status, _ = send_trade(trade_a)
        
        if not status:
            continue
        
        trade_b = {
            'endpoint': '/place/market_order/buy',
            'trading_symbol': ticker_b,
            'exchange': 'NFO',
            'quantity':quantity,
            'tag': 'ENTRY_INDEX',
            'uri': PUBLISHER_URI_INDEX_OPT
        }
        
        status, _ = send_trade(trade_b)
        
        # if second trade dosen't execute then rollback previous trade
        if not status:
            print('rollbacking 1st trade')
            trade_a['endpoint'] = '/place/market_order/sell'
            trade_a['tag'] = 'EXIT'
            status, _ = send_trade(trade_a)
            continue
        
        pair = f'{ticker_a}-{ticker_b}'
        RedisWorker5Dict().insert(pair)
        
        break
    
    return



def fetch_data_from_api(url, sybmol=''):

    logging.info(f"Beginning Fetching Data from Api for symbol {sybmol}")
    logging.info(f"Targeted URL : {url}")

    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en,en-US;q=0.9,ar;q=0.8',
        # 'cache-control': 'max-age=0',
        # 'upgrade-insecure-requests': '1',
        'referer': 'https://www.nseindia.com/option-chain',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }
    with requests.Session() as session:
        main_page = 'https://www.nseindia.com/option-chain'
        logging.info('Loading Home Page')
        session.get(main_page, headers={'user-agent': 'Mozilla/5.0'})
        logging.info('Loading Json Response')
        resp_cont = session.get(url, headers=headers)
        if resp_cont.status_code == 401:  # Resource not found
            logging.info('Resource not found')
            logging.info('Sleeping 2 seconds before retying')
            sleep(2)
            return fetch_data_from_api(url=url, sybmol=sybmol)
        logging.info('Valid Json Response')

        return resp_cont.json()


# for the stocks
def scalp_buy_stock(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    total_quantity = quantity
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('stocks')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            data = json.loads(message['data'])
            quotes = data['quotes']
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']

            if datetime.datetime.now().time() > x and last_rsi > 40 and last_slope > 40:
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': symbol,
                    'exchange': 'NSE',
                    'quantity': quantity,
                    'tag': 'ENTRY_STOCK',
                    'uri': PUBLISHER_URI_STOCKS,
                    'ltp': quotes[f'NSE:{symbol}']['last_price']
                }
                
                send_trade(trade)
                total_quantity += quantity



def scalp_sell_stock(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    total_quantity = quantity
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('stocks')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            data = json.loads(message['data'])
            quotes = data['quotes']
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']

            if datetime.datetime.now().time() > x and last_rsi < 40 and last_slope < 0:
                trade = {
                    'endpoint': '/place/market_order/sell',
                    'trading_symbol': symbol,
                    'exchange': 'NSE',
                    'quantity': quantity,
                    'tag': 'ENTRY_STOCK',
                    'uri': PUBLISHER_URI_STOCKS,
                    'ltp': quotes[f'NSE:{symbol}']['last_price']
                }
                
                send_trade(trade)
                total_quantity += quantity


# stock options
def scalp_buy_stock_option(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    total_quantity = quantity
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('stock_option')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            quotes = json.loads(message['data'])
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']
            
            for ticker in quotes:
                if f'NFO:{symbol}' == ticker:
                    if datetime.datetime.now().time() > x and last_rsi > 40 and last_slope > 0:
                        trade = {
                            'endpoint': '/place/limit_order/buy',
                            'trading_symbol': symbol,
                            'exchange': 'NFO',
                            'quantity': quantity,
                            'tag': 'ENTRY_STOCK_OPT',
                            'price': quotes[ticker]['depth']['sell'][1]['price'],
                            'uri': PUBLISHER_URI_STOCK_OPT,
                            'ltp': quotes[ticker]['last_price']
                        }
                        
                        send_trade(trade)
                        total_quantity += quantity
                        break



def scalp_sell_stock_option(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    total_quantity = quantity
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('stock_option')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            quotes = json.loads(message['data'])
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']
            
            for ticker in quotes:
                if f'NFO:{symbol}' == ticker:
                    if datetime.datetime.now().time() > x and last_rsi < 40  and last_slope < 0:
                        trade = {
                            'endpoint': '/place/limit_order/sell',
                            'trading_symbol': symbol,
                            'exchange': 'NFO',
                            'quantity': quantity,
                            'tag': 'ENTRY_STOCK_OPT',
                            'price': quotes[ticker]['depth']['buy'][1]['price'],
                            'uri': PUBLISHER_URI_STOCK_OPT,
                            'ltp': quotes[ticker]['last_price']
                        }
                        
                        send_trade(trade)
                        total_quantity += quantity
                        break

# stock futures
def scalp_buy_stock_fut(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    total_quantity = quantity
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('stock_fut')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            quotes = json.loads(message['data'])
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']
            
            for ticker in quotes:
                if f'NFO:{symbol}' == ticker:
                    if datetime.datetime.now().time() > x and last_rsi > 40  and last_slope > 0:
                        trade = {
                            'endpoint': '/place/limit_order/buy',
                            'trading_symbol': symbol,
                            'exchange': 'NFO',
                            'quantity': quantity,
                            'tag': 'ENTRY_STOCK_FUT',
                            'price': quotes[ticker]['depth']['sell'][1]['price'],
                            'uri': PUBLISHER_URI_STOCK_FUT,
                            'ltp': quotes[ticker]['last_price']
                        }
                        
                        send_trade(trade)
                        total_quantity += quantity
                        break



def scalp_sell_stock_fut(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    total_quantity = quantity
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('stock_fut')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            quotes = json.loads(message['data'])
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']
            
            for ticker in quotes:
                if f'NFO:{symbol}' == ticker:
                    if datetime.datetime.now().time() > x and last_rsi < 40  and last_slope < 0:
                        trade = {
                            'endpoint': '/place/limit_order/sell',
                            'trading_symbol': symbol,
                            'exchange': 'NFO',
                            'quantity': quantity,
                            'tag': 'ENTRY_STOCK_FUT',
                            'price': quotes[ticker]['depth']['buy'][1]['price'],
                            'uri': PUBLISHER_URI_STOCK_FUT,
                            'ltp': quotes[ticker]['last_price']
                        }
                        
                        send_trade(trade)
                        total_quantity += quantity
                        break