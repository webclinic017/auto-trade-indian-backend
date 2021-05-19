def insert_data(collection, data, ticker):
    collection.update_one(
        {'ticker': ticker},
        {'$push': {'data': data}, '$set': {'ticker': ticker}},
        True
    )


def get_key_token(zerodha_id, collection):
    document = collection.find_one({'ZERODHA ID': zerodha_id})
    # print(document)
    return document['API Key'], document['ACCESS TOKEN']
