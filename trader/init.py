# wait for all services
import pika, redis, time, os, requests

REDIS_SERVER = os.environ['REDIS_HOST']
RABBIT_MQ_SERVER = os.environ['RABBIT_MQ_HOST']
ZERODHA_SERVER = os.environ['ZERODHA_WORKER_HOST']
EXIT_SERVER = os.environ['EXIT_HOST']

def wait_for_service():
    
    # queues = [
    #     'trader',
    #     'compare',
    #     'worker_5',
    # ]
    
    while True:    
        try:
            p = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_MQ_SERVER))
            # channel = p.channel()
            
            # for queue in queues:
            #     channel.queue_declare(queue=queue)
            
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
from services.exit_worker import main as main_exit
from services.exit_worker_2 import main as main_exit2
from services.orders import main as main_orders
from services.worker_4 import main as main_wk4
from services.worker_5 import main as main_wk5
from services.scraper import main as main_scraper
from services.calculator import main as main_calculator

# orders service start
orders_process = {}
orders_services = [
    {'name':'orders_service', 'script':main_orders, 'args': []}
]

for service in orders_services:
    orders_process[service['name']] = Process(
        target=main_orders,
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
        requests.get(f"http://{EXIT_SERVER}/")
        break
    except:
        time.sleep(1)
        continue




# add service as {'name':'foo', 'script':'./a.out'}
services = [
    {'name':'exit_service', 'script': main_exit, 'args':[]},
    # {'name':'exit_service_2', 'script': main_exit2, 'args':[]},
    # {'name':'scrapper', 'script':main_scraper, 'args':[]},
    # {'name':'calculator', 'script':main_calculator, 'args':[os.environ['EXPIRY_DATE']]},
    # {'name':'compare', 'script':'', 'args':[]},
    # {'name':'worker_5', 'script':main_wk5, 'args':[]},
    {'name':'worker_4', 'script':main_wk4, 'args':[]},
    # {'name':'worker_6', 'script':'', 'args':[]},
    # {'name':'worker_8', 'script':'', 'args':[]},
]


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