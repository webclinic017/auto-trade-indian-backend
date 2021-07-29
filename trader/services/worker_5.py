import json
import pika
import requests
from .function_signals import start_trade
import os

ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
RABBIT_MQ_SERVER = os.environ['RABBIT_MQ_HOST']

token_map = requests.get(f'http://{ZERODHA_SERVER}/get/token_map').json()

worker = 'worker_5'
nf_quantity = int(os.environ['NF_QUANTITY'])
bf_quantity = int(os.environ['BF_QUANTITY'])

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_MQ_SERVER)
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
            start_trade(document['data'].pop(), quantity)
        except:
            pass

    channel.basic_consume(
        queue=worker, on_message_callback=callback, auto_ack=True
    )
    print('[*] Waiting for Message')
    channel.start_consuming()
