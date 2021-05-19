from kiteconnect import KiteConnect

def retrieve_existing_positions(api_key, access_token):
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token = access_token
    positions = kite.positions()
    return positions

def market_buy_order(kite: KiteConnect, tradingsymbol, exchange, quantity):
    order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchange,
                                tradingsymbol=tradingsymbol,
                                transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=quantity,
                                product=kite.PRODUCT_NRML, order_type=kite.ORDER_TYPE_MARKET,
                                price=None,
                                validity=kite.VALIDITY_DAY,
                                disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                                trailing_stoploss=None, tag=None)
    return order_id

def market_sell_order(kite: KiteConnect, tradingsymbol, exchange, quantity):
    order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchange,
                                tradingsymbol=tradingsymbol,
                                transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=quantity,
                                product=kite.PRODUCT_NRML, order_type=kite.ORDER_TYPE_MARKET,
                                price=None,
                                validity=kite.VALIDITY_DAY,
                                disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                                trailing_stoploss=None, tag=None)
    return order_id

def limit_sell_order(kite: KiteConnect, tradingsymbol, exchange, quantity):
    price = bid
    order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchange,
                                tradingsymbol=tradingsymbol,
                                transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=quantity,
                                product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_LIMIT,
                                price=price, validity=kite.VALIDITY_DAY,
                                disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                                trailing_stoploss=None, tag=None)
    return order_id

def limit_buy_order(kite: KiteConnect, tradingsymbol, exchange, quantity):
    price = offer
    order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=exchange,
                                tradingsymbol=tradingsymbol,
                                transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=quantity,
                                product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_LIMIT,
                                price=price, validity=kite.VALIDITY_DAY,
                                disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None,
                                trailing_stoploss=None, tag=None)
    return order_id

def get_bid_offer_price(tick: list):
    global bid, offer
    bid = tick[0]['depth']['buy'][1]['price']
    offer = tick[0]['depth']['sell'][1]['price']
    return bid, offer

def profit_or_loss_for_the_day(kite: KiteConnect):
    trades = kite.trades()
    profit = 0
    for trade in trades:
        if trade['transaction_type'] == 'BUY':
            profit = profit - trade["quantity"] * trade["average_price"]
        else:
            profit = profit + trade["quantity"] * trade["average_price"]
    return profit

def exit_all_positions(kite):
    print('exit all positions')
    positions = kite.positions()
    
    for pos in positions['net']:
        quantity = pos['quantity']
        trading = pos['tradingsymbol']
        ltp = pos['last_price']
        product = pos['product']
        exchange = pos['exchange']
        
        if quantity < 0:
            ACTION_TO_PERFORM = kite.TRANSACTION_TYPE_BUY
        elif quantity > 0:
            ACTION_TO_PERFORM = kite.TRANSACTION_TYPE_SELL
        else:
            ACTION_TO_PERFORM = None
        
        if ACTION_TO_PERFORM:
            kite.place_order(
                kite.VARIETY_REGULAR,
                exchange,
                trading_symbol,
                ACTION_TO_PERFORM,
                quantity,
                product,
                kite.ORDER_TYPE_MARKET,
                squareoff=None,
                stoploss=None
            )

def check_profit_loss(kite, captial):
    import time
    
    while True:
        sum = 0
        positions = kite.positions()
        for pos in positions['net']:
            pnl = pos['pnl']
            sum += pnl
        
        if abs(sum) >= captial/10:
            exit_all_positions(kite)
            return True
        
        time.sleep(4)

def get_ask_bid(kite, symbol):
    quote = kite.quote(symbol)
    first_buy_price = quote[symbol]['depth']['buy'][0]['price']
    first_buy_quantity = quote[symbol]['depth']['buy'][0]['quantity']
    
    first_sell_price = quote[symbol]['depth']['sell'][0]['price']
    first_sell_quantity = quote[symbol]['depth']['sell'][0]['price']
    
    return {
        'ask_price':0,
        'bid_price':0
    }