import json, pika
from functions_signals import *

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq')
    )
    channel = connection.channel()
    channel.queue_declare(queue='compare')
    
    
    def callback(ch, method, properties, body):
        print('[*] Message Received')
        json_data = json.loads(body.decode('utf-8'))
        # print(json_data)
        
        current = json_data['raw']['data'].pop()
        prev = json_data['raw']['data'].pop()
        latest_compare = compareResult(prev, current, True)
        
        # print(json_data)
        
        # send the latest compare to worker 6
        if json_data['eod']:
            channel.basic_publish(
                exchange='',
                routing_key='worker_6',
                body=json.dumps(latest_compare).encode(),
            )
    
    channel.basic_consume(queue='compare', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    main()