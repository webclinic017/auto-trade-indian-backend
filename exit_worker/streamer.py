import websocket
import redis
import json

class ExitStreamer:
    def __init__(self, ticker, token, host, r:redis.StrictRedis):
        self.ticker = ticker
        self.token = token
        self.uri = f'ws://{host}/ws/ticker/{self.token}'
        self.ws = websocket.WebSocketApp(self.uri, on_message=self.on_message)
        
       

        self.r = r
    
    def on_message(self, ws, message):
        print(message)
        ticker = json.loads(message)
        data = self.r.get(f'{self.ticker}_ORDERS')
        
        if not bool(data):
            data = '[]'
        
        orders = json.loads(data)
        
        ltp = ticker['last_price']
        
        total_investment = 0
        total_quantity = 0
        
        for order in orders:
            total_quantity += order['filled_quantity']
            total_investment += order['filled_quantity'] * order['average_price']
        
        average_price = total_investment / total_quantity
        
        profit = (average_price / ltp) * 100
        print(profit)
        
        if profit >= 5:
            print(f'EXITING TICKER {self.token}')
            self.r.delete(f'{self.ticker}_ORDERS')
        
        
    
    def start(self):
        print(f'[**] EXIT STREAMER STARTED FOR {self.ticker}')
        self.ws.run_forever()
