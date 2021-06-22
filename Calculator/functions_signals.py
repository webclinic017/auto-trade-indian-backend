import logging
import operator
import datetime, time

def filterd_dates(res, filter_key='expiryDate'):
    logging.info(f'Filtering by {filter_key} - Start')
    expiry_data_dict = {}
    for record in res['records']['data']:
        expiry_data_li = []
        if expiry_data_dict.get(record[filter_key], None):
            expiry_data_li = expiry_data_dict[record[filter_key]]
            expiry_data_li.append(record)
        else:
            expiry_data_li.append(record)
        expiry_data_dict[record[filter_key]] = expiry_data_li

    logging.info(f'Filtering by {filter_key} - Done')
    return expiry_data_dict


def filterd_strike_price(date_filterd_dict, last_trade_price, date):
    logging.info(f'Filtering by date: {date} ltp : {last_trade_price} - Start')
    big_ten, small_ten = [], []
    for item in date_filterd_dict.get(date, ''):
        if item.get('PE', None):
            if operator.lt(item['strikePrice'], last_trade_price):
                small_ten.append(item['strikePrice'])
        if item.get('CE', None):
            if operator.gt(item['strikePrice'], last_trade_price):
                big_ten.append(item['strikePrice'])

    filterd_strikes = {'CE': big_ten[:10],
                       'PE': small_ten[-1::-1][:10]}
    logging.info(f'Filtering by date: {date} ltp : {last_trade_price} - Done')
    return filterd_strikes


def calculate_at_the_money(filterd_strikes, ltp):
    logging.info(f'calculating at the money - Start')
    is_ce = False
    atm = 0
    for plus_strike1, minus_strike1 in zip(*filterd_strikes.values()):
        diff_points = abs((minus_strike1-plus_strike1))
        if (ltp-minus_strike1) > (plus_strike1-ltp):
            atm = plus_strike1
            is_ce = True
        if (ltp-minus_strike1) < (plus_strike1-ltp):
            atm = minus_strike1
        if (ltp-minus_strike1) == (plus_strike1-ltp) and (ltp-minus_strike1) < diff_points:
            atm = minus_strike1
        if (ltp-minus_strike1) == (plus_strike1-ltp) and (ltp-minus_strike1) == diff_points:
            atm = ltp
        logging.info(
            f'minus_strike1:{minus_strike1} , atm : {atm} ,plus_strike1 : {plus_strike1},ltp : {ltp}')
        break
    logging.info(f'calculating at the money - Done')
    filterd_strikes.update({'atm': atm, 'ltp': ltp, 'is_ce': is_ce})


def parsing_data(filtered_data, filter_date, raw_data, symbol):
    logging.info('Extracting Data from Json object')
    # getting the dictionary of filter_date(required expiry date) from date wise dictionary
    data = filtered_data.get(filter_date, None)
    if data:
        ltp = raw_data['records']['underlyingValue']
        last_time = raw_data['records']['timestamp']
        call_totaloi = raw_data['filtered']['CE']['totOI']
        call_totalvolume = raw_data['filtered']['CE']['totVol']
        put_totaloi = raw_data['filtered']['PE']['totOI']
        put_totalvolume = raw_data['filtered']['PE']['totVol']

        plus_strike1, plus_strike2, plus_strike3, plus_strike4, plus_strike5, plus_strike6, plus_strike7, call_maxoi, call_2ndmaxoi, call_maxoichng, call_2ndmaxoichng, call_maxvol, call_2ndmaxvol, call_maxiv, call_2ndmaxiv = create_puls_and_minus(
            data, 'CE', ltp)

        minus_strike1, minus_strike2, minus_strike3, minus_strike4, minus_strike5, minus_strike6, minus_strike7, put_maxoi, put_2ndmaxoi, put_maxoichng, put_2ndmaxoichng, put_maxvol, put_2ndmaxvol, put_maxiv, put_2ndmaxiv = create_puls_and_minus(
            data, 'PE', ltp)

        diff_points = abs((minus_strike1-plus_strike1))

        atm = 0
        if (ltp-minus_strike1) > (plus_strike1-ltp):
            atm = plus_strike1
        if (ltp-minus_strike1) < (plus_strike1-ltp):
            atm = minus_strike1
        if (ltp-minus_strike1) == (plus_strike1-ltp) and (ltp-minus_strike1) < diff_points:
            atm = minus_strike1
        if (ltp-minus_strike1) == (plus_strike1-ltp) and (ltp-minus_strike1) == diff_points:
            atm = ltp

        pcr_oi = put_totaloi/call_totaloi
        pcr_volume = put_totalvolume/call_totalvolume

        if (pcr_oi > 1):
            # oi_trend="bull"
            oi_trend = 20
        if (pcr_oi < 1):
            # oi_trend='bear'
            oi_trend = -20

        if (pcr_volume > 1):
            # volume_trend="bull"
            volume_trend = 20
        if (pcr_volume < 1):
            # volume_trend='bear'
            volume_trend = -20

        if atm == minus_strike1:
            minus_strike1 = minus_strike2
            minus_strike2 = minus_strike3
            minus_strike3 = minus_strike4
            minus_strike4 = minus_strike5
            minus_strike5 = minus_strike6
            minus_strike6 = minus_strike7

        if atm == plus_strike1:
            plus_strike1 = plus_strike2
            plus_strike2 = plus_strike3
            plus_strike3 = plus_strike4
            plus_strike4 = plus_strike5
            plus_strike5 = plus_strike6
            plus_strike6 = plus_strike7

        logging.info(
            f'Making Dictionary dic_plus_strike_CE and dic_minus_strike_PE -Start')
        for item in (data):
            if item.get('CE', None):
                if item['strikePrice'] == atm:
                    dic_atm_CE = create_dict(item, 'CE')
                if item['strikePrice'] == plus_strike1:
                    dic_plus_strike1_CE = create_dict(item, 'CE')
            if item.get('PE', None):
                if item['strikePrice'] == atm:
                    dic_atm_PE = create_dict(item, 'PE')
                if item['strikePrice'] == minus_strike1:
                    dic_minus_strike1_PE = create_dict(item, 'PE')

        logging.info(
            f'Making Dictionary dic_plus_strike_CE and dic_minus_strike_PE -Done')

        logging.info(
            f'Setting StrikePrice based on openInterest and totalTradedVolume - Start')
        for item in (data):
            if item.get('CE', None):
                if item['CE']['openInterest'] == call_maxoi:
                    call_maxoi_StrikePrice = item['strikePrice']
                if item['CE']['openInterest'] == call_2ndmaxoi:
                    call_2ndmaxoi_StrikePrice = item['strikePrice']

                if item['CE']['changeinOpenInterest'] == call_maxoichng:
                    call_maxoichng_StrikePrice = item['strikePrice']
                if item['CE']['changeinOpenInterest'] == call_2ndmaxoichng:
                    call_2ndmaxoichng_StrikePrice = item['strikePrice']

                if item['CE']['totalTradedVolume'] == call_maxvol:
                    call_maxvol_StrikePrice = item['strikePrice']
                if item['CE']['totalTradedVolume'] == call_2ndmaxvol:
                    call_2ndmaxvol_StrikePrice = item['strikePrice']

                if item['CE']['impliedVolatility'] == call_maxiv:
                    call_maxiv_StrikePrice = item['strikePrice']
                if item['CE']['impliedVolatility'] == call_2ndmaxiv:
                    call_2ndmaxiv_StrikePrice = item['strikePrice']

            if item.get('PE', None):
                if item['PE']['openInterest'] == put_maxoi:
                    put_maxoi_StrikePrice = item['strikePrice']
                if item['PE']['openInterest'] == put_2ndmaxoi:
                    put_2ndmaxoi_StrikePrice = item['strikePrice']

                if item['PE']['changeinOpenInterest'] == put_maxoichng:
                    put_maxoichng_StrikePrice = item['strikePrice']
                if item['PE']['changeinOpenInterest'] == put_2ndmaxoichng:
                    put_2ndmaxoichng_StrikePrice = item['strikePrice']

                if item['PE']['totalTradedVolume'] == put_maxvol:
                    put_maxvol_StrikePrice = item['strikePrice']
                if item['PE']['totalTradedVolume'] == put_2ndmaxvol:
                    put_2ndmaxvol_StrikePrice = item['strikePrice']

                if item['PE']['impliedVolatility'] == put_maxiv:
                    put_maxiv_StrikePrice = item['strikePrice']
                if item['PE']['impliedVolatility'] == put_2ndmaxiv:
                    put_2ndmaxiv_StrikePrice = item['strikePrice']

        logging.info(
            f'Setting StrikePrice based on openInterest and totalTradedVolume - Done')

        imm_resistance = 0
        next_resistance = 0
        imm_support = 0
        next_support = 0

        logging.info(
            'Setting imm_resistance_oi and next_resistance_oi - Start')
        if call_maxoi_StrikePrice == call_maxoichng_StrikePrice:
            imm_resistance = call_maxoi_StrikePrice
            next_resistance = call_maxoi_StrikePrice
        elif call_maxoi_StrikePrice > call_maxoichng_StrikePrice:
            imm_resistance = call_maxoichng_StrikePrice
            next_resistance = call_maxoi_StrikePrice
        elif call_maxoichng_StrikePrice > call_maxoi_StrikePrice:
            imm_resistance = call_maxoi_StrikePrice
            next_resistance = call_maxoichng_StrikePrice

        if put_maxoi_StrikePrice == put_maxoichng_StrikePrice:
            imm_support = put_maxoi_StrikePrice
            next_support = put_maxoi_StrikePrice
        elif put_maxoi_StrikePrice > put_maxoichng_StrikePrice:
            imm_support = put_maxoi_StrikePrice
            next_support = put_maxoichng_StrikePrice
        elif put_maxoichng_StrikePrice > put_maxoi_StrikePrice:
            imm_support = put_maxoichng_StrikePrice
            next_support = put_maxoi_StrikePrice

        logging.info('Setting imm_resistance_oi and next_resistance_oi - Done')
        oi_power = 0
        oiChng_power = 0
        if (call_maxoi > put_maxoi):
            # oi_power='bear'
            oi_power = -15
        if (call_maxoi < put_maxoi):
            # oi_power='bull'
            oi_power = 15
        if (call_maxoichng > put_maxoichng):
            oiChng_power = 'bear'
        if (call_maxoichng < put_maxoichng):
            oiChng_power = 'bull'

        imm_resistance_oi = 0
        next_resistance_oi = 0
        imm_support_oi = 0
        next_support_oi = 0

        logging.info(
            'Checking imm_resistance_oi and next_resistance_oi - Start')
        for item in (data):
            if item.get('CE', None):
                if item['CE']['strikePrice'] == imm_resistance:
                    imm_resistance_oi = item['CE']['openInterest']
                if item['CE']['strikePrice'] == next_resistance:
                    next_resistance_oi = item['CE']['openInterest']
            if item.get('PE', None):
                if item['PE']['strikePrice'] == next_support:
                    next_support_oi = item['PE']['openInterest']
                if item['PE']['strikePrice'] == imm_support:
                    imm_support_oi = item['PE']['openInterest']

        logging.info(
            'Checking imm_resistance_oi and next_resistance_oi - Done')
        imm_trend = 0
        next_trend = 0
        if (imm_resistance_oi > imm_support_oi):
            # imm_trend='bear'
            imm_trend = -10
        if (imm_resistance_oi < imm_support_oi):
            # imm_trend='bull'
            imm_trend = 10

        if (next_resistance_oi > next_support_oi):
            # next_trend='bear'
            next_trend = -10
        if (next_resistance_oi < next_support_oi):
            # next_trend='bull'
            next_trend = 10

        upper_circuit = ltp+dic_atm_CE['lastPrice']+dic_atm_PE['lastPrice']
        lower_circuit = ltp-(dic_atm_CE['lastPrice']+dic_atm_PE['lastPrice'])

        costly_option = 0
        if ((ltp+diff_points)*dic_plus_strike1_CE['lastPrice']/plus_strike1) > ((ltp-diff_points)*dic_minus_strike1_PE['lastPrice']/minus_strike1):
            # costly_option='Call options are costly '
            costly_option = 'bull'
        if ((ltp+diff_points)*dic_plus_strike1_CE['lastPrice']/plus_strike1) < ((ltp-diff_points)*dic_minus_strike1_PE['lastPrice']/minus_strike1):
            # costly_option='Put options are costly'
            costly_option = 'bear'

        logging.info('Constructing the final output - Start')

        Overall_trend = (imm_trend) + (next_trend) + \
            (oi_power) + (volume_trend)+(oi_trend)
        data = {
            'symbol': symbol,
            'last_time': last_time,
            'ltp': ltp,
            'overall_trend': Overall_trend,
            'expiry': filter_date,
            'pcr_oi': pcr_oi,
            'pcr_volume': pcr_volume,
            'imm_trend': imm_trend,
            'next_trend': next_trend,
            'oi_power': oi_power,
            'oiChng_power': oiChng_power,
            'oi_trend': oi_trend,
            'vol_trend': volume_trend,
            'imm_resistance': imm_resistance,
            'next_resistance': next_resistance,
            'imm_support': imm_support,
            'next_support': next_support,
            'costly_option': costly_option,
            'upper_circuit': upper_circuit,
            'lower_circuit': lower_circuit,
            'call_maxoi_StrikePrice': call_maxoi_StrikePrice,
            'call_2ndmaxoi_StrikePrice': call_2ndmaxoi_StrikePrice,
            'call_maxoi_StrikePricel': call_maxoi_StrikePrice,
            'call_maxoichng_StrikePrice': call_maxoichng_StrikePrice,
            'call_2ndmaxoichng_StrikePrice': call_2ndmaxoichng_StrikePrice,
            'call_maxvol_StrikePrice': call_maxvol_StrikePrice,
            'call_2ndmaxvol_StrikePrice': call_2ndmaxvol_StrikePrice,
            'call_maxiv_StrikePrice': call_maxiv_StrikePrice,
            'call_2ndmaxiv_StrikePrice': call_2ndmaxiv_StrikePrice,
            'put_maxoi_StrikePrice': put_maxoi_StrikePrice,
            'put_2ndmaxoi_StrikePrice': put_2ndmaxoi_StrikePrice,
            'put_maxoi_StrikePricel': put_maxoi_StrikePrice,
            'put_maxoichng_StrikePrice': put_maxoichng_StrikePrice,
            'put_2ndmaxoichng_StrikePrice': put_2ndmaxoichng_StrikePrice,
            'put_maxvol_StrikePrice': put_maxvol_StrikePrice,
            'put_2ndmaxvol_StrikePrice': put_2ndmaxvol_StrikePrice,
            'put_maxiv_StrikePrice': put_maxiv_StrikePrice,
            'putl_2ndmaxiv_StrikePrice': put_2ndmaxiv_StrikePrice,
        }

        logging.info('Constructing the final output - Done')
        return data


def constract_final_output(filtered_data_dict, filterd_strikes, date, giant_dict):
    logging.info(f'constracting final_output - Start')
    date_dict = filtered_data_dict.get(date, None)
    CE_strikes, PE_strikes = filterd_strikes['CE'], filterd_strikes['PE']
    ltp, atm, is_ce = filterd_strikes['ltp'], filterd_strikes['atm'], filterd_strikes['is_ce']
    new_ce = {str(item['CE']['strikePrice']): item['CE']
              for item in date_dict if item['strikePrice'] in CE_strikes}
    new_pe = {str(item['PE']['strikePrice']): item['PE']
              for item in date_dict if item['strikePrice'] in PE_strikes}
    new_atm = [item for item in date_dict if item['strikePrice'] == atm][0]

    list_to_compare = new_ce
    if not is_ce:
        list_to_compare = new_pe
    for strikePrice in list_to_compare:
        if strikePrice == atm:
            list_to_compare[strikePrice].update({'is_atm': True})
        else:
            list_to_compare[strikePrice].update({'is_atm': False})

    logging.info(f'constracting final_output - Done')
    pre_final_dict = {
        'CE_Stikes': new_ce,
        'PE_Stikes': new_pe,
        'ATM_Strikes': new_atm,
        'ltp': ltp,
        'atm': atm,
        'date': date
    }
    pre_final_dict.update(giant_dict)
    return pre_final_dict


def create_puls_and_minus(parent_dict, key_to_add, ltp):
    logging.info(f'Creating Plus and Minus Values Currently : {key_to_add}')
    lst_call, lst_calloi, lst_calloichng, lst_callvol, lst_calliv = [], [], [], [], []
    comparision_operator = operator.gt
    if key_to_add == 'PE':
        comparision_operator = operator.lt
    for item in parent_dict:
        if comparision_operator(item['strikePrice'], ltp) and item.get(key_to_add, None):
            lst_call.append(item['strikePrice'])
            lst_calloi.append(item[key_to_add]['openInterest'])
            lst_calloichng.append(item[key_to_add]['changeinOpenInterest'])
            lst_callvol.append(item[key_to_add]['totalTradedVolume'])
            lst_calliv.append(item[key_to_add]['impliedVolatility'])
    plus_strike1, plus_strike2, plus_strike3, plus_strike4, plus_strike5, plus_strike6, plus_strike7 = lst_call[
        0:7]

    if key_to_add == 'PE':
        rev = lst_call[:6:-1][:8]
        plus_strike1, plus_strike2, plus_strike3, plus_strike4, plus_strike5, plus_strike6, plus_strike7 = rev[
            0:7]

    lst_calloi.sort()
    lst_calloichng.sort()
    lst_callvol.sort()
    lst_calliv.sort()

    call_maxoi, call_2ndmaxoi = lst_calloi[-1], lst_calloi[-2]
    call_maxoichng, call_2ndmaxoichng = lst_calloichng[-1], lst_calloichng[-2]
    call_maxvol, call_2ndmaxvol = lst_callvol[-1], lst_callvol[-2]
    call_maxiv, call_2ndmaxiv = lst_calliv[-1], lst_calliv[-2]

    return plus_strike1, plus_strike2, plus_strike3, plus_strike4, plus_strike5, plus_strike6, plus_strike7, call_maxoi, call_2ndmaxoi, call_maxoichng, call_2ndmaxoichng, call_maxvol, call_2ndmaxvol, call_maxiv, call_2ndmaxiv


def create_dict(parent_dict, key_to_add, keys_to_remove=['expiryDate', 'identifier', 'underlying']):
    new_dict = parent_dict[key_to_add]
    for key_to_remove in keys_to_remove:
        new_dict.pop(key_to_remove, None)
    return new_dict


def find_all_tickers(data):
    date_, month, year = data['date'].split('-')
    symbol = data['symbol']
    
    for key in ['CE_Stikes', 'PE_Stikes']:
        for strike in data[key]:
            obj = data[key][strike]
            
            datetime_object = datetime.datetime.strptime(month, "%b")
            month_number = datetime_object.month
            year = time.strftime("%y", time.localtime())
            obj['symbol'] = symbol
            obj['futures'] = symbol + year + month.upper() + 'FUT'
            obj['weekly_Options_CE'] = symbol + year + \
            str(month_number) + date_ + strike + 'CE'
            obj['weekly_Options_PE'] = symbol + year + \
                str(month_number) + date_ + strike + 'PE'
            obj['monthly_Options_CE'] = symbol + year + \
                month.upper() + strike + 'CE'
            obj['monthly_Options_PE'] = symbol + year + \
                month.upper() + strike + 'PE'
            
            data[key][strike] = obj

    return data

def gen_data(json_data, expiry_date):
    ticker = json_data['ticker']
    ltp = json_data['records']['underlyingValue']
    filterd_dates_dict = filterd_dates(json_data)
    filterd_strikes = filterd_strike_price(
        filterd_dates_dict, last_trade_price=ltp, date=expiry_date)
    calculate_at_the_money(filterd_strikes, ltp)
    giant_dict = parsing_data(
        filterd_dates_dict, expiry_date, json_data, ticker)
    final_filtered_output = constract_final_output(
        filterd_dates_dict, filterd_strikes, expiry_date, giant_dict)
    
    final_filtered_output = find_all_tickers(final_filtered_output)
    
    return final_filtered_output
