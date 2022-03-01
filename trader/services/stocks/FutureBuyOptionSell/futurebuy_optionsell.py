from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from interfaces.bot import StrategyType, TradeBot
from entities.ticker import TickerGenerator
from utils.strategy import StrategyUtil
from entities.orders import Order
from typing import List


class FutureBuyOptionSell(TradeBot):
    strategy_type = StrategyType.HYBRID

    def entry_strategy(self):
        for ticks in TickerGenerator("22", "MAR", "", "", "").stocks():
            if self.data["stock_tickers"][ticks.ticker.tradingsymbol]["trade"] > 0:
                # buy future
                try:
                    future_quote = self.zerodha.live_data(ticks.future.tradingsymbol)
                except:
                    continue

                future = Trade(
                    TradeEndpoint.LIMIT_ORDER_BUY,
                    ticks.future.tradingsymbol,
                    "NFO",
                    ticks.future.lot_size,
                    TradeTag.ENTRY,
                    "",
                    future_quote.last_price,
                    future_quote.depth.sell[1].price,
                    future_quote.last_price,
                    TradeType.STOCKFUT,
                    parent_ticker=ticks.ticker.tradingsymbol,
                )

                # sell option
                try:
                    ce_quote = self.zerodha.live_data(ticks.ce_ticker.tradingsymbol)
                    pe_quote = self.zerodha.live_data(ticks.pe_ticker.tradingsymbol)
                except:
                    continue

                ce_option = Trade(
                    TradeEndpoint.LIMIT_ORDER_SELL,
                    ticks.ce_ticker.tradingsymbol,
                    "NFO",
                    ticks.ce_ticker.lot_size,
                    TradeTag.ENTRY,
                    "",
                    ce_quote.last_price,
                    ce_quote.depth.buy[1].price,
                    ce_quote.last_price,
                    TradeType.STOCKOPT,
                    parent_ticker=ticks.ticker.tradingsymbol,
                )

                pe_option = Trade(
                    TradeEndpoint.LIMIT_ORDER_SELL,
                    ticks.ce_ticker.tradingsymbol,
                    "NFO",
                    ticks.ce_ticker.lot_size,
                    TradeTag.ENTRY,
                    "",
                    pe_quote.last_price,
                    pe_quote.depth.buy[1].price,
                    pe_quote.last_price,
                    TradeType.STOCKOPT,
                    parent_ticker=ticks.ticker.tradingsymbol,
                )

                self.enter_hybrid_trade([future, ce_option, pe_option])

    def exit_strategy_hybrid(self, orders: List[Order]):
        # get the total average price
        average_entry_price = StrategyUtil.get_average_entry_price_of_orders(orders)
        average_price = StrategyUtil.get_average_price_of_orders(orders, self.zerodha)

        profit_price = (110 / 100) * average_entry_price

        trades = []

        for order in orders:
            try:
                quote = self.zerodha.live_data(order.trading_symbol)
            except:
                continue

            trades.append(order.get_exit_trade(quote))

        if average_price > profit_price:
            self.exit_all_trades(trades)
