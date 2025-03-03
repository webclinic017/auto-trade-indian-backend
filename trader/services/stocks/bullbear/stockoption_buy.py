# Modify the strategy in such a way remove first fivemin high lo in the strategy and monitor two candles atleast in the same trend then enter the
# trade for CE. For PE


# the intraday output of each ticker can be appended or overwrite in stock_tickers.json (Entered Strategy, first five min high, first five min low
# entered time, exited time, )
# once entered update with the strategy entered entered time.
# once exited updated with the time of exit so that re entry need not be necessary
# Five min and OHLC strategy should be between 9.30 to 10.30
# again five min strategy should start at 11.30 to 15
# Bollinger Band strategy and prev high, low strategy should be between 9.30 to 15.00. Stoploss first five min high or low
# Trade strategy should be positional until stoploss hits (which is first five min low)
'''
 self.enter_trade(pe_trade,
                                {
                                    "profit_percent": 5,
                                    "exit_time": datetime.time(10, 30),
                                },
'''

from typing import Dict
from interfaces.bot import TradeBot
from entities.orders import Order
from entities.ticker import TickerGenerator
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
import time
import datetime
import math


class StockOptionBuying(TradeBot):
    invalid_tickers = set()
    fivemin_tickers_morning = set()
    fivemin_tickers_afternoon = set()
    tenmin_tickers = set()
    trade_tickers = set()
    bollband_tickers = set()
    prev_high_low_tickers = set()

    original_tickers = {}
    entered_data = {}

    STRATEGY_FIRST_5MIN = "first_5minute"  # 9:30 to 10:30  again 11:30 to 15:00 PROFIT -> 5 % or else exit by time > 10 : 30 for morning
    STRATEGY_OHLC = "ohlc_strategy"  # 9:30 to 10:30  again 11:30 to 15:00 PROFIT -> 5 % or else exit by time > 10 : 30 for morning

    STRATEGY_BOLINGER_BAND = "bolinger_band"  # 9:30 to 15:00 -> PROFIT -> 15 %
    STRATEGY_TRADE = "trade"  # 9:30 to 15:00 PROFIT -> 10 %
    STRATEGY_PREV_HIGH_LOW = "prev_high_low"  # 9:30 to 15:00 PROFIT -> 5 %

    # first 5 minute ohlc of each ticker
    first_5min_ohlc_tickers: Dict[str, HistoricalOHLC] = dict()

    def option_volatilty(self, bid_price, ask_price):
        return 100 * (ask_price - bid_price) / (bid_price)

    def body_length(self, ohlc: HistoricalOHLC):
        return ohlc.close - ohlc.open

    def candle_length(self, ohlc: HistoricalOHLC):
        return ohlc.high - ohlc.low

    def direction(self, body_length: float):
        return 100 if body_length > 0 else -100

    def view(self, direction, candle_length, body_length):
        if direction == 100 and abs(body_length) > 0.8 * candle_length:
            return "bull"

        if direction == -100 and abs(body_length) < 0.8 * candle_length:
            return "bear"

        return None

    def ohlc_view(self, direction, candle_length, body_length):
        if direction == 100 and abs(body_length) > 0.6 * candle_length:
            return "bull"

        if direction == -100 and abs(body_length) > 0.6 * candle_length:
            return "bear"

        return None

    def option_type(self, trading_symbol: str):
        if "CE" in trading_symbol:
            return "CE"
        if "PE" in trading_symbol:
            return "PE"

        raise Exception("Neither PE nor CE in the trading symbol")

    def get_original_ticker(self, trading_symbol: str):
        return self.original_tickers[trading_symbol]
# BHARTIARTL22MAR740CE
    def entry_strategy(self):
        while True:
            if datetime.datetime.now().time() < datetime.time(
                9, 30, 5
            ) or datetime.datetime.now().time() > datetime.time(15, 1, 5):
                continue

            for ticks in TickerGenerator("22", "MAR", "", "", "").stocks():
                self.original_tickers[
                    ticks.ce_ticker.tradingsymbol
                ] = ticks.ticker.tradingsymbol
                self.original_tickers[
                    ticks.pe_ticker.tradingsymbol
                ] = ticks.ticker.tradingsymbol

                if (
                    ticks.ticker.tradingsymbol in self.invalid_tickers
                    or ticks.ticker.tradingsymbol not in self.data["stock_tickers"]
                ):
                    continue

                try:
                    # check if the first 5min for original ticker is present or not
                    if ticks.ticker.tradingsymbol not in self.first_5min_ohlc_tickers:
                        intraday_data = self.zerodha.historical_data_today(
                            ticks.ticker.tradingsymbol,
                            HistoricalDataInterval.INTERVAL_5_MINUTE,
                        )

                        # if the first 5min data is not present then add it to dictonary
                        self.first_5min_ohlc_tickers[
                            ticks.ticker.tradingsymbol
                        ] = intraday_data[0]

                    if len(intraday_data) == 0:
                        raise Exception(
                            "intraday data is not available for",
                            ticks.ticker.tradingsymbol,
                        )
                except Exception as e:

                    self.invalid_tickers.add(ticks.ticker.tradingsymbol)

                    print(e)
                    continue
                # df = self.zerodha.get_ohlc_data_frame(intraday_data)
                # df["slope"] = (df["high"].shift(1) - df["high"].shift(2)) / (
                #     df["low"].shift(1) - df["low"].shift(2)
                # )
                # slope = df["slope"].iloc[-2]

                try:
                    quote = self.zerodha.live_data(ticks.ticker.tradingsymbol)

                    if quote.last_price == 0:
                        raise Exception("no live quote for", ticks.ticker.tradingsymbol)

                except Exception as e:
                    print(e)
                    self.invalid_tickers.add(ticks.ticker.tradingsymbol)
                    continue
                # historical technical data
                bollinger_band = self.data["stock_tickers"][ticks.ticker.tradingsymbol]["bollinger_band"]
                trade = self.data["stock_tickers"][ticks.ticker.tradingsymbol]["trade"]
                # first five min data of each ticker
                first_body_length = self.body_length(
                    self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol]
                )
                first_direction = self.direction(first_body_length)
                first_candle_length = self.candle_length(
                    self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol]
                )
                first_view = self.view(
                    first_direction, first_candle_length, first_body_length
                )

                ohlc_view = self.ohlc_view(
                    first_direction, first_candle_length, first_body_length
                )
                view = self.view(
                    first_direction, first_candle_length, first_body_length
                )
                try:
                    ce_quote = self.zerodha.live_data(ticks.ce_ticker.tradingsymbol)
                except Exception as e:
                    print(e)
                    continue

                try:
                    pe_quote = self.zerodha.live_data(ticks.pe_ticker.tradingsymbol)
                except Exception as e:
                    print(e)
                    continue

                if len(ce_quote.depth.sell) >= 2:
                    # ce_lots = math.ceil(
                    #     10000
                    #     / (ticks.ce_ticker.lot_size * ce_quote.depth.sell[1].price)
                    # )*ticks.ce_ticker.lot_size

                    ce_trade = Trade(
                        TradeEndpoint.LIMIT_ORDER_BUY,
                        ticks.ce_ticker.tradingsymbol,
                        "NFO",
                        ticks.ce_ticker.lot_size,
                        TradeTag.ENTRY,
                        "",
                        ce_quote.depth.sell[1].price,
                        ce_quote.depth.sell[1].price,
                        ce_quote.last_price,
                        TradeType.STOCKOPT,
                    )
                else:
                    continue

                if len(pe_quote.depth.sell) >= 2:
                    # pe_lots = math.ceil(
                    #     10000
                    #     / (ticks.pe_ticker.lot_size * pe_quote.depth.sell[1].price)
                    # )*ticks.pe_ticker.lot_size

                    pe_trade = Trade(
                        TradeEndpoint.LIMIT_ORDER_BUY,
                        ticks.pe_ticker.tradingsymbol,
                        "NFO",
                        ticks.pe_ticker.lot_size,
                        TradeTag.ENTRY,
                        "",
                        pe_quote.depth.sell[1].price,
                        pe_quote.depth.sell[1].price,
                        pe_quote.last_price,
                        TradeType.STOCKOPT,
                    )
                else:
                    continue

                # ------------------------------------ entry conditions --------------------------------- #

                # -------------------------- TRADE STRATEGY -----------------------

                # condition for trade strategy for ce ticker
                if (
                    (trade > 0)
                    and (
                        quote.last_price
                        > self.data["stock_tickers"][ticks.ticker.tradingsymbol][
                            "previous_high"
                        ]
                    )
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        ) < 5
                    )
                    and (ticks.ticker.tradingsymbol not in self.trade_tickers)
                ):
                    self.enter_trade(ce_trade, {"profit_percent": 10})
                    self.trade_tickers.add(ticks.ticker.tradingsymbol)

                # condition for trade strategy for pe ticker
                if (
                    (trade < 0)
                    and (
                        quote.last_price
                        < self.data["stock_tickers"][ticks.ticker.tradingsymbol][
                            "previous_low"
                        ]
                    )
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        ) < 5
                    )
                    and (ticks.ticker.tradingsymbol not in self.trade_tickers)
                ):
                    self.enter_trade(pe_trade, {"profit_percent": 10})
                    self.trade_tickers.add(ticks.ticker.tradingsymbol)

                # --------------------- BOLLINGER BAND ------------------------

                # condition for bollinger band ce
                if (
                    (bollinger_band == "first_wide")
                    and (
                        quote.last_price
                        > self.data["stock_tickers"][ticks.ticker.tradingsymbol][
                            "previous_high"
                        ]
                    )
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        ) < 5
                    )
                    and (ticks.ticker.tradingsymbol not in self.bollband_tickers)
                ):
                    self.enter_trade(ce_trade, {"profit_percent": 15})
                    self.bollband_tickers.add(ticks.ticker.tradingsymbol)

                # condition for bollinger band pe
                if (
                    (bollinger_band == "first_wide")
                    and (
                        quote.last_price
                        < self.data["stock_tickers"][ticks.ticker.tradingsymbol][
                            "previous_low"
                        ]
                    )
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        ) < 5
                    )
                    and (ticks.ticker.tradingsymbol not in self.bollband_tickers)
                ):
                    self.enter_trade(pe_trade, {"profit_percent": 15})
                    self.bollband_tickers.add(ticks.ticker.tradingsymbol)

                # ------------------- PREVIOUS HIGH LOW CLOSE --------------------

                # condition for prev_high_low ce
                if (
                    quote.last_price
                    > self.data["stock_tickers"][ticks.ticker.tradingsymbol][
                        "previous_high"
                    ]
                    and (ticks.ticker.tradingsymbol not in self.prev_high_low_tickers)
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        ) < 5
                    )
                ):
                    self.enter_trade(ce_trade, {"profit_percent": 5})
                    self.prev_high_low_tickers.add(ticks.ticker.tradingsymbol)

                # condition for prev_high_low pe
                if (
                    quote.last_price
                    < self.data["stock_tickers"][ticks.ticker.tradingsymbol][
                        "previous_low"
                    ]
                    and (ticks.ticker.tradingsymbol not in self.prev_high_low_tickers)
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        ) < 5
                    )
                ):
                    self.enter_trade(pe_trade, {"profit_percent": 5})
                    self.prev_high_low_tickers.add(ticks.ticker.tradingsymbol)

                # ------------------------ FIRST 5 MINUTE -------------------------------

                # compute the current time because below strategies are entered based on current time
                current_time = datetime.datetime.now().time()

                # ----------- TIMMINGS FROM 9 : 30 to 10 : 30 ---------------------------

                # condition for ohlc ce ticker
                if (
                    (
                        self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol].open
                        == self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol].low
                    )
                    and (ohlc_view == "bull")
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        ) < 5
                    )
                ) or (view == "bull"):
                    if (
                        quote.last_price
                        > self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol].high
                    ) and (
                        ticks.ticker.tradingsymbol not in self.fivemin_tickers_morning
                    ):
                        # enter between 9 : 30 to 10 : 30 time only
                        if current_time >= datetime.time(
                            9, 30
                        ) and current_time <= datetime.time(10, 30):
                            self.enter_trade(
                                ce_trade,
                                {
                                    "profit_percent": 5,
                                    "exit_time": datetime.time(10, 30),
                                },
                            )
                            self.fivemin_tickers_morning.add(ticks.ticker.tradingsymbol)

                if (
                    (
                        self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol].open
                        == self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol].high
                    )
                    and (ohlc_view == "bear")
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        ) < 5
                    )
                ) or (view == "bear"):
                    if (
                        quote.last_price
                        < self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol].low
                    ) and (
                        ticks.ticker.tradingsymbol not in self.fivemin_tickers_morning
                    ):

                        # enter between 9 : 30 to 10 : 30 time only
                        if current_time >= datetime.time(
                            9, 30
                        ) and current_time <= datetime.time(10, 30):
                            self.enter_trade(
                                pe_trade,
                                {
                                    "profit_percent": 5,
                                    "exit_time": datetime.time(10, 30),
                                },
                            )
                            self.fivemin_tickers_morning.add(ticks.ticker.tradingsymbol)

                # ----------------- TIMMINGS FROM 11 : 30 to 15 : 00 -------------------------

                # condition first 5min for ce ticker
                if (
                    quote.last_price
                    > self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol].high
                    and ticks.ticker.tradingsymbol not in self.fivemin_tickers_afternoon
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        )
                    )
                ):
                    if current_time >= datetime.time(
                        11, 30
                    ) and current_time <= datetime.time(15, 0):
                        self.enter_trade(ce_trade, {"profit_percent": 5})
                        self.fivemin_tickers_afternoon.add(ticks.ticker.tradingsymbol)

                # condition first 5min for pe ticker
                if (
                    quote.last_price
                    < self.first_5min_ohlc_tickers[ticks.ticker.tradingsymbol].low
                    and ticks.ticker.tradingsymbol not in self.fivemin_tickers_afternoon
                    and (
                        self.option_volatilty(
                            quote.depth.sell[1].price, quote.depth.buy[1].price
                        )
                    )
                ):
                    if current_time >= datetime.time(
                        11, 30
                    ) and current_time <= datetime.time(15, 0):
                        self.enter_trade(pe_trade, {"profit_percent": 5})
                        self.fivemin_tickers_afternoon.add(ticks.ticker.tradingsymbol)
            print("fivemin_tickers" , fivemin_tickers_morning)
            print("fivemin_tickers_afternoon" , fivemin_tickers_afternoon
            print("trade_tickers" , trade_tickers
            print("bollband_tickers", bollband_tickers)
            print("prev_high_low_tickers" , prev_high_low_tickers)



      

            time.sleep(10)

    def exit_strategy(self, order: Order):
        profit = (100 + order.profit_percent) / 100 * order.average_entry_price
        loss = 95 / 100 * order.average_entry_price
        original_ticker = order.parent_ticker

        
        try:
            if original_ticker not in self.first_5min_ohlc_tickers:
                raise Exception(
                    "empty historical data for original", order.trading_symbol
                )
        except Exception as e:
            print(e)
            return

        quote = self.zerodha.live_data(self.get_original_ticker(order.trading_symbol))
        quote_derivative = self.zerodha.live_data(order.trading_symbol)

        if len(quote_derivative.depth.buy) >= 2:
            trade = Trade(
                TradeEndpoint.LIMIT_ORDER_SELL,
                order.trading_symbol,
                "NFO",
                order.total_quantity,
                TradeTag.EXIT,
                "",
                order.average_entry_price,
                quote_derivative.depth.buy[1].price,
                quote_derivative.last_price,
                TradeType.STOCKOPT,
            )
        else:
            return

        if (
            self.option_type(order.trading_symbol) == "CE"
            and quote.last_price < self.first_5min_ohlc_tickers[original_ticker].low
        ):
            self.exit_trade(trade)
            return

        if (
            self.option_type(order.trading_symbol) == "PE"
            and quote.last_price > self.first_5min_ohlc_tickers[original_ticker].high
        ):
            self.exit_trade(trade)
            return

        if quote_derivative.last_price >= profit:
            self.exit_trade(trade)
            return

        # if quote_derivative.last_price <= loss:
        #     self.exit_trade(trade)
        #     return

        current_time = datetime.datetime.now().time()

        # exit at the time specified in the strategy
        if current_time > datetime.time(15, 10, 1) or (
            order.exit_time and current_time > order.exit_time
        ):
            self.exit_trade(trade)
            return
