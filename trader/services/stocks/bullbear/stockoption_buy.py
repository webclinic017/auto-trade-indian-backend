from email.quoprimime import body_length

from matplotlib import ticker
from interfaces.bot import TradeBot
from entities.orders import Order
from entities.ticker import TickerGenerator
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
import time
import datetime


class StockOptionBuying(TradeBot):
    invalid_tickers = set()
    fivemin_tickers = set()
    tenmin_tickers = set()

    original_tickers = {}

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

    def entry_strategy(self):
        while True:
            if datetime.datetime.now().time() < datetime.time(
                9, 30, 5
            ) or datetime.datetime.now().time() > datetime.time(15, 1, 5):
                continue

            for ticks in TickerGenerator("22", "FEB", "", "", "").stocks():
                self.original_tickers[
                    ticks.ce_ticker.tradingsymbol
                ] = ticks.ticker.tradingsymbol
                self.original_tickers[
                    ticks.pe_ticker.tradingsymbol
                ] = ticks.ticker.tradingsymbol

                if ticks.ticker.tradingsymbol in self.invalid_tickers:
                    continue

                try:
                    intraday_data = self.zerodha.historical_data_today(
                        ticks.ticker.tradingsymbol,
                        HistoricalDataInterval.INTERVAL_5_MINUTE,
                    )

                    if len(intraday_data) == 0:
                        raise Exception(
                            "intraday data is not available for",
                            ticks.ticker.tradingsymbol,
                        )
                except Exception as e:

                    self.invalid_tickers.add(ticks.ticker.tradingsymbol)

                    print(e)
                    continue

                try:
                    quote = self.zerodha.live_data(ticks.ticker.tradingsymbol)

                    if quote.last_price == 0:
                        raise Exception("no live quote for", ticks.ticker.tradingsymbol)

                except Exception as e:
                    print(e)
                    self.invalid_tickers.add(ticks.ticker.tradingsymbol)
                    continue

                # first five min data of each ticker
                first_body_length = self.body_length(intraday_data[0])
                first_direction = self.direction(first_body_length)
                first_candle_length = self.candle_length(intraday_data[0])
                first_view = self.view(
                    first_direction, first_candle_length, first_body_length
                )

                second_body_length = self.body_length(intraday_data[1])
                second_direction = self.direction(second_body_length)
                second_candle_length = self.candle_length(intraday_data[1])
                second_view = self.ohlc_view(
                    second_direction, second_candle_length, second_body_length
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

                if (
                    (intraday_data[0].open == intraday_data[0].low)
                    and (ohlc_view == "bull")
                ) or (view == "bull"):
                    if (quote.last_price > intraday_data[0].high) and (
                        ticks.ticker.tradingsymbol not in self.fivemin_tickers
                    ):
                        self.enter_trade(ce_trade)
                        self.fivemin_tickers.add(ticks.ticker.tradingsymbol)

                if (
                    (first_view == "bear")
                    and (second_view == "bull")
                    and (quote.last_price > intraday_data[1].high)
                    and (ticks.ticker.tradingsymbol not in self.tenmin_tickers)
                ):
                    self.enter_trade(ce_trade)
                    self.tenmin_tickers.add(ticks.ticker.tradingsymbol)

                if (
                    (intraday_data[0].open == intraday_data[0].high)
                    and (ohlc_view == "bear")
                ) or (view == "bear"):
                    if (quote.last_price < intraday_data[0].low) and (
                        ticks.ticker.tradingsymbol not in self.fivemin_tickers
                    ):
                        self.enter_trade(pe_trade)
                        self.fivemin_tickers.add(ticks.ticker.tradingsymbol)

                if (
                    (first_view == "bull")
                    and (second_view == "bear")
                    and (quote.last_price < intraday_data[1].low)
                    and (ticks.ticker.tradingsymbol not in self.tenmin_tickers)
                ):
                    self.enter_trade(pe_trade)
                    self.tenmin_tickers.add(ticks.ticker.tradingsymbol)

            time.sleep(10)

    def exit_strategy(self, order: Order):

        profit = 110 / 100 * order.average_entry_price

        try:
            intraday_data = self.zerodha.historical_data_today(
                self.get_original_ticker(order.trading_symbol),
                HistoricalDataInterval.INTERVAL_5_MINUTE,
            )
            if len(intraday_data) == 0:
                raise Exception(
                    "empty historical data for original", order.trading_symbol
                )
        except Exception as e:
            print(e)
            return

        quote = self.zerodha.live_data(self.get_original_ticker(order.trading_symbol))
        quote_derivative = self.zerodha.live_data(order.trading_symbol)

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

        if (
            self.option_type(order.trading_symbol) == "CE"
            and quote.last_price < intraday_data[0].low
        ):
            self.exit_trade(trade)
            return

        if (
            self.option_type(order.trading_symbol) == "PE"
            and quote.last_price > intraday_data[0].high
        ):
            self.exit_trade(trade)
            return

        if quote_derivative.last_price >= profit:
            self.exit_trade(trade)
            return

        if datetime.datetime.now().time() > datetime.time(15, 10, 1):
            self.exit_trade(trade)
            return
