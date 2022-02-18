from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.ticker import TickerGenerator
from interfaces.bot import TradeBot
from entities.orders import Order
import datetime
import time
import talib as tb
import pandas as pd

# condition are as below:
# 1. both the candles should be bullish or bearish
# 2. If both the candles are bullish and slope = 3 and crossing the high of both the candles buy for a profit of 2%
# 3. If both the candles are bullish and slope == 5 to 10 and crossing the high of both the candles buy for the profit of 5%
# 4. If both the candles are bullish and slope == 10 or more and crossing the high of both the candles buy for the profit of 10%
# 2. If both the candles are bearish and slope = -3 and crossing the low of both the candles buy for a profit of 2%
# 3. If both the candles are bearish and slope == -5 to -10 and crossing the low of both the candles buy for the profit of 5%
# 4. If both the candles are bearish and slope == -10 or less and crossing the low of both the candles buy for the profit of 10%


class BullBear(TradeBot):

    # sl_ce={}
    # sl_pe = {}
    # profit = {}
    nifty = {}
    banknifty = {}

    def get_candle_length(self, ohlc: HistoricalOHLC):
        return ohlc.high - ohlc.low

    def get_body_length(self, ohlc: HistoricalOHLC):
        return ohlc.close - ohlc.open

    def get_direction(self, body_length: float):
        return 100 if body_length > 0 else -100

    def get_index_type(self, tradingsymbol):
        if "BANK" in tradingsymbol:
            return "BANKNIFTY"

        if "NIFTY" in tradingsymbol:
            return "NIFTY"

        raise Exception("invalid index ticker")

    def get_option_type(self, tradingsymbol):
        if "CE" in tradingsymbol:
            return "CE"

        if "PE" in tradingsymbol:
            return "PE"

        raise Exception("invalid option ticker")

    def entry_strategy(self):
        while True:
            if (datetime.datetime.now().time() < datetime.time(9, 30, 5)) or (
                datetime.datetime.now().time() > datetime.time(15, 1, 5)
            ):
                continue

            print(f"[**] time stamp: {datetime.datetime.now()}\n\n")

            for tick in self.ticker_generator.index(1):
                if tick.ticker_type == "NIFTY":
                    try:
                        historical_data = self.zerodha.historical_data(
                            "NIFTY 50",
                            datetime.date.today(),
                            datetime.datetime.today(),
                            HistoricalDataInterval.INTERVAL_5_MINUTE,
                        )

                        if len(historical_data) == 0:
                            raise Exception("empty historical data")
                    except Exception as e:
                        # if there is error in fetching the historical data from api
                        # if the historical data fetched is null
                        print(f"\n[**] exception in nifty historical data: {e}\n")
                        continue
                    # get_ohlc_data_frame(self, historical_data: List[HistoricalOHLC])
                    df = self.zerodha.get_ohlc_data_frame(historical_data)

                    df["slope"] = (df["high"] - df["high"].shift(1)) / (
                        df["low"] - df["low"].shift(1)
                    )
                    slope = df["slope"].iloc[-2]
                    # print(df)
                    # monitored_time = df['date'].iloc[-2]

                    candle_length = self.get_candle_length(historical_data[-2])
                    body_length = self.get_body_length(historical_data[-2])
                    direction = self.get_direction(body_length)

                    print("")
                    print(f"[*] slope for NIFTY  : {slope}")
                    print(f"[*] candle length for NIFTY  : {candle_length}")
                    print(f"[*] body length for NIFTY    : {body_length}")
                    print(f"[*] direction for NIFTY      : {direction}")
                    # print(f"[*] monitored time     : {current_time}")

                    latest_view = None
                    if direction == 100 and abs(body_length) > 0.8 * candle_length:
                        latest_view = "bull"
                    elif direction == -100 and abs(body_length) > 0.8 * candle_length:
                        latest_view = "bear"

                    print(f"[*] latest view for NIFTY    : {latest_view}")
                    print("")

                    quote = self.zerodha.live_data("NIFTY 50")

                    # condition for buying CE ticker of NIFTY
                    # if (
                    #     quote.last_price > historical_data[0].high
                    #     and latest_view == "bull"
                    # ):
                    # if (latest_view == "bull") and (slope > 3):
                    if (slope > 3) and (direction == 100):

                        try:
                            ce_quote = self.zerodha.live_data(
                                tick.ce_ticker.tradingsymbol
                            )
                        except Exception:
                            # when failed to fetch the quote for CE ticker then go for next ticker
                            continue

                        trade = Trade(
                            endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                            trading_symbol=tick.ce_ticker.tradingsymbol,
                            exchange="NFO",
                            quantity=tick.ce_ticker.lot_size,
                            tag=TradeTag.ENTRY,
                            publisher="",
                            entry_price=ce_quote.last_price,
                            price=ce_quote.depth.sell[1].price,
                            ltp=ce_quote.last_price,
                            type=TradeType.INDEXOPT,
                        )

                        self.enter_trade(trade)
                        # self.sl_ce["nifty"] = historical_data[-2].low
                        # self.profit["nifty_positive_slope"] = slope
                        self.nifty["ce_stop_loss"] = historical_data[-2].low
                        self.nifty["ce_profit"] = slope

                    # condition for buying PE ticker of NIFTY
                    # if (
                    #     quote.last_price < historical_data[0].low
                    #     and latest_view == "bear"
                    # ):

                    # if (latest_view == "bear") and (slope < -3):
                    if (slope < -3) and (direction == -100):
                        try:
                            pe_quote = self.zerodha.live_data(
                                tick.pe_ticker.tradingsymbol
                            )
                        except Exception:
                            # failed to fetch the quote for PE ticker then continue for next ticker
                            continue

                        trade = Trade(
                            endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                            trading_symbol=tick.pe_ticker.tradingsymbol,
                            exchange="NFO",
                            quantity=tick.pe_ticker.lot_size,
                            tag=TradeTag.ENTRY,
                            publisher="",
                            entry_price=pe_quote.last_price,
                            ltp=pe_quote.last_price,
                            price=pe_quote.depth.sell[1].price,
                            type=TradeType.INDEXOPT,
                        )

                        self.enter_trade(trade)
                        # self.sl_pe["nifty"] = historical_data[-2].high
                        # self.profit["nifty_negative_slope"] = slope
                        self.nifty["pe_stop_loss"] = historical_data[-2].high
                        self.nifty["pe_profit"] = slope

                if tick.ticker_type == "BANKNIFTY":
                    try:
                        historical_data = self.zerodha.historical_data(
                            "NIFTY BANK",
                            datetime.date.today(),
                            datetime.date.today(),
                            HistoricalDataInterval.INTERVAL_5_MINUTE,
                        )

                        if len(historical_data) == 0:
                            raise Exception("empty historical data")
                    except Exception as e:
                        # if there is an network in fetching historical data or empty historical data
                        print(f"\n[**] exception in historical data bank nifty: {e}\n")
                        continue

                    df = self.zerodha.get_ohlc_data_frame(historical_data)
                    df["slope"] = tb.LINEARREG_SLOPE(df["close"], 5)
                    slope = df["slope"].iloc[-1]
                    candle_length = self.get_candle_length(historical_data[-2])
                    body_length = self.get_body_length(historical_data[-2])
                    direction = self.get_direction(body_length)

                    print("")
                    print(f"[*] candle length for BANKNIFTY  : {candle_length}")
                    print(f"[*] body length for BANKNIFTY    : {body_length}")
                    print(f"[*] direction for BANKNIFTY      : {direction}")

                    latest_view = None
                    if direction == 100 and abs(body_length) > (0.8 * candle_length):
                        latest_view = "bull"
                    elif direction == -100 and abs(body_length) > (0.8 * candle_length):
                        latest_view = "bear"

                    quote = self.zerodha.live_data("NIFTY BANK")

                    print(f"[*] latest view for BANKNIFTY    : {latest_view}")
                    print("")

                    # if (
                    #     quote.last_price > historical_data[0].high
                    #     and latest_view == "bull"
                    # ):
                    # if (latest_view == "bull") and (slope > 4):
                    if (slope > 4) and (direction == 100):
                        try:
                            ce_quote = self.zerodha.live_data(
                                tick.ce_ticker.tradingsymbol
                            )
                        except Exception:
                            continue

                        trade = Trade(
                            endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                            trading_symbol=tick.ce_ticker.tradingsymbol,
                            exchange="NFO",
                            quantity=tick.ce_ticker.lot_size,
                            tag=TradeTag.ENTRY,
                            publisher="",
                            entry_price=ce_quote.last_price,
                            price=ce_quote.depth.sell[1].price,
                            ltp=ce_quote.last_price,
                            type=TradeType.INDEXOPT,
                        )

                        self.enter_trade(trade)
                        # self.sl_ce["banknifty"]=historical_data[-2].low
                        # self.profit["banknifty_positive_slope"] = slope
                        self.banknifty["ce_stop_loss"] = historical_data[-2].low
                        self.banknifty["ce_profit"] = slope
                        # self.sl_ce[ticks.tradingsymbol] = historical_data[-2].low

                    # if (
                    #     quote.last_price < historical_data[0].low
                    #     and latest_view == "bear"
                    # ):
                    # if (latest_view == "bear") and (slope < -4):
                    if (slope < -4) and (direction == -100):
                        try:
                            pe_quote = self.zerodha.live_data(
                                tick.pe_ticker.tradingsymbol
                            )
                        except Exception:
                            continue

                        trade = Trade(
                            endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                            trading_symbol=tick.pe_ticker.tradingsymbol,
                            exchange="NFO",
                            quantity=tick.pe_ticker.lot_size,
                            tag=TradeTag.ENTRY,
                            publisher="",
                            entry_price=pe_quote.last_price,
                            price=pe_quote.depth.sell[1].price,
                            ltp=pe_quote.last_price,
                            type=TradeType.INDEXOPT,
                        )

                        self.enter_trade(trade)
                        # self.sl_pe["banknifty"]=historical_data[-2].high
                        # self.profit["banknifty_negative_slope"] = slope
                        self.banknifty["pe_stop_loss"] = historical_data[-2].high
                        self.banknifty["pe_profit"] = slope
                        # self.sl_pe[ticks.tradingsymbol] = historical_data[-2].high

            time.sleep(300)

    def exit_strategy(self, order: Order):
        if self.get_index_type(order.trading_symbol) == "BANKNIFTY":
            quote = self.zerodha.live_data("NIFTY BANK")
            # ce_sl=self.sl_ce.get('banknifty', -float('inf'))
            # pe_sl=self.sl_pe.get('banknifty', -float('inf'))
            ce_sl = self.banknifty.get("ce_stop_loss", -float("inf"))
            pe_sl = self.banknifty.get("pe_stop_loss", -float("inf"))
            ce_profit = self.banknifty.get("ce_profit", -float("inf"))
            pe_profit = self.banknifty.get("pe_profit", -float("inf"))

            try:
                historical_data = self.zerodha.historical_data(
                    "NIFTY BANK",
                    datetime.date.today(),
                    datetime.date.today(),
                    HistoricalDataInterval.INTERVAL_5_MINUTE,
                )

                if len(historical_data) == 0:
                    raise Exception("empty historical data")
            except Exception:
                return
        else:
            quote = self.zerodha.live_data("NIFTY 50")

            # ce_sl = self.sl_ce.get('nifty', -float("inf"))
            # pe_sl = self.sl_pe.get('nifty', -float("inf"))
            ce_sl = self.nifty.get("ce_stop_loss", -float("inf"))
            pe_sl = self.nifty.get("pe_stop_loss", -float("inf"))
            ce_profit = self.nifty.get("ce_profit", -float("inf"))
            pe_profit = self.nifty.get("pe_profit", -float("inf"))
            try:
                historical_data = self.zerodha.historical_data(
                    "NIFTY 50",
                    datetime.date.today(),
                    datetime.date.today(),
                    HistoricalDataInterval.INTERVAL_5_MINUTE,
                )

                if len(historical_data) == 0:
                    raise Exception("empty historical data")
            except Exception:
                return

        ticker_quote = self.zerodha.live_data(order.trading_symbol)
        profit_breakeven = (101 / 100) * order.average_entry_price
        profit_min = (102 / 100) * order.average_entry_price
        profit_five = (105 / 100) * order.average_entry_price
        profit_ten = (110 / 100) * order.average_entry_price
        profit_fifteen = (115 / 100) * order.average_entry_price

        if (ce_profit > 3) and (ce_profit <= 5):
            profit = profit_min

        if (ce_profit > 5) and (ce_profit <= 10):
            profit = profit_five

        if (ce_profit > 10) and (ce_profit <= 15):
            profit = profit_ten

        if ce_profit > 15:
            profit = profit_fifteen

        if (pe_profit < -3) and (pe_profit >= -5):
            profit = profit_min

        if (pe_profit < -5) and (pe_profit >= -10):
            profit = profit_five

        if (pe_profit < -10) and (ce_profit >= -15):
            profit = profit_ten

        if pe_profit < -15:
            profit = profit_fifteen

        trade = Trade(
            endpoint=TradeEndpoint.MARKET_ORDER_SELL,
            trading_symbol=order.trading_symbol,
            exchange="NFO",
            quantity=order.total_quantity,
            tag=TradeTag.EXIT,
            publisher="",
            entry_price=ticker_quote.last_price,
            price=ticker_quote.depth.buy[1].price,
            ltp=ticker_quote.last_price,
            type=TradeType.INDEXOPT,
            max_quantity=1800,
        )

        if (
            self.get_option_type(order.trading_symbol) == "CE"
            and quote.last_price < ce_sl
        ):
            self.exit_trade(trade)
            return

        if (
            self.get_option_type(order.trading_symbol) == "PE"
            and quote.last_price > pe_sl
        ):
            self.exit_trade(trade)
            return

        if (
            ticker_quote.last_price >= profit
            or datetime.datetime.now().time() > datetime.time(15, 5)
        ):
            self.exit_trade(trade)
            return

    def start(self):
        current_time = datetime.datetime.now()
        current_minute = current_time.time().minute
        current_hour = current_time.time().hour

        if current_hour == 9 and current_minute < 30:
            current_minute = 30
        else:
            while current_minute % 5 != 0:
                current_minute += 1

            current_minute += 1

            if current_minute > 60:
                current_hour += 1

            current_hour %= 24
            current_minute %= 60

        self.start_time = datetime.time(current_hour, current_minute, 10)
        print(f"[**] strategy starts at {self.start_time}")
        # First stock year, stock month, index year, index month, indexweek
        self.ticker_generator = TickerGenerator("22", "JAN", "22", "FEB", "")

        super().start()
