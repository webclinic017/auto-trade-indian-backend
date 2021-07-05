import time
from scraper import fetch_data_from_api
import pika
import json


while True:
    tickers = ['NIFTY', 'BANKNIFTY']
    
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbit_mq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='index', exchange_type='fanout')
    result = channel.queue_declare(queue='trader')
    channel.queue_bind(exchange='index', queue=result.method.queue)

    for ticker in tickers:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={ticker}"
        json_data = fetch_data_from_api(url)
        json_data['ticker'] = ticker
        channel.basic_publish(
            exchange='index',
            routing_key='trader',
            body=json.dumps(json_data).encode()
        )
        print('[*] message send to queue..')

    channel.close()
    time.sleep(900)
