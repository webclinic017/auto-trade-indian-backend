import datetime
import time
from typing_extensions import Self
from interfaces.bot import TradeBot
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.orders import Order
import threading
from trader.constants.index import HISTORICAL_DATA

from trader.interfaces.bot import TradeBot


class BullBear(TradeBot):
    def entry_strategy(self):
        
        while True:
            if (
                datetime.datetime.now().time() < datetime.time(9,30)
                or datetime.datetime.now().time() > datetime.time(15,1)
            ):
                continue         

            nifty_latest_high=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].high
            nifty_latest_low=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].low            
            nifty_currentprice=self.zerodha.live_data("NIFTY 50")
            
            bnknifty_latest_high=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].high
            bnknifty_latest_low=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].low
            bnknifty_currentprice=self.zerodha.live_data("NIFTY BANK")
            
            

            

    def exit_strategy(self, order: Order):
        
        pass


    def start(self):
        while True:

            if (
                datetime.datetime.now().time() < datetime.time(9,30)
                or datetime.datetime.now().time() > datetime.time(15,1)
            ):
                continue

            self.nifty_first5min_high=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].high
            self.nifty_first5min_low=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].low
            self.nifty_first5min_open=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].open
            self.nifty_first5min_close=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].close

                        
            self.nifty_first5min_candlelength=self.nifty_first5min_high-self.nifty_first5min_low
            self.nifty_first5min_bodylength=self.nifty_first5min_open-self.nifty_first5min_close
            self.nifty_first5min_direction= 100 if (self.nifty_first5min_bodylength > 0) else -100
            self.nifty_fiiview=None
            if self.nifty_first5min_direction == 100 and abs(self.nifty_first5min_bodylength) > (0.6*self.nifty_first5min_candlelength):
                self.nifty_fiiview="Bullish"
            elif self.nifty_first5min_direction==-100 and abs(self.nifty_first5min_bodylength) > (0.6* self.nifty_first5min_candlelength):
                self.nifty_fiiview="Bearish"

            self.bnknifty_first5min_open=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].open
            self.nifty_first5min_highbnknifty_first5min_high=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].high
            self.bnknifty_first5min_low=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].low
            self.bnknifty_first5min_close=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].close
            
            self.bnknifty_first5min_candlelength=self.bnknifty_first5min_high-self.bnknifty_first5min_low
            self.bnknifty_first5min_bodylength=self.bnknifty_first5min_open-self.bnknifty_first5min_close
            self.bnknifty_first5min_direction= 100 if (self.bnknifty_first5min_bodylength > 0) else -100
            self.bnknifty_fiiview=None
            if self.bnknifty_first5min_direction == 100 and abs(self.bnknifty_first5min_bodylength) > (0.6*self.bnknifty_first5min_candlelength):
                self.bnknifty_fiiview="Bullish"
            elif self.bnknifty_first5min_direction==-100 and abs(self.bnknifty_first5min_bodylength) > (0.6* self.bnknifty_first5min_candlelength):
                self.bnknifty_fiiview="Bearish"
        
        super().start()

