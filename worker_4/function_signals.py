import datetime, json, redis, requests, pika

def send_trade(trade):
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbit_mq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='index', exchange_type='fanout')
    result = channel.queue_declare(queue='zerodha_worker')
    channel.queue_bind(exchange='index', queue=result.method.queue)
    
    
    # publish trade to zerodha worker queue
    channel.basic_publish(
        exchange='index',
        routing_key='zerodha_worker',
        body=json.dumps(trade).encode()
    )
    connection.close()


        
def scalp_buy(symbol, quantity, n, redis_host='redis_server', redis_port=6379):
    x = datetime.time(6,45)
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            positions = json.loads(message['data'])
            rsi = requests.get(f'http://zerodha_worker/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']

            print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x:
                if last_rsi > 40:
                    trade = {
                        'endpoint': '/place/market_order/buy',
                        'trading_symbol': symbol,
                        'exchange': 'NFO',
                        'quantity': quantity,
                        'tag': 'ENTRY_INDEX'
                    }
                    
                    # publish trade to zerodha worker
                    send_trade(trade)
                    

def scalp_sell(symbol, quantity, n, redis_host='redis_server', redis_port=6379):
    x = datetime.time(6,45)
    
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    p = r.pubsub()
    p.subscribe('positions')
    
    for message in p.listen():
        if message['type'] != 'subscribe':
            positions = json.loads(message['data'])
            # print(positions)
            
            rsi = requests.get(f'http://zerodha_worker/get/rsi/{symbol}/7').json()
            last_rsi, last_slope = rsi['last_rsi'], rsi['last_slope']
            print(datetime.datetime.now().time())
            if datetime.datetime.now().time() > x:
                if last_rsi < 40:
                    trade = {
                        'endpoint': '/place/market_order/sell',
                        'trading_symbol': symbol,
                        'exchange': 'NFO',
                        'quantity': quantity,
                        'tag':'ENTRY_INDEX'
                    }
                    
                    # publish trade to zerodha_worker queue
                    send_trade(trade)