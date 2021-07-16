import requests
import time

tickers = ['NIFTY2172216000CE']

while True:
    data = {'tickers':list(map(lambda x : f'NFO:{x}', tickers))}
    quotes = requests.post('http://zerodha_worker_index/get/quote', json=data).json()
    print(quotes)
    for ticker in tickers:
        ema = requests.get(f'http://zerodha_worker_index/get/ema/{ticker}').json()
        # print(ticker, ema)
        
        if quotes[f'NFO:{ticker}']['volume'] > ema:
            print('ENTER THE TICKER')
        else:
            print('EXIT TICKER')
        

    time.sleep(300)