from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.ticker import TickerGenerator
from interfaces.bot import TradeBot
from entities.orders import Order
import datetime
import time

# condition are as below:

# 1. both the candles should be bullish or bearish
# 2. If both the candles are bullish and slope = 3 and crossing the high of both the candles buy for a profit of 2%
# 3. If both the candles are bullish and slope == 5 to 10 and crossing the high of both the candles buy for the profit of 5%
# 4. If both the candles are bullish and slope == 10 or more and crossing the high of both the candles buy for the profit of 10%
# 2. If both the candles are bearish and slope = -3 and crossing the low of both the candles buy for a profit of 2%
# 3. If both the candles are bearish and slope == -5 to -10 and crossing the low of both the candles buy for the profit of 5%
# 4. If both the candles are bearish and slope == -10 or less and crossing the low of both the candles buy for the profit of 10%


class BullBear(TradeBot):
    nifty = {}
    banknifty = {}

    total_profit = 0
    total_loss = 0

    PROFIT_LIMIT = 10000
    LOSS_LIMIT = 5000

    today = datetime.datetime.today() - datetime.timedelta(days=5)

    def get_minutes(delta):
        return divmod(delta.seconds, 60)[0]

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

    def enter_trade(self, trade: Trade):
        if self.is_ticker_expired(trade.trading_symbol):
            super().enter_trade(trade)

            self.zerodha.redis.set(
                f"bullbear:index:{trade.trading_symbol}",
                1,
                datetime.timedelta(minutes=5),
            )

    def is_ticker_expired(self, tradingsymbol):
        return self.zerodha.redis.get(f"bullbear:index:{tradingsymbol}") == None

    def entry_strategy(self):
        while True:
            if (datetime.datetime.now().time() < datetime.time(9, 25, 5)) or (
                datetime.datetime.now().time() > datetime.time(15, 1, 5)
            ):
                continue

            # completely stop the strategy
            if (
                self.total_profit >= self.PROFIT_LIMIT
                or self.total_loss >= self.LOSS_LIMIT
            ):
                break

            print(f"[**] time stamp: {datetime.datetime.now()}\n\n")

            for tick in self.ticker_generator.index(1):
                if tick.ticker_type == "NIFTY":
                    try:
                        historical_data = self.zerodha.historical_data(
                            "NIFTY 50",
                            self.today,
                            self.today,
                            HistoricalDataInterval.INTERVAL_5_MINUTE,
                        )

                        if len(historical_data) == 0:
                            raise Exception("empty historical data")
                    except Exception as e:
                        # if there is error in fetching the historical data from api
                        # if the historical data fetched is null
                        print(f"\n[**] exception in nifty historical data: {e}\n")
                        continue

                    df = self.zerodha.get_ohlc_data_frame(historical_data)
                    df["slope_low"] = (df["low"] - df["low"].shift(1)) / 5
                    df["slope_high"] = (df["high"] - df["high"].shift(1)) / 5

                    slope = None

                    if (df["slope_low"].iloc[-2] > 0) and (
                        df["slope_high"].iloc[-2] > 0
                    ):
                        slope = df["slope_low"].iloc[-2]
                    elif (df["slope_low"].iloc[-2] < 0) and df["slope_high"].iloc[
                        -2
                    ] < 0:
                        slope = df["slope_high"].iloc[-2]

                    candle_length = self.get_candle_length(historical_data[-2])
                    body_length = self.get_body_length(historical_data[-2])
                    direction = self.get_direction(body_length)
                    quote = self.zerodha.live_data("NIFTY 50")

                    print("***************** - NIFTY DATA BEGIN- *********************")

                    print(f"[*] slope for NIFTY             : {slope}")
                    print(
                        f"[*] candle time for NIFTY         : {historical_data[-2].time}"
                    )
                    print(
                        f"[*] latest high                   : {historical_data[-2].high}"
                    )
                    print(
                        f"[*] latest low                    : {historical_data[-2].low}"
                    )
                    print(f"[*] candle length for NIFTY     : {candle_length}")
                    print(f"[*] body length for NIFTY       : {body_length}")
                    print(f"[*] direction for NIFTY         : {direction}")
                    print(f"[*] current price of nifty      : {quote.last_price}")

                    print("***************** - NIFTY DATA END- *********************")

                    if (
                        (slope and slope > 1.5)
                        and (direction == 100)
                        and (quote.last_price > historical_data[-2].high)
                    ):

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
                            parent_ticker=tick.ticker_type,
                        )

                        self.enter_trade(trade)
                        self.nifty["ce_stop_loss"] = historical_data[-2].low
                        self.nifty["ce_profit"] = slope
                        self.nifty["ce_entry_value"] = quote.last_price
                        self.nifty["ce_entry_time"] = datetime.datetime.now()

                    # condition for buying PE ticker of NIFTY
                    if (
                        (slope and slope < -1.5)
                        and (direction == -100)
                        and (quote.last_price < historical_data[-2].low)
                    ):
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
                            parent_ticker=tick.ticker_type,
                        )

                        self.enter_trade(trade)
                        self.nifty["pe_stop_loss"] = historical_data[-2].high
                        self.nifty["pe_profit"] = slope
                        self.nifty["pe_entry_value"] = quote.last_price
                        self.nifty["pe_entry_time"] = datetime.datetime.now()

                if tick.ticker_type == "BANKNIFTY":
                    try:
                        historical_data = self.zerodha.historical_data(
                            "NIFTY BANK",
                            self.today,
                            self.today,
                            HistoricalDataInterval.INTERVAL_5_MINUTE,
                        )

                        if len(historical_data) == 0:
                            raise Exception("empty historical data")
                    except Exception as e:
                        # if there is an network in fetching historical data or empty historical data
                        print(f"\n[**] exception in historical data bank nifty: {e}\n")
                        continue

                    df = self.zerodha.get_ohlc_data_frame(historical_data)

                    df["slope_low"] = (df["low"] - df["low"].shift(1)) / 5
                    df["slope_high"] = (df["high"] - df["high"].shift(1)) / 5
                    slope = None

                    if (df["slope_low"].iloc[-2] > 0) and (
                        df["slope_high"].iloc[-2] > 0
                    ):
                        slope = df["slope_low"].iloc[-2]
                    elif (df["slope_low"].iloc[-2] < 0) and df["slope_high"].iloc[
                        -2
                    ] < 0:
                        slope = df["slope_high"].iloc[-2]

                    candle_length = self.get_candle_length(historical_data[-2])
                    body_length = self.get_body_length(historical_data[-2])
                    direction = self.get_direction(body_length)

                    latest_view = None
                    if direction == 100 and abs(body_length) > (0.8 * candle_length):
                        latest_view = "bull"
                    elif direction == -100 and abs(body_length) > (0.8 * candle_length):
                        latest_view = "bear"

                    quote = self.zerodha.live_data("NIFTY BANK")

                    print(
                        "***************** - BANK NIFTY DATA BEGIN- *********************"
                    )

                    print(f"[*] slope for BANK NIFTY             : {slope}")
                    print(
                        f"[*] candle time for BANK NIFTY         : {historical_data[-2].time}"
                    )
                    print(
                        f"[*] latest high                        : {historical_data[-2].high}"
                    )
                    print(
                        f"[*] latest low                         : {historical_data[-2].low}"
                    )
                    print(f"[*] candle length for BANK NIFTY     : {candle_length}")
                    print(f"[*] body length for BANK NIFTY       : {body_length}")
                    print(f"[*] direction for BANK NIFTY         : {direction}")
                    print(f"[*] current price of BANK nifty      : {quote.last_price}")

                    print(
                        "***************** - BANK NIFTY DATA END- *********************"
                    )

                    if (
                        (slope and slope > 1.5)
                        and (direction == 100)
                        and (quote.last_price > historical_data[-2].high)
                    ):
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
                            quantity=25,
                            tag=TradeTag.ENTRY,
                            publisher="",
                            entry_price=ce_quote.last_price,
                            price=ce_quote.depth.sell[1].price,
                            ltp=ce_quote.last_price,
                            type=TradeType.INDEXOPT,
                            parent_ticker=tick.ticker_type,
                        )

                        self.enter_trade(trade)

                        self.banknifty["ce_stop_loss"] = historical_data[-2].low
                        self.banknifty["ce_profit"] = slope
                        self.banknifty["ce_entry_value"] = quote.last_price
                        self.banknifty["ce_entry_time"] = datetime.datetime.now()

                    if (
                        (slope and slope < -1.5)
                        and (direction == -100)
                        and (quote.last_price < historical_data[-2].low)
                    ):
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
                            quantity=25,
                            tag=TradeTag.ENTRY,
                            publisher="",
                            entry_price=pe_quote.last_price,
                            price=pe_quote.depth.sell[1].price,
                            ltp=pe_quote.last_price,
                            type=TradeType.INDEXOPT,
                            parent_ticker=tick.ticker_type,
                        )

                        self.enter_trade(trade)

                        self.banknifty["pe_stop_loss"] = historical_data[-2].high
                        self.banknifty["pe_profit"] = slope
                        self.banknifty["pe_entry_value"] = quote.last_price
                        self.banknifty["pe_entry_time"] = datetime.datetime.now()

            time.sleep(10)

    def validate_exit(
        self,
        ce_sl,
        pe_sl,
        ce_profit,
        pe_profit,
        entered_price_ce,
        entered_time_ce,
        entered_price_pe,
        entered_time_pe,
    ):
        params = locals()

        if "self" in params:
            params.pop("self")

        print(params)

        if not (all([params[key] != None for key in params])):
            raise Exception("validation failed")

    def exit_strategy(self, order: Order):
        if order.parent_ticker == "BANKNIFTY":
            quote = self.zerodha.live_data("NIFTY BANK")
            ce_sl = self.banknifty.get("ce_stop_loss")
            pe_sl = self.banknifty.get("pe_stop_loss")
            ce_profit = self.banknifty.get("ce_profit")
            pe_profit = self.banknifty.get("pe_profit")
            entered_price_ce = self.banknifty.get("ce_entry_value")
            entered_time_ce = self.banknifty.get("ce_entry_time")
            entered_price_pe = self.banknifty.get("pe_entry_value")
            entered_time_pe = self.banknifty.get("pe_entry_time")

            try:
                self.validate_exit(
                    ce_sl,
                    pe_sl,
                    ce_profit,
                    pe_profit,
                    entered_price_ce,
                    entered_time_ce,
                    entered_price_pe,
                    entered_time_pe,
                )
            except Exception as e:
                print(f"[**] Exception : {e}")
                return

            ce_sl = ce_sl / 2
            pe_sl = pe_sl / 2

            try:
                historical_data = self.zerodha.historical_data(
                    "NIFTY BANK",
                    self.today,
                    self.today,
                    HistoricalDataInterval.INTERVAL_5_MINUTE,
                )

                if len(historical_data) == 0:
                    raise Exception("empty historical data")
            except Exception as e:
                print(f"[**] Exception : {e}")
                return

        else:
            quote = self.zerodha.live_data("NIFTY 50")
            ce_sl = self.nifty.get("ce_stop_loss")
            pe_sl = self.nifty.get("pe_stop_loss")
            ce_profit = self.nifty.get("ce_profit")
            pe_profit = self.nifty.get("pe_profit")
            entered_price_ce = self.nifty.get("ce_entry_value")
            entered_time_ce = self.nifty.get("entry_time")
            entered_price_pe = self.nifty.get("pe_entry_value")
            entered_time_pe = self.nifty.get("pe_entry_time")

            try:
                self.validate_exit(
                    ce_sl,
                    pe_sl,
                    ce_profit,
                    pe_profit,
                    entered_price_ce,
                    entered_time_ce,
                    entered_price_pe,
                    entered_time_pe,
                )
            except Exception as e:
                print(f"[**] Exception : {e}")
                return

            ce_sl = ce_sl / 2
            pe_sl = pe_sl / 2

            try:
                historical_data = self.zerodha.historical_data(
                    "NIFTY 50",
                    self.today,
                    self.today,
                    HistoricalDataInterval.INTERVAL_5_MINUTE,
                )

                if len(historical_data) == 0:
                    raise Exception("empty historical data")
            except Exception as e:
                print(f"[**] Exception : {e}")
                return

        ticker_quote = self.zerodha.live_data(order.trading_symbol)
        profit_breakeven = (101 / 100) * order.average_entry_price
        profit_min = (105 / 100) * order.average_entry_price
        profit_five = (107 / 100) * order.average_entry_price
        profit_ten = (110 / 100) * order.average_entry_price
        profit_fifteen = (115 / 100) * order.average_entry_price

        if (ce_profit > 1.5) and (ce_profit <= 5):
            profit = profit_min

        if (ce_profit > 5) and (ce_profit <= 10):
            profit = profit_five

        if (ce_profit > 10) and (ce_profit <= 15):
            profit = profit_ten

        if ce_profit > 15:
            profit = profit_fifteen

        if (pe_profit < -1.5) and (pe_profit >= -5):
            profit = profit_min

        if (pe_profit < -5) and (pe_profit >= -10):
            profit = profit_five

        if (pe_profit < -10) and (pe_profit >= -15):
            profit = profit_ten

        if pe_profit < -15:
            profit = profit_fifteen

        trade = order.get_exit_trade(ticker_quote)

        # completely exit the orders
        if self.total_profit >= self.PROFIT_LIMIT or self.total_loss >= self.LOSS_LIMIT:
            self.exit_trade(trade)
            return

        current_time = datetime.datetime.now()

        if (self.get_option_type(order.trading_symbol) == "CE") and (
            quote.last_price < ce_sl
        ):
            self.exit_trade(trade)

            self.total_loss += (
                order.average_entry_price - ticker_quote.last_price
            ) * order.quantity
            return

        if (self.get_option_type(order.trading_symbol) == "CE") and (
            entered_time_ce and (self.get_minutes(current_time - entered_time_ce)) >= 5
        ):
            if quote.last_price < entered_price_ce:
                print("[**] Exited after 5 minutes [**]")
                self.exit_trade(trade)
                return

        if (self.get_option_type(order.trading_symbol) == "PE") and (
            quote.last_price > pe_sl
        ):
            self.exit_trade(trade)

            self.total_loss += (
                order.average_entry_price - ticker_quote.last_price
            ) * order.quantity
            return

        if (self.get_option_type(order.trading_symbol) == "PE") and (
            entered_time_pe and self.get_minutes((current_time - entered_time_pe)) >= 5
        ):
            if quote.last_price < entered_price_pe:
                print("[**] Exited after 5 minutes [**]")
                self.exit_trade(trade)
                return

        if (
            ticker_quote.last_price >= profit
            or datetime.datetime.now().time() > datetime.time(15, 29)
        ):
            self.exit_trade(trade)

            self.total_profit += (
                ticker_quote.last_price - order.average_entry_price
            ) * order.quantity
            return

    def start(self):
        # wait until next 5 multiple time
        self.wait()

        # First stock year, stock month, index year, index month, indexweek
        self.ticker_generator = TickerGenerator("22", "JAN", "22", "3", "03")

        super().start()
