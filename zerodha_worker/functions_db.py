import requests

URI = "https://auto.bittrade.space/apicredential/"


def get_key_token(zerodha_id):
    document = requests.get(URI + zerodha_id).json()
    return document["api_key"], document["access_token"]
