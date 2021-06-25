import requests
import redis


token_map = requests.get('http://zerodha_worker/get/token_map').json()


redis_host = 'redis_pubsub'
redis_port = 6379
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)


def start_trade(document, quantity):
    flag = False
    
    CE_KEY = 'CE_Stikes'
    PE_KEY = 'PE_Stikes'
    PERCENTAGE = 5/100
    
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
                    'quantity':quantity
                }
                                
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': pe_documents[strike_]['weekly_Options_PE'],
                    'exchange': 'NFO',
                    'quantity':quantity
                }

                # send the trade to zerodha_worker queue
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
                    'quantity':quantity
                }

                # send trade to zerodha_worker queue
                
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': pe_documents[strike]['weekly_Options_PE'],
                    'exchange': 'NFO',
                    'quantity':quantity
                }
                
                # send trade to zerodha_worker queue
                return
    
    return