from entities.orders import Order
from entities.ticker import TickerGenerator
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from interfaces.bot import TradeBot


class FutureBuyOptionSell(TradeBot):
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

                # self.enter_hybrid_trade([future, ce_option, pe_option])

                self.enter_trade(future)
                self.enter_trade(ce_option)
                self.enter_trade(pe_option)

    def exit_strategy(self, order: Order):
        """
        {
            'tradingsymbol': 'ORIGINAL_TICKER',
            'pairs': [
                {tradingsymbol: CE, average_entry_price: 120, quantity: 4, exchange: 'NFO'},
                {tradingsymbol: CE, average_entry_price: 110, quantity: 2, exchange: 'NFO'},
                {tradingsymbol: PE, average_entry_price: 130, quantity: 2, exchange: 'NFO'},
                {tradingsymbol: FUT, average_entry_price: 150, quantity: 3, exchange: 'NFO'},
            ],
            profit_to_exit: 4,
            loss_to_exit: 5,
            total_quantity: 11,
            entry_price: 112  # <original_tickers_entry_price>
        }
        """

        return
