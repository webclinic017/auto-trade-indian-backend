# wait for all services
import pika, redis, time, os, requests

REDIS_SERVER = os.environ['REDIS_HOST']
RABBIT_MQ_SERVER = os.environ['RABBIT_MQ_HOST']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
ORDERS_SERVER = os.environ['ORDERS_HOST']

def wait_for_service():
    while True:    
        try:
            p = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_MQ_SERVER))
            r = redis.StrictRedis(host=REDIS_SERVER, port=6379, decode_responses=True)
            requests.get(f"http://{ZERODHA_SERVER}/")
            p.close()
            r.close()
            break
        except:
            time.sleep(2)
            continue    

print('waiting for services ...')
wait_for_service()
print('services are up running ...')


# import the object with aliase name Process
from threading import Thread as Process # <-- change the type of process here to threading.Thread or multiprocess.Process
from services.exit_worker_2 import main as main_exit2
from services.live_data import main as live_data_main

# for the index
from services.index.worker_4 import main as main_wk4_index
# from services.index.worker_5 import main as main_wk5
from services.index.scraper import main as main_scraper_index
from services.index.calculator import main as main_calculator_index

# for the stocks
from services.stocks.calculator import main as main_calculator_stock
from services.stocks.scraper import main as main_scraper_stock
# from services.stocks.worker_4 import main as main_wk4_stock

# orders service start
orders_process = {}

orders_services = [
    # {'name':'orders_service', 'script':main_orders, 'args': []}
    {'name':'live_data_service', 'script':live_data_main, 'args':[]}
]

for service in orders_services:
    orders_process[service['name']] = Process(
        target=service['script'],
        args=service['args']
    )

for process in orders_process:
    orders_process[process].start()
    time.sleep(1)
    
for process in orders_process:
    orders_process[process].join()
# orders service stop

# wait for orders service to start
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
    {'name':'scrapper', 'script':main_scraper_index, 'args':[]},
    {'name':'calculator', 'script':main_calculator_index, 'args':[os.environ['EXPIRY_DATE']]},
    # {'name':'compare', 'script':'', 'args':[]},
    # {'name':'worker_5', 'script':main_wk5, 'args':[]},
    {'name':'worker_4_index', 'script':main_wk4_index, 'args':[]},
]

# for stock trading
services_stocks = [
    {'name':'scrapper', 'script':main_scraper_stock, 'args':[]},
    {'name':'calculator', 'script':main_calculator_stock, 'args':[os.environ['EXPIRY_DATE']]},
    # {'name':'compare', 'script':'', 'args':[]},
    # {'name':'worker_5', 'script':main_wk5, 'args':[]},
    # {'name':'worker_4_stock', 'script':main_wk4_stock, 'args':[]},
]

services = services_index + services_stocks

processes = {}

# start each process from init.d as children
for service in services:
    processes[service['name']] = Process(
        target=service['script'],
        args=service['args']
    )
print('starting services ...')

# start all processes
for process in processes:
    print(f'starting {process}')
    processes[process].start()
    time.sleep(1)

for process in processes:
    processes[process].join()