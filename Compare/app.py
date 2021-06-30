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
        current = json_data['data'].pop()
        prev = json_data['data'].pop()
        
        latest_compare = compareResult(prev, current, True)
        
        print('COMPARE FILE IS')
        print(latest_compare)
    
    channel.basic_consume(queue='compare', on_message_callback=callback, auto_ack=True)
    channel.consume()

if __name__ == '__main__':
    main()