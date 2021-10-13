import pika, redis, time, os, requests, time

os.environ["TZ"] = "Asia/Kolkata"
time.tzset()

REDIS_SERVER = os.environ["REDIS_HOST"]
RABBIT_MQ_SERVER = os.environ["RABBIT_MQ_HOST"]
ZERODHA_SERVER = os.environ["ZERODHA_WORKER_HOST"]
ORDERS_SERVER = os.environ["ORDERS_HOST"]

# wait for all services
def wait_for_service():
    while True:
        try:
            p = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_MQ_SERVER)
            )
            r = redis.StrictRedis(host=REDIS_SERVER, port=6379, decode_responses=True)
            requests.get(f"http://{ZERODHA_SERVER}/")
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
# from services.index.worker_4 import main as main_wk4_index

# from services.index.worker_5 import main as main_wk5
# from services.index.worker_6 import main as main_wk6_index
from services.index.worker_7 import main as main_wk7_index

# from services.index.scraper import main as main_scraper_index
# from services.index.calculator import main as main_calculator_index
# from services.index.compare import main as main_compare_index

# for the stocks
# from services.stocks.calculator import main as main_calculator_stock
# from services.stocks.scraper import main as main_scraper_stock
# from services.stocks.worker_4 import main as main_wk4_stock
# from services.stocks.worker_6 import main as main_wk6_stock
# from services.stocks.worker_8 import main as main_wk8_stock
# from services.stocks.worker_9 import main as main_wk9_stock
# from services.stocks.worker_10 import main as main_wk10_stock
# from services.stocks.worker_11 import main as main_wk11_stock
from services.stocks.worker_sample import main as main_sample

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
        requests.get(f"http://{ORDERS_SERVER}/")
        break
    except:
        time.sleep(1)
        continue


# add service as {'name':'foo', 'script':'./a.out'}
# for the index trading
services_index = [
    # {'name':'scrapper', 'script':main_scraper_index, 'args':[]},
    # {'name':'calculator', 'script':main_calculator_index, 'args':[os.environ['EXPIRY_DATE_INDEX']]},
    # {'name':'compare', 'script':main_compare_index, 'args':[]},
    # {'name':'worker_5', 'script':main_wk5, 'args':[]},
    # {"name": "worker_4_index", "script": main_wk4_index, "args": []},
    # {"name": "worker_6_index", "script": main_wk6_index, "args": []},
    {"name": "worker_7_index", "script": main_wk7_index, "args": []}
]

# for stock trading
services_stocks = [
    # {'name':'scrapper', 'script':main_scraper_stock, 'args':[]},
    # {'name':'calculator', 'script':main_calculator_stock, 'args':[os.environ['EXPIRY_DATE_STOCK']]},
    # {'name':'compare', 'script':'', 'args':[]},
    # {'name':'worker_4_stock', 'script':main_wk4_stock, 'args':[]},
    # {"name": "worker_6_stock", "script": main_wk6_stock, "args": []},
    # {'name': 'worker_7_stock', 'script': main_wk7_stock, 'args': []},
    # {"name": "worker_8_stock", "script": main_wk8_stock, "args": []},
    # {"name": "worker_9_stock", "script": main_wk9_stock, "args": []},
    # {"name": "worker_10_stock", "script": main_wk10_stock, "args": []},
    # {"name": "worker_11_stock", "script": main_wk11_stock, "args": []},
    # {"name": "main_sample", "script": main_sample, "args": []}
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
