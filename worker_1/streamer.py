import websocket
from kiteconnect import KiteConnect
from zerodha_functions import *
import json
import math
import threading


class Streamer:
    def __init__(self, token, host, api_key, access_token, document):
        self.token = token
        self.document = document
        self.entry_price = -math.inf
        self.high_price = -math.inf

        self.uri = f'ws://{host}/ws/ticker/{self.token}'
        self.ws = websocket.WebSocketApp(self.uri, on_message=self.on_message)
        self.kite = KiteConnect(api_key, access_token=access_token)

        self.should_stream = True
        self.should_trade = True

        self.mode = 'entry'  # the mode can be entry or exit
        self.is_first = True
        self.entry_lock = threading.Lock()
        self.exit_lock = threading.Lock()

        print(f'[***] STREAMER STARTED FOR {self.token} [***]')

    def perform_entry(self, cmp):
        if not self.entry_lock.locked():
            self.entry_lock.acquire()

            if cmp > self.entry_price and self.should_trade and self.mode == 'entry':
                market_buy_order(
                    self.kite,
                    self.document['instrument'],
                    self.kite.EXCHANGE_NFO,
                    self.document['quantity']
                )
                print('[***] ORDER PLACED [***]')
                self.mode = 'exit'

            self.entry_lock.release()

    def perform_exit(self, cmp):
        if not self.exit_lock.locked():
            self.exit_lock.acquire()

            delta = self.high_price - self.document['sl_points']
            positions = self.kite.positions()
            is_present = False

            for position in positions['day']:
                if self.document['instrument'] == position['tradingsymbol']:
                    is_present = True
                    break

            if is_present:

                if self.document['quantity'] > 0 and cmp <= delta and self.should_trade and self.mode == 'exit':
                    market_sell_order(
                        self.kite,
                        self.document['instrument'],
                        self.kite.EXCHANGE_NFO,
                        self.document['quantity']
                    )
                    print('[***] ORDER EXITED [***]')
                    self.mode = 'entry'
                    self.should_stream = False
                    self.should_trade = False

                elif cmp >= (self.entry_price + 1*self.document['sl_points']) and self.document['quantity'] > 0 and self.should_trade and self.mode == 'exit':
                    market_sell_order(
                        self.kite,
                        self.document['instrument'],
                        self.kite.EXCHANGE_NFO,
                        self.document['quantity']
                    )
                    print('[***] ORDER EXITED [***]')
                    self.mode = 'entry'
                    self.should_stream = False
                    self.should_trade = True

            self.exit_lock.release()

    def on_message(self, ws, message):
        ticker = json.loads(message)
        # print(ticker)
        if self.should_stream:
            if self.is_first:
                self.entry_price = ticker['last_price']
                self.is_first = False
            else:
                self.high_price = max(
                    self.entry_price, ticker['last_price'], self.high_price)
            if self.mode == 'entry':
                t_entry = threading.Thread(target=self.perform_entry, args=[
                                           ticker['last_price']])
                t_entry.start()
            elif self.mode == 'exit':
                t_exit = threading.Thread(target=self.perform_exit, args=[
                                          ticker['last_price']])
                t_exit.start()

    def start(self):
        self.ws.run_forever()
