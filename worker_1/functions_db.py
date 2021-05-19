def get_key_token(zerodha_id, collection):
    document = collection.find_one({'ZERODHA ID': zerodha_id})
    return document['API Key'], document['ACCESS TOKEN']
