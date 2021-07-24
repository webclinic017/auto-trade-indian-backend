import json
import pika

def send_trade(trade):
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbit_mq_index'))
    channel = connection.channel()
    channel.queue_declare(queue='zerodha_worker')
  
    # publish trade to zerodha worker queue
    channel.basic_publish(
        exchange='',
        routing_key='zerodha_worker',
        body=json.dumps(trade).encode()
    )
    connection.close()
