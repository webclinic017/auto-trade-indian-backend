import time, os
from entities.orders import OrderExecutorType
from utils.auth import get_key_token
from threading import (
    Thread as Process,
)
from kiteconnect import KiteConnect
import json
from services.index.bullbear.bullbear import BullBear as BullBearIndex
from services.stocks.bullbear.bullbear import BullBear as BullBearStocks
from services.stocks.bullbear.stockoption_buy import StockOptionBuying as StockOptionBuy

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

# get the api key and access token and set it as the environment variable
api_key, access_token = get_key_token(os.environ["AUTH_TOKEN"])

# set the api key and the access token
os.environ["API_KEY"] = api_key
os.environ["ACCESS_TOKEN"] = access_token


kite = KiteConnect(api_key, access_token)
instruments = kite.instruments()
token_map = {}
for instrument in instruments:
    token_map[instrument["tradingsymbol"]] = instrument


with open("/tmp/instrument_tokens.json", "w") as f:
    f.write(json.dumps(token_map, default=str))

with open("/tmp/instruments.json", "w") as f:
    f.write(json.dumps(instruments, default=str))


services = [
    {
        "name": "bullbear_index",
        "script": BullBearIndex(name="bullbear_index").start,
        "args": [],
    },
    
    # {
    #     "name": "bullbear_stock",
    #     "script": BullBearStocks(
    #         name="bullbear_stock", mode=OrderExecutorType.STRICT
    #     ).start,
    #     "args": [],
    # },
    
    {
        "name": "bullbear_stock",
        "script": BullBearStocks(
            name="bullbear_stock").start,
        "args": [],
    },
    
    {
        "name": "stockoption_buying",
        "script": StockOptionBuy(
            name="stockoption_buying").start,
        "args": [],
    },
]

processes = {}

# start each process from init.d as children
for service in services:
    processes[service["name"]] = Process(target=service["script"], args=service["args"])

print("starting services ...")

# start all processes
for process in processes:
    print(f"starting {process}")
    processes[process].start()


# wait for all process to complete
for process in processes:
    processes[process].join()
