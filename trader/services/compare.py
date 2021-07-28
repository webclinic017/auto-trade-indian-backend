import json, pika, requests, os

RABBIT_MQ_SERVER = os.environ['RABBIT_MQ_HOST']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_MQ_SERVER)
    )
    channel = connection.channel()
    channel.queue_declare(queue='compare')
    
    def callback(ch, method, properties, body):
        print('[*] Message Received')
        json_data = json.loads(body.decode('utf-8'))
        # print(json_data)
        latest_compare = requests.post(f'http://{ZERODHA_SERVER}/compare_results', json=json_data).json()
        
    
    channel.basic_consume(queue='compare', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    main()