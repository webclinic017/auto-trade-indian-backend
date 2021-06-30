from collections import defaultdict
import datetime
import logging
import time


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
    out_2 = defaultdict(int)

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