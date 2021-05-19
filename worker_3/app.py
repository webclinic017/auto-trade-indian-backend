import pika
import json
from pymongo import MongoClient
from functions_db import get_key_token
from zerodha_functions import *
from kiteconnect import KiteConnect
import os
import datetime

mongo = MongoClient('mongodb://db')
db = mongo['intraday'+str(datetime.date.today())]
collection = mongo['orders']

mongo_clients = mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

worker = 'worker_3'

zerodha_id = os.environ['USERNAME']
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])

# access_token = 'PSTIVkiKnMIYot42uTXnF9LbBKLqBeT4'

kite = KiteConnect(api_key, access_token=access_token)


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq'))
    channel = connection.channel()
    channel.queue_declare(queue=worker)

    def callback(ch, method, properties, body):
        print('[*] Message Received')
        document = json.loads(body.decode('utf-8'))

        positions = kite.positions()
        is_present_CE = False
        is_present_PE = False

        ticker_CE = document['ticker_CE']
        ticker_PE = document['ticker_PE']

        for position in positions['day']:
            if ticker_CE == position['tradingsymbol']:
                is_present_CE = True
                break

        for position in positions['day']:
            if ticker_PE == position['tradingsymbol']:
                is_present_PE = True
                break

        if document['enter']:

            if not(is_present_CE and is_present_PE):
                market_sell_order(
                    kite,
                    document['ticker_CE'],
                    kite.EXCHANGE_NFO,
                    document['quantity_ce']
                )
                market_sell_order(
                    kite,
                    document['ticker_PE'],
                    kite.EXCHANGE_NFO,
                    document['quantity_pe']
                )

                print('[**] ORDER PLACED [**]')

        else:
            ticker_CE = document['ticker_CE']
            ticker_PE = document['ticker_PE']

            positions = kite.positions()
            is_present_CE = False
            is_present_PE = False

            ce_buy_quantity = 0
            pe_buy_quantity = 0

            for position in positions['day']:
                if ticker_CE == position['tradingsymbol']:
                    is_present_CE = True
                    ce_buy_quantity = document['quantity_ce']
                    break

            for position in positions['day']:
                if ticker_PE == position['tradingsymbol']:
                    is_present_PE = True
                    pe_buy_quantity = document['quantity_pe']
                    break

            print(ticker_PE)
            print(ticker_CE)
            print(f'[****] Quantity: {ce_buy_quantity} [****]')
            print(f'[****] Quantity: {pe_buy_quantity} [****]')

            if (is_present_CE and is_present_PE) and (ce_buy_quantity > 0 and pe_buy_quantity > 0):

                market_buy_order(
                    kite,
                    document['ticker_CE'],
                    kite.EXCHANGE_NFO,
                    ce_buy_quantity
                )
                market_buy_order(
                    kite,
                    document['ticker_PE'],
                    kite.EXCHANGE_NFO,
                    pe_buy_quantity
                )

                print('[**] ORDER EXITED [**]')

    channel.basic_consume(
        queue=worker, on_message_callback=callback, auto_ack=True)
    print('[*] Waiting for Message')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
