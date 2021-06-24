import redis
from kiteconnect import KiteConnect
from pymongo import MongoClient
import os
from functions_db import get_key_token
from streamer import ExitStreamer

from flask import Flask

mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')

zerodha_id = os.environ['USERNAME']
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])

kite = KiteConnect(api_key=api_key, access_token=access_token)

redis_host = 'redis_pubsub'
redis_port = 6379
r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

app = Flask(__name__)

streamers = [
    
]

@app.route('start_exit_streamer/<str:token>/<str:ticker>')
def start_exit_streamer(token, ticker):
    if ticker not in streamers:
        streamer = ExitStreamer(ticker, token, 'token_server', r)
        streamer.start()
        streamers.append(ticker)
        return 'started the streamer'
    else:
        return 'streamer already running'

if __name__ == '__main__':
    app.run(debug=True)