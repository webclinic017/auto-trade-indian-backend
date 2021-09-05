def insert_data(collection, data, ticker):
    collection.update_one(
        {'ticker': ticker},
        {'$push': {'data': data}, '$set': {'ticker': ticker}},
        True
    )

    doc = collection.aggregate([
        {"$match": {"ticker": ticker}},
        {"$project": {"count": {"$size": "$data"}}}
    ])

    for doc_ in doc:
        return doc_['count'] >= 2
