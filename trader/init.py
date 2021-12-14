import pika, redis, time, os, requests, time
from interfaces.constants import LIVE_DATA, RABBIT_MQ, REDIS

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
            p = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_MQ))
            r = redis.StrictRedis(host=REDIS, port=6379, decode_responses=True)
            p.close()
            r.close()
            break
        except:
            time.sleep(2)
            continue


print("waiting for services ...")
wait_for_service()
print("services are up running ...")


# import the object with aliase name Process
from threading import (
    Thread as Process,
)  # <-- change the type of process here to threading.Thread or multiprocess.Process
from services.live_data import main as live_data_main

# for the index
from services.index.oi_index import main as main_oi_index
from services.index.five_min import main as main_five_min
from services.index.fifteen_min import main as main_fifteen_min
from services.index.bull_bear import main as main_bull_bear

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


# for the index trading
services_index = [
    {"name": "bull_bear", "script": main_bull_bear, "args": []},
]

# for stock trading
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
