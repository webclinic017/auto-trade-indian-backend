import pika
import json
from functions_signals import gen_data
from functions_db import insert_data
from pymongo import MongoClient
import os
import datetime

mongo = MongoClient("mongodb://db")
db = mongo['intraday_'+str(datetime.date.today())]
collection = db['index_master']


def main(expiry_date):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq'))
    channel = connection.channel()
    channel.queue_declare(queue='trader')
    channel.queue_declare(queue='compare')

    def callback(ch, method, properties, body):
        print("[*] Message Received")
        json_data = json.loads(body.decode('utf-8'))
        ticker = json_data['ticker']
        # print(json_data)

        data = gen_data(json_data, expiry_date)
        should_send = insert_data(collection, data, json_data['ticker'])

        if should_send:
            doc = collection.find_one(
                {"ticker": ticker}, {"data": {"$slice": -2}})
            doc["_id"] = str(doc["_id"])

            channel.basic_publish(
                exchange='',
                routing_key='compare',
                body=json.dumps(doc).encode()
            )

            print("[*] Message send to Compare")
        else:
            print("[*] Need 2 documents to compare")
        
        
        doc = collection.find_one(
            {'ticker':ticker}, {"data":{"$slice":-2}}
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
