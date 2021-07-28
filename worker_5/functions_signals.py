import json, redis, os


PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']

redis_host = 'redis_server'
redis_port = 6379
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

def send_trade(trade, channel):
    channel.basic_publish(
        exchange='',
        routing_key='zerodha_worker',
        body=json.dumps(trade).encode()
    )

def start_trade(document, quantity, channel):
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
                
                # send trade to zerodha_worker queue
                send_trade(trade, channel)
                                
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': pe_documents[strike_]['weekly_Options_PE'],
                    'exchange': 'NFO',
                    'quantity':quantity,
                    'tag': 'ENTRY_INDEX',
                    'uri': PUBLISHER_URI_INDEX_OPT
                }
                
                # send the trade to zerodha_worker queue
                send_trade(trade, channel)
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
                

                # send trade to zerodha_worker queue
                send_trade(trade, channel)
                
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': pe_documents[strike]['weekly_Options_PE'],
                    'exchange': 'NFO',
                    'quantity':quantity,
                    'tag': 'ENTRY_INDEX',
                    'uri': PUBLISHER_URI_INDEX_OPT
                }
                
                
                # send trade to zerodha_worker queue
                send_trade(trade, channel)
                return
    
    return