import pika, json, requests, os, datetime
from services.functions_db import insert_data
from pymongo import MongoClient

MONGO_DB_URI = os.environ['MONGO_URI']
RABBIT_MQ_SERVER = os.environ['RABBIT_MQ_HOST']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']

today = str(datetime.date.today())
mongo = MongoClient(MONGO_DB_URI)
db = mongo['intraday_' + today]
collection = db['index_master']

def main(expiry_date):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_MQ_SERVER))
    channel = connection.channel()
    channel.queue_declare(queue='trader_index')
    channel.queue_declare(queue='compare_index')
    

    def callback(ch, method, properties, body):
        print("[*] Message Received")
        json_data = json.loads(body.decode('utf-8'))
        ticker = json_data['ticker']

        data = requests.post(f'http://{ZERODHA_SERVER}/gen_data', json={'data':json_data, 'expiry':expiry_date}).json()
        should_send = insert_data(collection, data, json_data['ticker'])
        
        if should_send:
            doc = collection.find_one(
                {"ticker": ticker}, {"data": {"$slice": -2}})
            doc["_id"] = str(doc["_id"])
            
            data_ = {"raw": doc, "eod": False}

            channel.basic_publish(
                exchange='',
                routing_key='compare_index',
                body=json.dumps(data_).encode()
            )

            print("[*] Message send to Compare")
        else:
            print("[*] Need 2 documents to compare")
    

    channel.basic_consume(
        queue='trader_index', on_message_callback=callback, auto_ack=True)
    print('[*] Waiting for Message')
    channel.start_consuming()
