import redis, time, os, requests, time
from interfaces.constants import LIVE_DATA, REDIS

from utils.auth import get_key_token

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

# get the api key and access token and set it as the environment variable
api_key, access_token = get_key_token(os.environ["AUTH_TOKEN"])

# set the api key and the access token
os.environ["API_KEY"] = api_key
os.environ["ACCESS_TOKEN"] = access_token

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


from services.index.bullbear.bullbear import BullBear
from services.index.buyerseller.buyerseller import BuyerSellers
from services.index.costlycheap.costlycheap import CostlyCheap


services_index = [
    {"name": "bullbear", "script": BullBear(name="bullbear").start, "args": []},
    {
        "name": "buyerseller",
        "script": BuyerSellers(name="buyerseller").start,
        "args": [],
    },
    {
        "name": "costlycheap",
        "script": CostlyCheap(name="costlycheap").start,
        "args": [],
    },
]
services_stocks = []

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
