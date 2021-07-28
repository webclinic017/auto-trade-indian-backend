import time, os
# imort the object with aliase name Process
from threading import Thread as Process # <-- change the type of process here to threading.Thread or multiprocess.Process
from services.exit_worker import main as main_exit
from services.worker_4 import main as main_wk4
from services.worker_5 import main as main_wk5
from services.scraper import main as main_scraper
from services.calculator import main as main_calculator

# add service as {'name':'foo', 'script':'./a.out'}
services = [
    {'name':'exit_service', 'script': main_exit, 'args':[]},
    {'name':'scrapper', 'script':main_scraper, 'args':[]},
    {'name':'calculator', 'script':main_calculator, 'args':[os.environ['EXPIRY_DATE']]},
    {'name':'compare', 'script':'', 'args':[]},
    {'name':'worker_5', 'script':main_wk5, 'args':[]},
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