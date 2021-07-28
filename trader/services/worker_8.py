import requests, time
from function_signals import *
import os

tickers = ['NIFTY2172216000CE']
quantity = 75

PUBLISHER_URI_INDEX_OPT = os.environ['PUBLISHER_URI_INDEX_OPT']

while True:
    data = {'tickers':list(map(lambda x : f'NFO:{x}', tickers))}
    quotes = requests.post('http://zerodha_worker_index/get/quote', json=data).json()
    print(quotes)
    for ticker in tickers:
        ema = requests.get(f'http://zerodha_worker_index/get/ema/{ticker}').json()
        # print(ticker, ema)
        
        if quotes[f'NFO:{ticker}']['volume'] > ema:
            trade = {
                'endpoint': '/place/market_order/buy',
                'trading_symbol': ticker,
                'exchange': 'NFO',
                'quantity': quantity,
                'tag': 'ENTRY_INDEX',
                'uri': PUBLISHER_URI_INDEX_OPT
            }
        else:
            trade = {
                'endpoint': '/place/market_order/sell',
                'trading_symbol': ticker,
                'exchange': 'NFO',
                'quantity': quantity,
                'tag': 'EXIT',
                'uri': PUBLISHER_URI_INDEX_OPT
            }
        

    time.sleep(300)