import datetime, redis, requests, os, json
import logging
from time import sleep

PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']
ZERODHA_SERVER = 'zerodha_worker_index'
REDIS_SERVER = 'redis_server_index'
RABBIT_MQ_SERVER = 'rabbit_mq_index'

def send_trade(trade):
    response = requests.post(f'http://{ZERODHA_SERVER}' + trade['endpoint'], json=trade)
    return response.ok, response.json()

def scalp_buy(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            # positions = json.loads(message['data'])
            rsi = requests.get(f'http://{ZERODHA_SERVER}/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']

            print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x:
                if last_rsi > 30 and last_slope > 0:
                    trade = {
                        'endpoint': '/place/market_order/buy',
                        'trading_symbol': symbol,
                        'exchange': 'NFO',
                        'quantity': quantity,
                        'tag': 'ENTRY_INDEX',
                        'uri': PUBLISHER_URI_INDEX_OPT
                    }
                    
                    send_trade(trade)
                    

def scalp_sell(symbol, quantity, n, redis_host='redis_server_index', redis_port=6379):
    x = datetime.time(6,45)
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            positions = json.loads(message['data'])
            
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
                        'uri': PUBLISHER_URI_INDEX_OPT
                    }
                    
                    # publish trade to zerodha_worker queue
                    send_trade(trade)


redis_host = 'redis_server'
redis_port = 6379
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

def start_trade(document, quantity):
    CE_KEY = 'CE_Stikes'
    PE_KEY = 'PE_Stikes'
    PERCENTAGE = 2/100
    
    ce_documents = document[CE_KEY]
    pe_documents = document[PE_KEY]
    
    for strike in ce_documents:
        ltp_ce = ce_documents[strike]['lastPrice']
        min_ltp_ce = ltp_ce*(1-PERCENTAGE)
        max_ltp_ce = ltp_ce*(1+PERCENTAGE)
        
        for strike_ in pe_documents:
            ltp_pe = pe_documents[strike_]['lastPrice']
            
            if ltp_pe >= min_ltp_ce and ltp_pe <= max_ltp_ce:
                print(ce_documents[strike]['weekly_Options_CE'], pe_documents[strike_]['weekly_Options_PE'])
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': ce_documents[strike]['weekly_Options_CE'],
                    'exchange': 'NFO',
                    'quantity':quantity,
                    'tag': 'ENTRY_INDEX',
                    'uri': PUBLISHER_URI_INDEX_OPT
                }
                
                # send trade to zerodha_worker
                send_trade(trade)
                                
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': pe_documents[strike_]['weekly_Options_PE'],
                    'exchange': 'NFO',
                    'quantity':quantity,
                    'tag': 'ENTRY_INDEX',
                    'uri': PUBLISHER_URI_INDEX_OPT
                }
                
                # send the trade to zerodha_worker
                send_trade(trade)
                return
    
        
    for strike in pe_documents:
        ltp_pe = pe_documents[strike]['lastPrice']
        min_ltp_pe = ltp_pe*(1-PERCENTAGE)
        max_ltp_pe = ltp_pe*(1+PERCENTAGE)
        
        for strike_ in ce_documents:
            ltp_ce = ce_documents[strike_]['lastPrice']
            
            if ltp_ce >= min_ltp_pe and ltp_ce <= max_ltp_pe:
                print(ce_documents[strike_]['weekly_Options_CE'], pe_documents[strike]['weekly_Options_PE'])
                
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': ce_documents[strike_]['weekly_Options_CE'],
                    'exchange': 'NFO',
                    'quantity':quantity,
                    'tag': 'ENTRY_INDEX',
                    'uri': PUBLISHER_URI_INDEX_OPT
                }
                

                # send trade to zerodha_worker
                send_trade(trade)
                
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': pe_documents[strike]['weekly_Options_PE'],
                    'exchange': 'NFO',
                    'quantity':quantity,
                    'tag': 'ENTRY_INDEX',
                    'uri': PUBLISHER_URI_INDEX_OPT
                }
                
                
                # send trade to zerodha_worker
                send_trade(trade)
                return
    
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
