import time
from scraper import fetch_data_from_api
import pika
import json


while True:
    tickers = ['NIFTY', 'BANKNIFTY']
    
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbit_mq_index'))
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

    channel.close()
    time.sleep(900)
