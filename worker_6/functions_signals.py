import json

def send_trade(trade, channel):
    channel.basic_publish(
        exchange='index',
        routing_key='zerodha_worker',
        body=json.dumps(trade).encode()
    )
