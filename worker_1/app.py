import pika
import json
from streamer import Streamer
import os
import requests


worker = 'worker_1'

credentials = requests.get('http://zerodha_worker/get_api_key_token').json()
api_key = credentials['api_key']
access_token = credentials['access_token']

ws_host = os.environ['WS_HOST']
publisher_host = os.environ['PUBLISHER_HOST']
publisher_path = os.environ['PUBLISHER_PATH']

publisher_uri = f'{publisher_host}{publisher_path}'

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
                document,
                publisher_uri
            )
            tickers[document['instrument']].start()
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
