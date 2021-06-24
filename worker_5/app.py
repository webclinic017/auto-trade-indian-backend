import json
import pika
from functions_db import get_key_token
from functions_signals import start_trade
from pymongo import MongoClient
from kiteconnect import KiteConnect
import os

mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

token_map = mongo_clients['tokens']['tokens_map'].find_one()

worker = 'worker_5'

zerodha_id = os.environ['USERNAME']
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])

kite = KiteConnect(api_key=api_key, access_token=access_token)

nf_quantity = int(os.environ['NF_QUANTITY'])
bf_quantity = int(os.environ['BF_QUANTITY'])

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq')
    )
    channel = connection.channel()
    channel.queue_declare(queue=worker)
    
    def callback(ch, method, properties, body):
        print('[*] Message Received')
        document = json.loads(body.decode('utf-8'))
        # logic for auto trade goes here
        
        if document['ticker'] == 'NIFTY':
            quantity = nf_quantity
        elif document['ticker'] == 'BANKNIFTY':
            quantity = bf_quantity
        
        try:
            start_trade(kite, document['data'].pop(), quantity)
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
