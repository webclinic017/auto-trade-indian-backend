from kiteconnect import KiteConnect

def retrieve_existing_positions(api_key, access_token):
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token = access_token
    positions = kite.positions()
    return positions

def market_buy_order(kite: KiteConnect, tradingsymbol, exchange, quantity, tag=None):
    order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchange,
                                tradingsymbol=tradingsymbol,
                                transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=quantity,
                                product=kite.PRODUCT_NRML, order_type=kite.ORDER_TYPE_MARKET,
                                price=None,
                                validity=kite.VALIDITY_DAY,
                                disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                                trailing_stoploss=None, tag=tag)
    return order_id

def market_sell_order(kite: KiteConnect, tradingsymbol, exchange, quantity, tag=None):
    order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchange,
                                tradingsymbol=tradingsymbol,
                                transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=quantity,
                                product=kite.PRODUCT_NRML, order_type=kite.ORDER_TYPE_MARKET,
                                price=None,
                                validity=kite.VALIDITY_DAY,
                                disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                                trailing_stoploss=None, tag=tag)
    return order_id

def limit_sell_order(kite: KiteConnect, tradingsymbol, exchange, quantity, price, tag=None):
    order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchange,
                                tradingsymbol=tradingsymbol,
                                transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=quantity,
                                product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_LIMIT,
                                price=price, validity=kite.VALIDITY_DAY,
                                disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                                trailing_stoploss=None, tag=tag)
    return order_id

def limit_buy_order(kite: KiteConnect, tradingsymbol, exchange, quantity, price, tag=None):
    order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchange,
                                tradingsymbol=tradingsymbol,
                                transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=quantity,
                                product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_LIMIT,
                                price=price, validity=kite.VALIDITY_DAY,
                                disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                                trailing_stoploss=None, tag=tag)
    return order_id