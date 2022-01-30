from entities.orders import Order
from entities.ticker import TickerGenerator
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from interfaces.bot import TradeBot
import time
import datetime


class BullBearStock(TradeBot):
    def get_candle_length(self, ohlc: HistoricalOHLC):
        return ohlc.high - ohlc.low
    
    def get_body_length(self, ohlc:HistoricalOHLC):
        return ohlc.close - ohlc.open
    
    def get_direction(self,body_length: float):
        return 100 if body_length > 0 else -100
    
    def get_option_type(self, tradingsymbol):
        if "CE" in tradingsymbol:
            return "CE"
        
        if "PE" in tradingsymbol:
            return "PE"
    
    def entry_strategy(self):
        while True:
            if datetime.datetime.now().time() < self.start_time:
                continue
            
            for tick in self.ticker_generator.stocks
    
    
    