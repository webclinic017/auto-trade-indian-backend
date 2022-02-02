from interfaces.bot import TradeBot
from entities.ticker import TickerGenerator
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType


class Cpr(TradeBot):
    def entry_strategy(self):
        historical_tickers = TickerGenerator("", "", "", "", "").get_stock_historical_tickers()
        
        while True:
            for ticks in TickerGenerator("22", "FEB", "", "", "").stocks():
                his_calc = historical_tickers[ticks.ticker.tradingsymbol]
                
                if his_calc["tc"] < his_calc["bc"]:
                    try:
                        ce_quote = self.zerodha.live_data(ticks.ce_ticker.tradingsymbol)
                    except:
                        continue
                    
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
                    continue