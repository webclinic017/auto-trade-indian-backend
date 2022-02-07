from interfaces.bot import TradeBot
from entities.orders import Order
from entities.ticker import TickerGenerator
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
import time
import datetime


class BullBear(TradeBot):
    invalid_tickers = set()
    fivemin_tickers=set()

    def body_length(self, ohlc: HistoricalOHLC):
        return ohlc.close - ohlc.open

    def candle_length(self, ohlc: HistoricalOHLC):
        return ohlc.high - ohlc.low

    def direction(self, body_length: float):
        return 100 if body_length > 0 else -100
   

    def ohlcview(self, direction, candle_length, body_length):
        if direction == 100 and abs(body_length) > 0.6 * candle_length:
            return "bull"

        if direction == -100 and abs(body_length) > 0.6 * candle_length:
            return "bear"

        # if any of the both conditions are not met then return none
        return None

    def view(self, direction, candle_length, body_length):
        if direction == 100 and abs(body_length) > 0.8 * candle_length:
            return "bull"

        if direction == -100 and abs(body_length) > 0.8 * candle_length:
            return "bear"

        # if any of the both conditions are not met then return none
        return None

    def option_type(self, trading_symbol: str):
        if "CE" in trading_symbol:
            return "CE"
        if "PE" in trading_symbol:
            return "PE"

        raise Exception("Neither PE nor CE in the trading symbol")

    def get_original_ticker(self, trading_symbol: str):
        # ACC22JAN123CE -> ACC JAN123CE -> on spliting on 22 (year)
        return trading_symbol.split("22")[0]

    def entry_strategy(self):
        while True:
            if datetime.datetime.now().time() < datetime.time(9, 30, 5):
                continue
            
            # historical_tickers = TickerGenerator("22", "FEB", "", "", "").get_stock_historical_tickers()

            for ticks in TickerGenerator("22", "FEB", "", "", "").stocks():
                if ticks.ticker.tradingsymbol in self.invalid_tickers:
                    continue

                try:
                    historical_data = self.zerodha.historical_data_today(
                        ticks.ticker.tradingsymbol,
                        HistoricalDataInterval.INTERVAL_5_MINUTE,
                    )

                    # for empty historical data raise exception manually
                    if len(historical_data) == 0:
                        raise Exception("historical data is empty")
                except Exception as e:
                    # if historical data is failed due to network error then we continue to next ticker
                    # if the historical data is empty then also we get error
                    self.invalid_tickers.add(ticks.ticker.tradingsymbol)
                    
                    print(e)
                    continue

                try:
                    quote = self.zerodha.live_data(ticks.ticker.tradingsymbol)

                    if quote.last_price == 0:
                        raise Exception(
                            f"invalid quote for {ticks.ticker.tradingsymbol}"
                        )
                except Exception as e:
                    print(e)

                    self.invalid_tickers.add(ticks.ticker.tradingsymbol)
                    continue

                # index 0 refers to first 5 minute ohlc
                body_length = self.body_length(historical_data[0])
                direction = self.direction(body_length)
                candle_length = self.candle_length(historical_data[0])
                ohlcview = self.ohlcview(direction, candle_length, body_length)
                view = self.view(direction, candle_length, body_length)
                
                # if historical_tickers[ticks.ticker.tradingsymbol]["tc"] >  historical_tickers[ticks.ticker.tradingsymbol]["bc"]:
                #    trade = Trade(
                #         TradeEndpoint.LIMIT_ORDER_BUY,
                #         ticks.ce_ticker.tradingsymbol,
                #         "NFO",
                #         ticks.ce_ticker.lot_size,
                #         TradeTag.ENTRY,
                #         "",
                #         ce_quote.depth.sell[1].price,
                #         ce_quote.depth.sell[1].price,
                #         ce_quote.last_price,
                #         TradeType.STOCKOPT,
                #     )
                   
                #    self.enter_trade(trade)
                #    continue

                if (
                    (historical_data[0].open == historical_data[0].low)
                    and ohlcview == "bull"
                ) or (view == "bull"):
                    try:
                        ce_quote = self.zerodha.live_data(ticks.ce_ticker.tradingsymbol)
                    except Exception as e:
                        # if there is error in fetching the live quote for a ticker then continue for the next one
                        print(e)
                        continue

                    if quote.last_price > historical_data[0].high:
                        trade = Trade(
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

                        self.enter_trade(trade)
                        # continue

                if (
                    (historical_data[0].open == historical_data[0].high)
                    and ohlcview == "bear"
                ) or (view == "bear"):
                    print(ticks)
                    try:
                        pe_quote = self.zerodha.live_data(ticks.pe_ticker.tradingsymbol)
                    except Exception as e:
                        # if there is error in fetching the live quote for a ticker then continue for the next one
                        print(e)
                        continue

                    if quote.last_price < historical_data[0].low:
                        trade = Trade(
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

                        self.enter_trade(trade)
                        # continue

            time.sleep(10)

    # first price is to track the orders entry price
    # second price is to place the order
    # third price is to verify front end and not used
    # return means go to next order, continue means next trading symbol
    def exit_strategy(self, order: Order):
        profit = 110 / 100 * order.average_entry_price

        try:
            historical_data = self.zerodha.historical_data_today(
                self.get_original_ticker(order.trading_symbol),
                HistoricalDataInterval.INTERVAL_5_MINUTE,
            )

            if len(historical_data) == 0:
                raise Exception("empty historical data")
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
            and quote.last_price < historical_data[0].low
        ):
            self.exit_trade(trade)
            return

        if (
            self.option_type(order.trading_symbol) == "PE"
            and quote.last_price > historical_data[0].high
        ):
            self.exit_trade(trade)
            return

        if quote_derivative.last_price >= profit:
            self.exit_trade(trade)
            return
