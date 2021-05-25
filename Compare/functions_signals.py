from collections import defaultdict
import datetime
import logging
import time
import kiteconnect
import talib as tb

from pymongo import MongoClient
from functions_db import get_key_token
import pandas as pd
import numpy as np
import statsmodels.api as sm


mongo = MongoClient('mongodb://db')
# take tokens from the online mongo db
mongo_clients = MongoClient(
    'mongodb+srv://jag:rtut12#$@cluster0.alwvk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
tokens_dict = mongo_clients['tokens']['tokens_map'].find_one()


zerodha_id = 'AL0644'
api_key, access_token = get_key_token(
    zerodha_id, mongo_clients['client_details']['clients'])
# access_token = "PSTIVkiKnMIYot42uTXnF9LbBKLqBeT4"
kite = kiteconnect.KiteConnect(api_key=api_key, access_token=access_token)


# out_2):
def call_evaluate(curr_Volume, curr_LTP, curr_OI, prev_Volume, prev_LTP, prev_OI, strike_price, *args, **kwargs):
    eval = None
    call_power = 0
    call_unwinding = 0
    call_shortcovering = 0

    logging.info(f'### Call Evaluate StrikePrice {strike_price} - Start ###')
    if (curr_OI > prev_OI) & (curr_Volume > prev_Volume) & (curr_LTP > prev_LTP):
        eval = "Long Build Up & can buy CE of " + \
            str(strike_price) + " & OI Change of " + str((curr_OI-prev_OI))
        call_power = (curr_OI-prev_OI)
        call_unwinding = 0
        call_shortcovering = 0
    if (curr_OI > prev_OI) & (curr_Volume < prev_Volume) & (curr_LTP > prev_LTP):
        eval = " second level Long Build Up & can hold or accumulate or add CE of" + \
            str(strike_price) + "& OI Change of " + str((curr_OI-prev_OI))
        call_power = (curr_OI-prev_OI)
        call_unwinding = 0
        call_shortcovering = 0

    if (curr_OI > prev_OI) & (curr_Volume > prev_Volume) & (curr_LTP < prev_LTP):
        eval = " Short Build Up at CE of " + \
            str(strike_price) + " & acting as Current Resistance & OI Change of " + \
            str((curr_OI-prev_OI))
        call_power = (prev_OI-curr_OI)
        call_unwinding = 0
        call_shortcovering = 0
    if (curr_OI > prev_OI) & (curr_Volume < prev_Volume) & (curr_LTP < prev_LTP):
        eval = " second level Short Build Up at CE of " + \
            str(strike_price) + " & still acting as Current Resistance & OI Change of " + \
            str((curr_OI-prev_OI))
        call_power = (prev_OI-curr_OI)
        call_unwinding = 0
        call_shortcovering = 0
    if (curr_OI < prev_OI) & (curr_Volume > prev_Volume) & (curr_LTP > prev_LTP):
        eval = " Short Covering at CE of" + \
            str(strike_price) + "Trend is Bull & OI Change of " + \
            str((curr_OI-prev_OI))
        #out_2['CE_short_covering'] += 1
        call_power = (prev_OI-curr_OI)
        call_unwinding = 0
        call_shortcovering = (prev_OI-curr_OI)
    if (curr_OI < prev_OI) & (curr_Volume < prev_Volume) & (curr_LTP > prev_LTP):
        eval = " second level Short Covering at CE of " + \
            str(strike_price) + " Trend Continues to be Bull & OI Change of " + \
            str((curr_OI-prev_OI))
        call_power = (prev_OI-curr_OI)
        call_unwinding = 0
        call_shortcovering = (prev_OI-curr_OI)
    if (curr_OI < prev_OI) & (curr_Volume < prev_Volume) & (curr_LTP < prev_LTP):
        eval = " Long Unwinding at CE of " + \
            str(strike_price) + " Trend may reverse from Bull to Bear & OI Change of " + \
            str((curr_OI-prev_OI))
        call_power = (curr_OI-prev_OI)
        #out_2['CE_long_unwinding'] += 1
        call_unwinding = (curr_OI-prev_OI)
        call_shortcovering = 0
    if (curr_OI < prev_OI) & (curr_Volume > prev_Volume) & (curr_LTP < prev_LTP):
        eval = " Second Level Long Unwinding at CE of " + \
            str(strike_price) + " Trend Reversal Bull to Bear Continues & OI Change of " + \
            str((curr_OI-prev_OI))
        call_power = (curr_OI-prev_OI)
        call_unwinding = (curr_OI-prev_OI)
        call_shortcovering = 0

    logging.info(f'### Call Evaluate Eval {eval} ###')
    logging.info(f'### Call Evaluate StrikePrice {strike_price} - Done ###')
    return eval, call_power, call_unwinding, call_shortcovering


# out_2):
def put_evaluate(curr_Volume, curr_LTP, curr_OI, prev_Volume, prev_LTP, prev_OI, strike_price, *args, **kwargs):
    eval = None
    put_power = 0
    put_unwinding = 0
    put_shortcovering = 0

    logging.info(f'### Put Evaluate StrikePrice {strike_price} - Start ###')
    if (curr_OI > prev_OI) & (curr_Volume > prev_Volume) & (curr_LTP > prev_LTP):
        #eval="Long Build Up & can buy PE of" + str(strike_price)
        eval = "Long Build Up by OI Change of " + \
            str((curr_OI-prev_OI)) + " & can buy PE of" + str(strike_price)
        put_power = (prev_OI-curr_OI)
        put_unwinding = 0
        put_shortcovering = 0
    if (curr_OI > prev_OI) & (curr_Volume < prev_Volume) & (curr_LTP > prev_LTP):
        eval = " second level Long Build Up by OI Change of " + \
            str((curr_OI-prev_OI)) + \
            " & can hold or accumulate or add PE of" + str(strike_price)
        put_power = (prev_OI-curr_OI)
        put_unwinding = 0
        put_shortcovering = 0
    if (curr_OI > prev_OI) & (curr_Volume > prev_Volume) & (curr_LTP < prev_LTP):
        eval = " Short Build Up at PE of " + \
            str(strike_price) + " & acting as Current Support & OI Change of " + \
            str((curr_OI-prev_OI))
        put_power = (curr_OI-prev_OI)
        put_unwinding = 0
        put_shortcovering = 0
    if (curr_OI > prev_OI) & (curr_Volume < prev_Volume) & (curr_LTP < prev_LTP):
        eval = " second level Short Build Up at PE of " + \
            str(strike_price) + "& still acting as Current Support & OI Change of " + \
            str((curr_OI-prev_OI))
        put_power = (curr_OI-prev_OI)
        put_unwinding = 0
        put_shortcovering = 0
    if (curr_OI < prev_OI) & (curr_Volume > prev_Volume) & (curr_LTP > prev_LTP):
        eval = " Short Covering at PE of" + \
            str(strike_price) + " Trend is Bear & OI Change of " + \
            str((curr_OI-prev_OI))
        put_power = (prev_OI-curr_OI)
        put_unwinding = 0
        put_shortcovering = (prev_OI-curr_OI)
        #out_2['PE_short_covering'] += 1
    if (curr_OI < prev_OI) & (curr_Volume < prev_Volume) & (curr_LTP > prev_LTP):
        eval = " second level Short Covering at PE of " + \
            str(strike_price) + "Trend Continues to be Bear & OI Change of " + \
            str((curr_OI-prev_OI))
        put_power = (prev_OI-curr_OI)
        put_unwinding = 0
        put_shortcovering = (prev_OI-curr_OI)
    if (curr_OI < prev_OI) & (curr_Volume < prev_Volume) & (curr_LTP < prev_LTP):
        eval = " Long Unwinding at PE of " + \
            str(strike_price) + " Trend may reverse from Bear to Bull & OI Change of " + \
            str((curr_OI-prev_OI))
        put_power = (prev_OI-curr_OI)
        put_unwinding = (prev_OI-curr_OI)
        put_shortcovering = 0
        #out_2['PE_long_unwinding'] += 1
    if (curr_OI < prev_OI) & (curr_Volume > prev_Volume) & (curr_LTP < prev_LTP):
        eval = " Second Level Long Unwinding at PE of " + \
            str(strike_price) + " Trend Reversal Bear to Bull Continues & OI Change of " + \
            str((curr_OI-prev_OI))
        put_power = (prev_OI-curr_OI)
        put_unwinding = (prev_OI-curr_OI)
        put_shortcovering = 0
    logging.info(f'### Put Evaluate Eval {eval} ###')
    logging.info(f'### Put Evaluate StrikePrice {strike_price} - Done ###')
    return eval, put_power, put_unwinding, put_shortcovering


def compareResult(prev, current, is_index=True):

    # out_2 = {
    #     'CE_long_unwinding':0,
    #     'CE_short_covering':0,
    #     'PE_long_unwinding':0,
    #     'PE_short_covering':0,
    #     'ATM_CE_long_winding':0,
    #     'ATM_CE_short_covering':0,
    #     'ATM_PE_long_winding':0,
    #     'ATM_PE_short_covering':0
    # }
    out_2 = defaultdict(int)

    curr_atm = current['atm']

    evaluation = defaultdict(int)
    # key_parent means keys of the current dictionary
    for key_parent in current:
        # first you are getting the key in current diction, if there is no key then it returns none, if you get
        # the key and that key is not a dictionary means if it is a strikeprice then consider that strike price
        if type(current.get(key_parent, None)) != dict:
            continue
        # those dictionaries that are having key as strike prices or CE, PE are called value_parent
        value_parent = current[key_parent]
        # print(value_parent)
        # for each item of the selected dictionaries
        for key, value in value_parent.items():
            # verifying if key value of current dictionary is having in previous dictionary
            prev_strikeprice_dict = prev[key_parent].get(key, None)
            # counter verifying whether extracted from previous is not a dicontionary
            if type(prev_strikeprice_dict) != dict:
                continue
            if key_parent == 'ATM_Strikes' and type(prev_strikeprice_dict) == dict:
                logging.info(
                    f"Checking key {key_parent} strikeprice {value['strikePrice']}")
                prev_strikeprice_dict = prev[key_parent].get(key, None)
            logging.info(f'Checking key {key_parent} strikeprice {key}')
            if type(prev_strikeprice_dict) == dict:
                curr_strikePrice = value['strikePrice']
                prev_lastPrice = prev[key_parent][key]['lastPrice']
                curr_lastPrice = value['lastPrice']

                prev_totalTraded = prev[key_parent][key]['totalTradedVolume']
                curr_totalTraded = value['totalTradedVolume']

                prev_openInterest = prev[key_parent][key]['openInterest']
                curr_openInterest = value['openInterest']

                if 'CE' in key_parent or 'CE' in key:
                    # print(key_parent)
                    # print(key)
                    result, power, unwinding, short_covering = call_evaluate(
                        curr_totalTraded, curr_lastPrice, curr_openInterest, prev_totalTraded, prev_lastPrice, prev_openInterest, curr_strikePrice, out_2)
                    if 'ATM' in key_parent or 'ATM' in key:
                        evaluation['atm_CE_unwinding_'+str(key)] = unwinding
                        evaluation['atm_CE_short_covering_' +
                                   str(key)] = short_covering
                        evaluation['atm_CE_Power_'+str(key)] = power
                        evaluation['total_atm_CE_unwinding'] += unwinding
                        evaluation['total_atm_CE_short_covering'] += short_covering
                        evaluation['total_atm_CE_power'] += power
                    else:
                        evaluation['CE_unwinding_'+str(key)] = unwinding
                        evaluation['CE_short_covering_' +
                                   str(key)] = short_covering
                        evaluation['CE_Power_'+str(key)] = power
                        evaluation['total_CE_unwinding'] += unwinding
                        evaluation['total_CE_short_covering'] += short_covering
                        evaluation['total_CE_power'] += power
                elif 'PE' in key_parent or 'PE' in key:
                    # print(key_parent)
                    # print(key)
                    result, power, unwinding, short_covering = put_evaluate(
                        curr_totalTraded, curr_lastPrice, curr_openInterest, prev_totalTraded, prev_lastPrice, prev_openInterest, curr_strikePrice, out_2)
                    if 'ATM' in key_parent or 'ATM' in key:
                        evaluation['atm_PE_unwinding_'+str(key)] = unwinding
                        evaluation['atm_PE_short_covering_' +
                                   str(key)] = short_covering
                        evaluation['atm_PE_Power_'+str(key)] = power
                        evaluation['total_atm_PE_unwinding'] += unwinding
                        evaluation['total_atm_PE_short_covering'] += short_covering
                        evaluation['total_atm_PE_power'] += power
                    else:
                        evaluation['PE_unwinding_'+str(key)] = unwinding
                        evaluation['PE_short_covering_' +
                                   str(key)] = short_covering
                        evaluation['PE_Power_'+str(key)] = power
                        evaluation['total_PE_unwinding'] += unwinding
                        evaluation['total_PE_short_covering'] += short_covering
                        evaluation['total_PE_power'] += power

                evaluation['total_power'] = evaluation['total_PE_power'] + evaluation['total_atm_PE_power'] + \
                    evaluation['total_CE_power'] + \
                    evaluation['total_atm_CE_power']
                evaluation['total_unwinding'] = evaluation['total_PE_unwinding']+evaluation['total_atm_PE_unwinding'] + \
                    evaluation['total_CE_unwinding'] + \
                    evaluation['total_atm_CE_unwinding']
                evaluation['total_short_covering'] = evaluation['total_PE_short_covering']+evaluation['total_atm_PE_short_covering'] + \
                    evaluation['total_CE_short_covering'] + \
                    evaluation['total_atm_CE_short_covering']

                unique_key = f"atm_{key}_{str(value['strikePrice'])}" if key == 'CE' or key == 'PE' else f'{key_parent}_{key}'
                logging.info(
                    '### Adding evaluation result to the dictionary ###')
                evaluation.update({unique_key: result})
                evaluation[unique_key+'_Power'] = power
                value['eval_result'] = result

                evaluation['total_power'] += power
    logging.info('### Adding evaluation dictionary to json file ###')
    for key in ['ATM_Strikes', 'CE_Stikes', 'PE_Stikes']:
        current.pop(key)

    current.update({**evaluation})

    latest_compare = current

    date_, month, year = latest_compare['date'].split('-')

    datetime_object = datetime.datetime.strptime(month, "%b")
    month_number = datetime_object.month
    year = time.strftime("%y", time.localtime())

    symbol = latest_compare['symbol']
    latest_compare['futures'] = symbol + year + month.upper() + 'FUT'

    if is_index:
        latest_compare['weekly_Options_CE'] = symbol + year + \
            str(month_number) + date_ + str(int(latest_compare['atm'])) + 'CE'
        latest_compare['weekly_Options_PE'] = symbol + year + \
            str(month_number) + date_ + str(int(latest_compare['atm'])) + 'PE'

    latest_compare['monthly_Options_CE'] = symbol + year + \
        month.upper() + str(int(latest_compare['atm'])) + 'CE'
    latest_compare['monthly_Options_PE'] = symbol + year + \
        month.upper() + str(int(latest_compare['atm'])) + 'PE'
    latest_compare = {**latest_compare}

    logging.info('### Compare - Done ###')

    return latest_compare


def get_atr(symbol):
    token = tokens_dict[symbol]['token']
    tday = datetime.date.today()
    fday = datetime.date.today() - datetime.timedelta(days=4)
    df = kite.historical_data(token, fday, tday, '5minute', False, False)
    df = pd.DataFrame(df)

    df['TR'] = df['high'] - df['low']
    df['atr'] = tb.ATR(df["high"], df["low"], df["close"], 14)

    df_atr = df.tail(1)

    atr = int(list(x for x in df_atr['atr'])[0])
    tr = int(list(x for x in df_atr['TR'])[0])
    atr = atr if atr != None else tr
    atr = atr+(0.1*atr)
    return atr


def ema_5813(symbol):
    token = tokens_dict[symbol]['token']
    tday = datetime.date.today()
    fday = datetime.date.today()-datetime.timedelta(days=4)
    df = kite.historical_data(token, fday, tday, '2minute', False, False)
    df = pd.DataFrame(df)
    df['ema_close5'] = tb.EMA(df["close"], 5)
    df['slope_5'] = (df['ema_close5']-df['ema_close5'].shift(1))/2
    df['ema_close8'] = tb.EMA(df["close"], 8)
    df['slope_8'] = (df['ema_close8']-df['ema_close8'].shift(1))/2
    df['ema_close13'] = tb.EMA(df["close"], 13)
    df['slope_13'] = (df['ema_close13']-df['ema_close13'].shift(1))/2
    df['ema_close20'] = tb.EMA(df["close"], 20)
    df['slope_20'] = (df['ema_close20']-df['ema_close20'].shift(1))/2

    df_ema_5813 = df.tail(1)
    ema_5 = int(list(x for x in df_ema_5813['ema_close5'])[0])
    ema_8 = int(list(x for x in df_ema_5813['ema_close8'])[0])
    ema_13 = int(list(x for x in df_ema_5813['ema_close13'])[0])
    ema_20 = int(list(x for x in df_ema_5813['ema_close20'])[0])

    slope_5 = (list(x for x in df_ema_5813['slope_5'])[0])
    slope_8 = (list(x for x in df_ema_5813['slope_8'])[0])
    slope_13 = (list(x for x in df_ema_5813['slope_13'])[0])
    slope_20 = (list(x for x in df_ema_5813['slope_20'])[0])
    cond1 = (ema_5 > ema_8) and (ema_8 > ema_13) and (ema_13 > ema_20)
    cond2 = (slope_5 >= 0.7) and (slope_8 >= 0.7) and (
        slope_13 >= 0.7) and (slope_20 >= 0.7)
    if cond1 and cond2:
        requirement = 1
    else:
        requirement = 0

    # requirement = cond1 and cond2
    print("ema for 581320 are" + ""+"" + symbol +
          str(ema_5), str(ema_8), str(ema_13), str(ema_20))
    print("slopes of 581320 are" + ""+"" + symbol + str(slope_5),
          str(slope_8), str(slope_13), str(slope_20))
    return requirement

def slope(symbol, n):
    "function to calculate the slope of regression line for n consecutive points on a plot"
    token = tokens_dict[symbol]['token']
    tday = datetime.date.today()
    fday = datetime.date.today()-datetime.timedelta(days=4)
    df = kite.historical_data(token, fday, tday, '2minute', False, False)
    df_slope=df.copy()
    df = df_slope.iloc[-1*n:,:]
    y = ((df_slope["open"] + df_slope["close"])/2).values
    x = np.array(range(n))
    y_scaled = (y - y.min())/(y.max() - y.min())
    x_scaled = (x - x.min())/(x.max() - x.min())
    x_scaled = sm.add_constant(x_scaled)
    model = sm.OLS(y_scaled,x_scaled)
    results = model.fit()
    slope = np.rad2deg(np.arctan(results.params[-1]))
    df["up"] = np.where(df["low"]>=df["low"].shift(1),1,0)
    df["dn"] = np.where(df["high"]<=df["high"].shift(1),1,0)
    if df["close"][-1] > df["open"][-1]:
        if df["up"][-1*n:].sum() >= 0.7*n:
            trend="uptrend"
    elif df["open"][-1] > df["close"][-1]:
        if df["dn"][-1*n:].sum() >= 0.7*n:
            trend= "downtrend"
    else:
        trend=None
    return slope,trend

