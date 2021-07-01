import pika
import json
from functions_signals import gen_data
from functions_db import insert_data
from pymongo import MongoClient
import os
import datetime

today = str(datetime.date.today())
yesterday = str(datetime.date.today() - datetime.timedelta(days=1))

stock_market_end = datetime.time(15, 30, 0)

mongo = MongoClient("mongodb://db")
db = mongo['intraday_' + today]
collection = db['index_master']
db_ = mongo['intraday_' + yesterday]
collection_ = db_['index_master']

def main(expiry_date):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq'))
    channel = connection.channel()
    channel.queue_declare(queue='trader')
    channel.queue_declare(queue='compare')
    channel.queue_declare(queue='worker_5')

    def callback(ch, method, properties, body):
        print("[*] Message Received")
        json_data = json.loads(body.decode('utf-8'))
        ticker = json_data['ticker']
        # print(json_data)

        data = gen_data(json_data, expiry_date)
        
        # should_send = insert_data(collection, data, json_data['ticker'])
        insert_data(collection, data, json_data['ticker'])
        
        # if should_send:
        #     doc = collection.find_one(
        #         {"ticker": ticker}, {"data": {"$slice": -2}})
        #     doc["_id"] = str(doc["_id"])

        #     channel.basic_publish(
        #         exchange='',
        #         routing_key='compare',
        #         body=json.dumps(doc).encode()
        #     )

        #     print("[*] Message send to Compare")
        # else:
        #     print("[*] Need 2 documents to compare")
        
        min_time = datetime.time(stock_market_end.hour, stock_market_end.minute - 15)
        max_time = datetime.time(stock_market_end.hour, stock_market_end.minute - 13)
        now = datetime.datetime.now().time()
        
        if now >= min_time and now <= max_time:
            doc_today = collection.find_one({'ticker':ticker}, {"data":{"$slice":-1}})
            doc_yesterday = collection.find_one({'ticker':ticker}, {"data":{"$slice":-1}})
            
            if doc_yesterday != None and doc_today != None:
                # send to compare to perform the trading
                data = {"data":[doc_yesterday, doc_today]}
                channel.basic_publish(
                    exchange='',
                    routing_key='compare',
                    body=json.dumps(data).encode()
                )
            else:
                print('[**] Needed Yesterday\'s Data for Compare')
            
        doc = collection.find_one(
            {'ticker':ticker}, {"data":{"$slice":-1}}
        )
        
        doc["_id"] = str(doc["_id"])
        
        channel.basic_publish(
            exchange='',
            routing_key='worker_5',
            body=json.dumps(doc).encode()
        )
        print('[*] Latest document send to worker 5')

    channel.basic_consume(
        queue='trader', on_message_callback=callback, auto_ack=True)
    print('[*] Waiting for Message')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        print(os.environ['EXPIRY_DATE'])
        main(expiry_date=os.environ['EXPIRY_DATE'])
    except KeyboardInterrupt:
        exit()
