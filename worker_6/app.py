import json
import pika
from functions_signals import send_trade
import os

worker = 'worker_6'

nf_quantity = int(os.environ['NF_QUANTITY'])
bf_quantity = int(os.environ['BF_QUANTITY'])

quantity = int(os.environ['W6_QUANTITY'])

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq')
    )
    channel = connection.channel()
    result = channel.queue_declare(queue=worker)
    channel.queue_bind(exchange='index', queue=result.method.queue)
    
    result = channel.queue_declare(queue='zerodha_worker')
    channel.queue_bind(exchange='index', queue=result.method.queue)
    
    def callback(ch, method, properties, body):
        print('[*] Message Received')
        latest_compare = json.loads(body.decode('utf-8'))
        # logic for auto trade goes here
        if (latest_compare['total_power'] > quantity):
            
            if latest_compare['symbol'] == 'BANKNIFTY':
                print("i can buy" , latest_compare['weekly_Options_CE'])
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': latest_compare['weekly_Options_CE'],
                    'exchange': 'NFO',
                    'quantity': bf_quantity,
                    'tag': 'ENTRY_INDEX'
                }
                send_trade(trade, channel)
                
                print("i can buy" , latest_compare['futures'])
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': latest_compare['futures'],
                    'exchange': 'NFO',
                    'quantity': bf_quantity,
                    'tag': 'ENTRY_INDEX'
                }
                send_trade(trade, channel)
                
            elif latest_compare['symbol'] == 'NIFTY':
                print("i can buy" , latest_compare['weekly_Options_CE'])
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': latest_compare['weekly_Options_CE'],
                    'exchange': 'NFO',
                    'quantity': nf_quantity,
                    'tag': 'ENTRY_INDEX'
                }
                send_trade(trade, channel)
                
                print("i can buy" , latest_compare['futures'])
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': latest_compare['futures'],
                    'exchange': 'NFO',
                    'quantity': nf_quantity,
                    'tag': 'ENTRY_INDEX'
                }
                send_trade(trade, channel)
                
        elif (latest_compare['total_power'] < -quantity):
            
            if latest_compare['symbol'] == 'BANKNIFTY':
                print("i can buy" , latest_compare['weekly_Options_PE'])
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': latest_compare['weekly_Options_PE'],
                    'exchange': 'NFO',
                    'quantity': bf_quantity,
                    'tag': 'ENTRY_INDEX'
                }
                send_trade(trade, channel)
                
                print("i can sell" , latest_compare['futures'])
                trade = {
                    'endpoint': '/place/market_order/sell',
                    'trading_symbol': latest_compare['futures'],
                    'exchange': 'NFO',
                    'quantity': bf_quantity,
                    'tag': 'ENTRY_INDEX'
                }
                send_trade(trade, channel)
                
            elif latest_compare['symbol'] == 'NIFTY':
                print("i can buy" , latest_compare['weekly_Options_PE'])
                trade = {
                    'endpoint': '/place/market_order/buy',
                    'trading_symbol': latest_compare['weekly_Options_PE'],
                    'exchange': 'NFO',
                    'quantity': nf_quantity,
                    'tag': 'ENTRY_INDEX'
                }
                send_trade(trade, channel)
                
                print("i can sell" , latest_compare['futures'])
                trade = {
                    'endpoint': '/place/market_order/sell',
                    'trading_symbol': latest_compare['futures'],
                    'exchange': 'NFO',
                    'quantity': nf_quantity,
                    'tag': 'ENTRY_INDEX'
                }
                send_trade(trade, channel)
            
        else:
            #print("i did nothing for" , jsonObject[-1]['symbol'])
            pass

    channel.basic_consume(
        queue=worker, on_message_callback=callback, auto_ack=True
    )
    print('[*] Waiting for Message')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
