from entities.orders import Order
from entities.ticker import TickerGenerator
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.zerodha import HistoricalDataInterval
from interfaces.bot import TradeBot
import time


class BullBearStock(TradeBot):
    
    
    def entry_strategy(self):
        while True:


            for stock in self.ticker_generator.stocks():
                try:
                    historical_data = self.zerodha.historical_data_today(
                        stock.ticker.tradingsymbol, HistoricalDataInterval.INTERVAL_5_MINUTE
                    )
                    
                    if len(historical_data) == 0:
                        raise Exception('Empty historical data')
                except Exception as e:
                    print(e)
                    
                    time.sleep(5)
                    continue

                if historical_data[0].open == historical_data[0].low and 0.6* (historical_data[0].open - historical_data[0].close) > (historical_data[0].high-historical_data[0].low):
                    if self.zerodha.live_data(stock.ticker.tradingsymbol).last_price > historical_data[0].high:
                        trade = Trade(
                            TradeEndpoint.LIMIT_ORDER_BUY, 
                            stock.ce_ticker.tradingsymbol, 
                            'NFO', 
                            stock.ce_ticker.lot_size, 
                            TradeTag.ENTRY, 
                            '', 
                            self.zerodha.live_data(stock.ce_ticker.tradingsymbol).depth.sell[1].price, 
                            self.zerodha.live_data(stock.ce_ticker.tradingsymbol).depth.sell[1].price, 
                            self.zerodha.live_data(stock.ce_ticker.tradingsymbol).last_price, 
                            TradeType.STOCKOPT
                        )
                        
                        self.enter_trade(trade)
            
            time.sleep(300)


    def exit_strategy(self, order: Order):
        # RELIANCE22FEB2400CE -->  RELIANCE  FEB2400CE -> by spliting on 22
        try:
            historical_data = self.zerodha.historical_data_today(order.trading_symbol.split("22")[0], HistoricalDataInterval.INTERVAL_5_MINUTE)
        except Exception as e:
            print(e)
            return
        
        trade = Trade(
            TradeEndpoint.LIMIT_ORDER_SELL, 
            order.trading_symbol, 
            'NFO', 
            1, 
            TradeTag.EXIT, 
            '', 
            order.average_entry_price,
            self.zerodha.live_data(order.trading_symbol).depth.buy[1].price,
            self.zerodha.live_data(order.trading_symbol).last_price,
            TradeType.STOCKOPT   
        )
        
        if 'CE' in order.trading_symbol and (self.zerodha.live_data(order.trading_symbol).last_price < historical_data[0].low):
            self.exit_trade(trade)
            return
        


    def start(self):
        self.ticker_generator = TickerGenerator(
            "22",
            "FEB",
            "",
            "",
            ""
        )
        
        super().start()