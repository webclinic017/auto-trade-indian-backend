import requests
import logging
from time import sleep


def fetch_data_from_api(url, sybmol=''):

    logging.info(f"Beginning Fetching Data from Api for symbol {sybmol}")
    logging.info(f"Targeted URL : {url}")

    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en,en-US;q=0.9,ar;q=0.8',
        # 'cache-control': 'max-age=0',
        # 'upgrade-insecure-requests': '1',
        'referer': 'https://www.nseindia.com/option-chain',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }
    with requests.Session() as session:
        main_page = 'https://www.nseindia.com/option-chain'
        logging.info('Loading Home Page')
        session.get(main_page, headers={'user-agent': 'Mozilla/5.0'})
        logging.info('Loading Json Response')
        resp_cont = session.get(url, headers=headers)
        if resp_cont.status_code == 401:  # Resource not found
            logging.info('Resource not found')
            logging.info('Sleeping 2 seconds before retying')
            sleep(2)
            return fetch_data_from_api(url=url, sybmol=sybmol)
        logging.info('Valid Json Response')

        return resp_cont.json()
