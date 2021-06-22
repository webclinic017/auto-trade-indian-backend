import json
from zerodha_functions import *
import websocket

import os

PUBLISHER_HOST = os.environ['PUBLISHER_HOST']
PUBLISHER_PATH = os.environ['PUBLISHER_PATH']

PUBLISHER_URI = f'{PUBLISHER_HOST}{PUBLISHER_PATH}'

def send_notification(data):
    try:
        ws_publisher = websocket.create_connection(PUBLISHER_URI)
        ws_publisher.send(json.dumps(data))
        ws_publisher.close()
    except:
        pass

def start_trade(kite, document):
    flag = False
    
    CE_KEY = 'CE_Stikes'
    PE_KEY = 'PE_Stikes'
    PERCENTAGE = 0.05
    
    ce_documents = document[CE_KEY]
    pe_documents = document[PE_KEY]
    
    for strike in ce_documents:
        ltp_ce = ce_documents[strike]['lastPrice']
        min_ltp_ce = ltp_ce*(1-PERCENTAGE)
        max_ltp_ce = ltp_ce*(1+PERCENTAGE)
        
        for strike in pe_documents:
            ltp_pe = pe_documents[strike]['lastPrice']
            
            if ltp_pe >= min_ltp_ce or ltp_pe <= max_ltp_ce:
                print('[**] Performing Trade')
                flag = True
        
    if flag:
        return
        
    for strike in pe_documents:
        ltp_ce = pe_documents[strike]['lastPrice']
        min_ltp_pe = ltp_pe*(1-PERCENTAGE)
        max_ltp_pe = ltp_pe*(1+PERCENTAGE)
        
        for strike in ce_documents:
            ltp_ce = ce_documents[strike]['lastPrice']
            
            if ltp_ce >= min_ltp_pe or ltp_ce <= max_ltp_pe:
                print('[**] Performing Trade')
                flag = True
    
    return