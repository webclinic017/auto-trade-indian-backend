import json
import pika
import requests
from functions_signals import start_trade
import os

token_map = requests.get('http://zerodha_worker_index/get/token_map').json()

worker = 'worker_5'

nf_quantity = int(os.environ['NF_QUANTITY'])
bf_quantity = int(os.environ['BF_QUANTITY'])

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq_index')
    )
    channel = connection.channel()
    channel.queue_declare(queue=worker)
    channel.queue_declare(queue='zerodha_worker')
    
    def callback(ch, method, properties, body):
        print('[*] Message Received')
        document = json.loads(body.decode('utf-8'))
        # logic for auto trade goes here
        
        if document['ticker'] == 'NIFTY':
            quantity = nf_quantity
        elif document['ticker'] == 'BANKNIFTY':
            quantity = bf_quantity
        
        try:
            start_trade(document['data'].pop(), quantity, channel)
        except:
            pass

    channel.basic_consume(
        queue=worker, on_message_callback=callback, auto_ack=True
    )
    print('[*] Waiting for Message')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
