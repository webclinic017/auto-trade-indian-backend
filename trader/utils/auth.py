import requests

URI = "https://auto.bittrade.space/users/profile/detail"


def get_key_token(zerodha_id):
    document = requests.get(
        URI, headers={"Authorization": f"Token {zerodha_id}"}
    ).json()
    return document["api_key"], document["access_token"]
