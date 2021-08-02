import time, pika, json, os
from .function_signals import fetch_data_from_api

RABBIT_MQ_SERVER = os.environ['RABBIT_MQ_HOST']

def main():
    while True:
        tickers = ['NIFTY', 'BANKNIFTY']
        
        connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_MQ_SERVER))
        channel = connection.channel()
        channel.queue_declare(queue='trader')


        for ticker in tickers:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={ticker}"
            json_data = fetch_data_from_api(url)
            json_data['ticker'] = ticker
            channel.basic_publish(
                exchange='',
                routing_key='trader',
                body=json.dumps(json_data).encode()
            )
            print('[*] message send to queue..')

        time.sleep(15)
        channel.close()
        time.sleep(900 - 15)