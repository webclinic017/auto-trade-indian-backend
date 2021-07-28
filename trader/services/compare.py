import json, pika, requests

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq_index')
    )
    channel = connection.channel()
    channel.queue_declare(queue='compare')
    
    
    def callback(ch, method, properties, body):
        print('[*] Message Received')
        json_data = json.loads(body.decode('utf-8'))
        # print(json_data)
        latest_compare = requests.post('http://zerodha_worker_index/compare_results', json=json_data).json()
        
    
    channel.basic_consume(queue='compare', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    main()