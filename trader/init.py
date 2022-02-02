import redis, time, os, requests, time
from interfaces.constants import LIVE_DATA, REDIS
from entities.orders import OrderExecutorType

from utils.auth import get_key_token

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

# get the api key and access token and set it as the environment variable
api_key, access_token = get_key_token(os.environ["AUTH_TOKEN"])

# set the api key and the access token
os.environ["API_KEY"] = api_key
os.environ["ACCESS_TOKEN"] = access_token

from kiteconnect import KiteConnect

kite = KiteConnect(api_key, access_token)
instruments = kite.instruments()
token_map = {}
for instrument in instruments:
    token_map[instrument["tradingsymbol"]] = instrument

import json

with open("/tmp/instrument_tokens.json", "w") as f:
    f.write(json.dumps(token_map, default=str))

with open("/tmp/instruments.json", "w") as f:
    f.write(json.dumps(instruments, default=str))


# wait for all services
def wait_for_service():
    while True:
        try:
            r = redis.StrictRedis(host=REDIS, port=6379, decode_responses=True)
            r.close()
            break
        except:
            time.sleep(1)
            continue


print("waiting for services ...")
wait_for_service()
print("services are up running ...")


# import the object with aliase name Process
from threading import (
    Thread as Process,
)
from services.live_data import main as live_data_main


# orders service start
orders_process = {}

orders_services = [
    {"name": "live_data_service", "script": live_data_main, "args": []},
]

for service in orders_services:
    orders_process[service["name"]] = Process(
        target=service["script"], args=service["args"]
    )

for process in orders_process:
    orders_process[process].start()
    time.sleep(1)


# # wait for orders service to start
while True:
    try:
        requests.get(LIVE_DATA)
        break
    except Exception as e:
        print(e)
        time.sleep(1)
        continue


from services.index.bullbear.bullbear import BullBear as BullBearIndex
from services.stocks.bullbear.bullbear import BullBear as BullBearStocks
from entities.ticker import TickerGenerator
import json

stock_tickers = TickerGenerator("", "", "", "", "").stocks_historical_prices()

with open("/tmp/stock_tickers.json", "w") as f:
    f.write(json.dumps(stock_tickers))

services_index = [
    # {
    #     "name": "bullbear_index",
    #     "script": BullBearIndex(name="bullbear_index").start,
    #     "args": [],
    # },
    # {
    #     "name": "buyerseller",
    #     "script": BuyerSellers(name="buyerseller").start,
    #     "args": [],
    # },
    # {
    #     "name": "costlycheap",
    #     "script": CostlyCheap(name="costlycheap").start,
    #     "args": [],
    # },
]
services_stocks = [
    # {
    #     "name": "bullbear_stock",
    #     "script": BullBearStocks(
    #         name="bullbear_stock", mode=OrderExecutorType.STRICT
    #     ).start,
    #     "args": [],
    # },
    # {
    #     "name": "historical_stocks",
    #     "script": HistoricalStocks(name="historical_stocks").start,
    #     "args": [],
    # }
]

services = services_index + services_stocks

processes = {}

# start each process from init.d as children
for service in services:
    processes[service["name"]] = Process(target=service["script"], args=service["args"])

print("starting services ...")

# start all processes
for process in processes:
    print(f"starting {process}")
    processes[process].start()
    time.sleep(1)


# wait for all process to complete
for process in processes:
    processes[process].join()

# wait for all process to comlete
for process in orders_process:
    orders_process[process].join()
