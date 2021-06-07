import pika
import json
from functions_signals import *
from functions_db import insert_data
from pymongo import MongoClient
import datetime
import os
import requests

mongo = MongoClient("mongodb://db")
db = mongo['intraday_'+str(datetime.date.today())]
collection = db['index_compare']

# take tokens from the online mongo db
mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
token_map = mongo_clients['tokens']['tokens_map'].find_one()


nf_quantity = int(os.environ['NF_QUANTITY'])
bf_quantity = int(os.environ['BF_QUANTITY'])
investment = int(os.environ['INVESTMENT'])
max_loss = int(os.environ['MAX_LOSS'])
expected_profit = int(os.environ['EXPECTED_PROFIT'])

token_server = os.environ['TOKEN_SERVER']

tokens = set()


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbit_mq'))
    channel = connection.channel()
    channel.queue_declare(queue='compare')

    def callback(ch, method, properties, body):
        print("[*] Message Received")
        json_data = json.loads(body.decode('utf-8'))
        current = json_data['data'].pop()
        prev = json_data['data'].pop()

        latest_compare = compareResult(prev, current, True)
        # Take this as reference

        if (latest_compare['weekly_Options_CE'] not in token_map) or (latest_compare['weekly_Options_PE'] not in token_map):
            print('TOKEN NOT PRESENT')
            return 


        UP_TREND = 'uptrend'
        DOWN_TREND = 'downtrend'

        atr_PE = get_atr(latest_compare['weekly_Options_PE'])
        atr_CE = get_atr(latest_compare['weekly_Options_CE'])
        # ema5_ce,ema8_ce,ema13_ce,ema20_ce=ema_5813(latest_compare['weekly_Options_CE'])
        # ema5_pe,ema8_pe,ema13_pe,ema20_pe=ema_5813(latest_compare['weekly_Options_PE'])
        slope_ce, trend_ce = slope(latest_compare['weekly_Options_CE'], 7)
        print("slope",latest_compare['weekly_Options_CE'], slope_ce)
        print("trend",latest_compare['weekly_Options_CE'], trend_ce)
        slope_pe, trend_pe = slope(latest_compare['weekly_Options_PE'], 7)
        print("slope",latest_compare['weekly_Options_PE'], slope_pe)
        print("trend",latest_compare['weekly_Options_PE'], trend_pe)
        
        latest_compare['atr_PE'] = atr_PE
        latest_compare['atr_CE'] = atr_CE
        latest_compare['slope_ce'] = slope_ce
        latest_compare['slope_pe'] = slope_pe
        latest_compare['trend_ce'] = trend_ce
        latest_compare['trend_pe'] = trend_pe
        insert_data(collection, latest_compare, latest_compare['symbol'])


###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 1 Start                                                                                                                                                #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

        if (latest_compare['total_power'] > 500) and (latest_compare['costly_option'] == 'bull') and (trend_ce == UP_TREND  or (slope_ce >= 30)):
            document = {
                'instrument': latest_compare['weekly_Options_CE'],
                'token': token_map[latest_compare['weekly_Options_CE']]['token'],
                'trade_direction': 'buy',
                'entry_level': latest_compare['ltp'],
                'last_time': latest_compare["last_time"],
                'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_CE'] else nf_quantity,
                'entry': True,
                'sl_points': latest_compare['atr_CE']

            }

            if latest_compare['weekly_Options_CE'] not in tokens:
                token = token_map[latest_compare['weekly_Options_CE']]['token']
                requests.get(f'http://{token_server}:3000/subscribe/{token}')
                tokens.add(latest_compare['weekly_Options_CE'])
            
            # the above document is encoded in binary format and named with variable body and sent to worker 1 app.py
            channel.basic_publish(
                exchange='',
                routing_key='worker_1',
                body=json.dumps(document).encode()
            )

            symbol = document['instrument']
            print(f'[**] Message send to worker 1 to buy CE {symbol}')

        if (latest_compare['total_power'] < -500) and latest_compare['costly_option'] == 'bear' and (trend_pe == UP_TREND or (slope_pe >= 30)):
            document = {
                'instrument': latest_compare['weekly_Options_PE'],
                'token': token_map[latest_compare['weekly_Options_PE']]['token'],
                'trade_direction': 'buy',
                'entry_level': latest_compare['ltp'],
                'last_time': latest_compare["last_time"],
                'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_PE'] else nf_quantity,
                'entry': True,
                'sl_points': latest_compare['atr_PE']

            }

            if latest_compare['weekly_Options_PE'] not in tokens:
                token = token_map[latest_compare['weekly_Options_PE']]['token']
                requests.get(f'http://{token_server}:3000/subscribe/{token}')
                tokens.add(latest_compare['weekly_Options_PE'])

            channel.basic_publish(
                exchange='',
                routing_key='worker_1',
                body=json.dumps(document).encode()
            )

            symbol = document['instrument']
            print(f'[**] Message send to worker 1 to buy PE {symbol}')


###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition1 end                                                                                                                                               #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 2 Start                                                                                                                                                #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

        if (latest_compare['total_CE_short_covering'] > 0) and (latest_compare['total_PE_power'] > 0) and (trend_ce==UP_TREND or (slope_ce >= 30)):
            document = {
                'instrument': latest_compare['weekly_Options_CE'],
                'token': token_map[latest_compare['weekly_Options_CE']]['token'],
                'trade_direction': 'buy',
                'entry_level': latest_compare['ltp'],
                'last_time': latest_compare["last_time"],
                'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_CE'] else nf_quantity,
                'sl_points': latest_compare['atr_CE']

            }

            if latest_compare['weekly_Options_CE'] not in tokens:
                token = token_map[latest_compare['weekly_Options_CE']]['token']
                requests.get(f'http://{token_server}:3000/subscribe/{token}')
                tokens.add(latest_compare['weekly_Options_CE'])

            channel.basic_publish(
                exchange='',
                routing_key='worker_1',
                body=json.dumps(document).encode()
            )
            symbol = document['instrument']
            print(f'[**] Message send to worker 1 to buy CE {symbol}')

        if latest_compare['total_CE_unwinding'] < 0 and latest_compare['total_PE_power'] < 0 and (trend_pe==UP_TREND or (slope_pe >= 30)):
            document = {
                'instrument': latest_compare['weekly_Options_PE'],
                'token': token_map[latest_compare['weekly_Options_PE']]['token'],
                'trade_direction': 'buy',
                'entry_level': latest_compare['ltp'],
                'last_time': latest_compare["last_time"],
                'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_PE'] else nf_quantity,
                'sl_points': latest_compare['atr_PE']
            }

            if latest_compare['weekly_Options_PE'] not in tokens:
                token = token_map[latest_compare['weekly_Options_PE']]['token']
                requests.get(f'http://{token_server}:3000/subscribe/{token}')
                tokens.add(latest_compare['weekly_Options_PE'])

            channel.basic_publish(
                exchange='',
                routing_key='worker_1',
                body=json.dumps(document).encode()
            )
            symbol = document['instrument']
            print(f'[**] Message send to worker 1 to buy PE {symbol}')

###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 2 end                                                                                                                                               #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 3 Start    if condition 1,2,4,5 are not satisfying then condition 3                                                                                                                                            #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

        if (slope_ce) == 0 and (slope_pe == 0):

            document = latest_compare
            document['enter'] = True
            # document['token_CE'] = token_map[latest_compare['weekly_Options_CE']]
            # document['token_PE'] = token_map[latest_compare['weekly_Options_PE']]

            document['ticker_CE'] = latest_compare['weekly_Options_CE']
            document['ticker_PE'] = latest_compare['weekly_Options_PE']

            document['quantity_ce'] = 125 if "BANKNIFTY" in latest_compare['weekly_Options_CE'] else 375
            document['quantity_pe'] = 125 if "BANKNIFTY" in latest_compare['weekly_Options_PE'] else 375
            # document['instrument'] = latest_compare['weekly_Options_CE']
            # document['token'] = token_map[latest_compare['weekly_Options_CE']]['token']
            # 'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_CE'] else nf_quantity,

            channel.basic_publish(
                exchange='',
                routing_key='worker_3',
                body=json.dumps(document).encode()
            )
            print('[**] Message send to worker 3 to SELL BOTH PE and CE')
        elif (slope_ce) == 1 or (slope_pe == 1):
            document = latest_compare
            document['enter'] = False

            document['ticker_CE'] = latest_compare['weekly_Options_CE'],
            document['ticker_PE'] = latest_compare['weekly_Options_PE'],
            document['quantity_ce'] = 125 if "BANKNIFTY" in latest_compare['weekly_Options_CE'] else 375
            document['quantity_pe'] = 125 if "BANKNIFTY" in latest_compare['weekly_Options_PE'] else 375

            # document['instrument'] = latest_compare['weekly_Options_CE']
            # document['token'] = token_map[latest_compare['weekly_Options_CE']]['token']

            channel.basic_publish(
                exchange='',
                routing_key='worker_3',
                body=json.dumps(document).encode()
            )

###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 3 end                                                                                                                                               #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 4 Start                                                                                                                                                #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

        if latest_compare["total_PE_unwinding"] > 0 and latest_compare["total_CE_power"] > 0 and (trend_ce==UP_TREND or (slope_ce >= 30)):
            document = {
                'instrument': latest_compare['weekly_Options_CE'],
                'token': token_map[latest_compare['weekly_Options_CE']]['token'],
                'trade_direction': 'buy',
                'entry_level': latest_compare['ltp'],
                'last_time': latest_compare["last_time"],
                'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_CE'] else nf_quantity,
                'sl_points': latest_compare['atr_CE']


            }

            if latest_compare['weekly_Options_CE'] not in tokens:
                token = token_map[latest_compare['weekly_Options_CE']]['token']
                requests.get(f'http://{token_server}:3000/subscribe/{token}')
                tokens.add(latest_compare['weekly_Options_CE'])

            channel.basic_publish(
                exchange='',
                routing_key='worker_1',
                body=json.dumps(document).encode()
            )
            symbol = document['instrument']
            print(f'[**] Message send to worker 1 to buy CE {symbol}')

        if latest_compare["total_PE_short_covering"] < 0 and latest_compare["total_CE_power"] < 0 and (trend_pe==UP_TREND or(slope_pe >= 30)):
            document = {
                'instrument': latest_compare['weekly_Options_PE'],
                'token': token_map[latest_compare['weekly_Options_PE']]['token'],
                'trade_direction': 'buy',
                'entry_level': latest_compare['ltp'],
                'last_time': latest_compare["last_time"],
                'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_PE'] else nf_quantity,
                'sl_points': latest_compare['atr_PE']


            }

            if latest_compare['weekly_Options_PE'] not in tokens:
                token = token_map[latest_compare['weekly_Options_PE']]['token']
                requests.get(f'http://{token_server}:3000/subscribe/{token}')
                tokens.add(latest_compare['weekly_Options_PE'])

            channel.basic_publish(
                exchange='',
                routing_key='worker_1',
                body=json.dumps(document).encode()
            )
            symbol = document['instrument']
            print(f'[**] Message send to worker 1 to buy PE {symbol}')

###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 4 end                                                                                                                                               #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 5 Start                                                                                                                                                #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

        if latest_compare["total_CE_short_covering"] > 0 and latest_compare["total_CE_unwinding"] == 0 and (slope_ce == 1):
            document = {
                'instrument': latest_compare['weekly_Options_CE'],
                'token': token_map[latest_compare['weekly_Options_CE']]['token'],
                'trade_direction': 'buy',
                'entry_level': latest_compare['ltp'],
                'last_time': latest_compare["last_time"],
                'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_CE'] else nf_quantity,
                'sl_points': latest_compare['atr_CE']


            }

            if latest_compare['weekly_Options_CE'] not in tokens:
                token = token_map[latest_compare['weekly_Options_CE']]['token']
                requests.get(f'http://{token_server}:3000/subscribe/{token}')
                tokens.add(latest_compare['weekly_Options_CE'])

            channel.basic_publish(
                exchange='',
                routing_key='worker_1',
                body=json.dumps(document).encode()
            )
            symbol = document['instrument']
            print(f'[**] Message send to worker 1 to buy CE {symbol}')

        if latest_compare["total_CE_unwinding"] < 0 and latest_compare["total_CE_short_covering"] == 0 and (slope_pe == 1):
            document = {
                'instrument': latest_compare['weekly_Options_PE'],
                'token': token_map[latest_compare['weekly_Options_PE']]['token'],
                'trade_direction': 'buy',
                'entry_level': latest_compare['ltp'],
                'last_time': latest_compare["last_time"],
                'quantity': bf_quantity if 'BANKNIFTY' in latest_compare['weekly_Options_PE'] else nf_quantity,
                'sl_points': latest_compare['atr_PE']


            }

            if latest_compare['weekly_Options_PE'] not in tokens:
                token = token_map[latest_compare['weekly_Options_PE']]['token']
                requests.get(f'http://{token_server}:3000/subscribe/{token}')
                tokens.add(latest_compare['weekly_Options_PE'])

            channel.basic_publish(
                exchange='',
                routing_key='worker_1',
                body=json.dumps(document).encode()
            )
            symbol = document['instrument']
            print(f'[**] Message send to worker 1 to buy PE {symbol}')

###################################################################################################################################################################################
#                                                                                                                                                                           #
# Condition 5 end                                                                                                                                               #
#                                                                                                                                                                           #                                                                                                                                                                           #
#############################################################################################################################################################################

    channel.basic_consume(
        queue='compare', on_message_callback=callback, auto_ack=True)
    print('[*] Waiting for Message')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
