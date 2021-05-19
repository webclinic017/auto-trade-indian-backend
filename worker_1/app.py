from re import T
import pika
import json
from streamer import Streamer
from pymongo import MongoClient
from functions_db import get_key_token
import datetime
import os
import gc
import threading

mongo = MongoClient('mongodb://db')
db = mongo['intraday'+str(datetime.date.today())]
collection = mongo['orders']

mongo_clients = mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

worker = 'worker_1'

zerodha_id = os.environ['USERNAME']
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])

# access_token = "PSTIVkiKnMIYot42uTXnF9LbBKLqBeT4"

ws_host = os.environ['WS_HOST']

tickers = {}


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq'))
    channel = connection.channel()
    channel.queue_declare(queue=worker)

    # the encoded body is received below and it is decoded to readable format )(utf-8 is readable text)

    def callback(ch, method, properties, body):
        print('[*] Message Received')
        document = json.loads(body.decode('utf-8'))

        if document['instrument'] not in tickers:
            tickers[document['instrument']] = Streamer(
                document['token'],
                ws_host,
                api_key,
                access_token,
                document
            )
            t = threading.Thread(target=tickers[document['instrument']].start)
            t.start()
        else:
            # just update the document
            tickers[document['instrument']].document = document
            if tickers[document['instrument']].should_trade == False:
                tickers[document['instrument']].should_trade = True
                tickers[document['instrument']].should_stream = True
                tickers[document['instrument']].mode = 'entry'

    channel.basic_consume(
        queue=worker, on_message_callback=callback, auto_ack=True)
    print('[*] Waiting for Message')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
