import time, pika, json, os
from services.function_signals import fetch_data_from_api

RABBIT_MQ_SERVER = os.environ['RABBIT_MQ_HOST']

def main():
    while True:
        tickers = [
            'AARTIIND', 'ACC', 'ADANIENT', 'ADANIPORTS', 'AMARAJABAT', 'AMBUJACEM', 'APOLLOHOSP',
            'APOLLOTYRE', 'ASHOKLEY',
            'ASIANPAINT', 'AUROPHARMA', 'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE',
            'BALKRISIND', 
            'BANKBARODA', 'BATAINDIA', 'BEL', 'BERGEPAINT', 'BHARATFORG', 'BHARTIARTL', 
            'BIOCON', 
            'BPCL', 'BRITANNIA', 'CADILAHC', 'CANBK', 'CHOLAFIN', 'CIPLA', 'COALINDIA', 'COFORGE',
            'COLPAL', 'CONCOR',
            'CUMMINSIND', 'DABUR', 'DIVISLAB', 'DLF', 'DRREDDY', 'EICHERMOT', 'ESCORTS',
            'EXIDEIND', 'FEDERALBNK', 'GAIL',
            'GLENMARK', 'GODREJCP', 'GODREJPROP', 'GRASIM', 'HAVELLS', 'HCLTECH',
            'HDFC', 'HDFCAMC', 'HDFCBANK',
            'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDPETRO', 'HINDUNILVR', 'IBULHSGFIN',
            'ICICIBANK', 'ICICIGI',
            'ICICIPRULI','IDFCFIRSTB', 
            'IGL', 'INDIGO', 'INDUSINDBK', 'INDUSTOWER',
            'INFY', 'IOC',
            'ITC', 'JINDALSTEL', 'JSWSTEEL', 'JUBLFOOD', 'KOTAKBANK',
            'LICHSGFIN', 'LT', 'LUPIN',
            'MANAPPURAM', 
            'MARICO', 
            'MARUTI', 'MCDOWELL-N', 'MFSL', 'MGL',
            'MINDTREE', 'MOTHERSUMI', 'MRF',
            'MUTHOOTFIN', 'NATIONALUM', 'NAUKRI','NMDC', 'NTPC', 'ONGC',
            'PEL', 'PFC',
            'PIDILITIND', 'PNB', 'POWERGRID', 'PVR', 'RAMCOCEM', 'RBLBANK', 'RECLTD', 'RELIANCE',
            'SBILIFE', 'SBIN',
            'SIEMENS', 'SRF', 'SRTRANSFIN', 'SUNPHARMA', 'TATACHEM',
            'TATACONSUM', 'TATAMOTORS',
            'TATAPOWER', 'TATASTEEL', 'TCS', 'TECHM', 'TITAN','TORNTPOWER',
            'TVSMOTOR', 'UBL', 'ULTRACEMCO',
            'UPL', 'VEDL', 'VOLTAS', 'WIPRO', 'ZEEL'
        ]
        
        connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_MQ_SERVER))
        channel = connection.channel()
        channel.queue_declare(queue='trader_stock')


        for ticker in tickers:
            url = f'https://www.nseindia.com/api/option-chain-equities?symbol={ticker}'
            json_data = fetch_data_from_api(url)
            json_data['ticker'] = ticker
            channel.basic_publish(
                exchange='',
                routing_key='trader_stock',
                body=json.dumps(json_data).encode()
            )
            print('[*] message send to queue..')

        time.sleep(15)
        channel.close()
        time.sleep(900 - 15)