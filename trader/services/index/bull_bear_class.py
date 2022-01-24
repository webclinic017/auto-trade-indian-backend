import datetime
import time
from typing_extensions import Self
from interfaces.bot import TradeBot
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.orders import Order
import threading
from trader.constants.index import HISTORICAL_DATA
from entities.ticker import TickerGenerator
from trader.interfaces.bot import TradeBot


class BullBear(TradeBot):
    def entry_strategy(self):
        
        while True:    
            nifty_latest_open=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].open
            nifty_latest_high=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].high
            nifty_latest_low=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].low
            nifty_latest_close=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].low
            nifty_latest_cdllength=nifty_latest_high-nifty_latest_low
            nifty_latest_bodylength=nifty_latest_open-nifty_latest_close
            nifty_latest_direction=100 if (nifty_latest_bodylength>0) else -100

            nifty_latestview=None
            if nifty_latest_direction ==100 and abs(nifty_latest_bodylength) > (0.8* nifty_latest_cdllength):
                nifty_latestview="bull"

            elif nifty_latest_direction==-100 and abs(nifty_latest_bodylength) > (0.8* nifty_latest_cdllength):
                nifty_latestview="bear"
                        
            nifty_currentprice=self.zerodha.live_data("NIFTY 50")
            nifty_ceticker_currentprice=self.zerodha.live_data("NIFTY 50").
            
            
            bnknifty_latest_open=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].open
            bnknifty_latest_high=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].high
            bnknifty_latest_low=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].low
            bnknifty_latest_close=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-1].close
            
            bnknifty_latest_cdllength=bnknifty_latest_high-bnknifty_latest_low
            bnknifty_latest_bodylength=bnknifty_latest_open-bnknifty_latest_close
            bnknifty_latest_direction=100 if (bnknifty_latest_bodylength>0) else -100

            bnknifty_latestview=None
            if bnknifty_latest_direction ==100 and abs(bnknifty_latest_bodylength) > (0.8* bnknifty_latest_cdllength):
                bnknifty_latestview="bull"

            elif bnknifty_latest_direction==-100 and abs(bnknifty_latest_bodylength) > (0.8* bnknifty_latest_cdllength):
                bnknifty_latestview="bear"
                        
            
            bnknifty_currentprice=self.zerodha.live_data("NIFTY BANK")
            
            if nifty_currentprice > self.nifty_first5min_high and nifty_latestview=="bull" and nifty_currentprice>nifty_latest_high:
                trade=Trade(
                    endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                    trading_symbol="NIFTY BANK",
                    exchange='NFO',
                    quantity=25,
                    tag=TradeTag.ENTRY,
                    publisher="",
                    entry_price=1,
                    price=1,
                    ltp=1,
                    type=TradeType.STOCKOPT,
                )
                
                
                self.enter_trade(trade)

            if bnknifty_currentprice > self.bnknifty_first5min_high and bnknifty_latestview=="bull" and bnknifty_currentprice>bnknifty_latest_high:
                trade=Trade(
                    endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                    trading_symbol="NIFTY BANK",
                    exchange='NFO',
                    quantity=25,
                    tag=TradeTag.ENTRY,
                    publisher="",
                    entry_price=1,
                    price=1,
                    ltp=1,
                    type=TradeType.STOCKOPT,
                )
                
                
                
                self.enter_trade(trade)


            

    def exit_strategy(self, order: Order):
        
        entry_price=order.average_entry_price
        profit=(110/100) * entry_price
        entered_ticker=order.trading_symbol
        
        entered_ticker_ltp=self.zerodha.live_data(entered_ticker).last_price

        pass


    def start(self):
        while True:
            if (
                datetime.datetime.now().time() < datetime.time(9,30)
            ):
                continue
            
            break

        self.nifty_first5min_high=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].high
        self.nifty_first5min_low=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].low
        self.nifty_first5min_open=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].open
        self.nifty_first5min_close=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].close

                    
        self.nifty_first5min_candlelength=self.nifty_first5min_high-self.nifty_first5min_low
        self.nifty_first5min_bodylength=self.nifty_first5min_open-self.nifty_first5min_close
        self.nifty_first5min_direction= 100 if (self.nifty_first5min_bodylength > 0) else -100
        self.nifty_fiiview=None
        if self.nifty_first5min_direction == 100 and abs(self.nifty_first5min_bodylength) > (0.6*self.nifty_first5min_candlelength):
            self.nifty_fiiview="bull"
        elif self.nifty_first5min_direction==-100 and abs(self.nifty_first5min_bodylength) > (0.6* self.nifty_first5min_candlelength):
            self.nifty_fiiview="bear"

        self.bnknifty_first5min_open=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].open
        self.bnknifty_first5min_high=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].high
        self.bnknifty_first5min_low=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].low
        self.bnknifty_first5min_close=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[0].close
        
        self.bnknifty_first5min_candlelength=self.bnknifty_first5min_high-self.bnknifty_first5min_low
        self.bnknifty_first5min_bodylength=self.bnknifty_first5min_open-self.bnknifty_first5min_close
        self.bnknifty_first5min_direction= 100 if (self.bnknifty_first5min_bodylength > 0) else -100
        self.bnknifty_fiiview=None
        if self.bnknifty_first5min_direction == 100 and abs(self.bnknifty_first5min_bodylength) > (0.6*self.bnknifty_first5min_candlelength):
            self.bnknifty_fiiview="bull"
        elif self.bnknifty_first5min_direction==-100 and abs(self.bnknifty_first5min_bodylength) > (0.6* self.bnknifty_first5min_candlelength):
            self.bnknifty_fiiview="bear"
        
        super().start()

