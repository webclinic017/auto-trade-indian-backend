import datetime
import time
from typing_extensions import Self
from interfaces.bot import TradeBot
from entities.zerodha import HistoricalDataInterval, HistoricalOHLC
from entities.trade import Trade, TradeEndpoint, TradeTag, TradeType
from entities.orders import Order
import threading
# from trader.constants.index import HISTORICAL_DATA
from entities.ticker import TickerGenerator
from interfaces.bot import TradeBot


class BullBear(TradeBot):
    def entry_strategy(self):              
        while True:                                
            nifty_currentprice=self.zerodha.live_data("NIFTY 50").last_price  
            print('NIFTY_LTP', nifty_currentprice)
            bnknifty_currentprice=self.zerodha.live_data("NIFTY BANK").last_price
            print("banknifty_LTP", bnknifty_currentprice)
            nifty_ceticker = ""
            nifty_peticker = ""
            bnknifty_ceticker = ""
            bnknifty_peticker = ""

            print()
            for tick in self.ticker_generator.index(1):
                if tick.ticker_type == 'NIFTY':
                    nifty_ceticker = tick.ce_ticker.tradingsymbol
                    nifty_peticker = tick.pe_ticker.tradingsymbol

                    
                    
                if tick.ticker_type == 'BANKNIFTY':
                    bnknifty_ceticker = tick.ce_ticker.tradingsymbol
                    bnknifty_peticker = tick.pe_ticker.tradingsymbol


            print(nifty_peticker, nifty_ceticker)
            print(bnknifty_peticker, bnknifty_ceticker)


            nifty_ceticker_ltp=self.zerodha.live_data(nifty_ceticker).last_price
            nifty_peticker_ltp=self.zerodha.live_data(nifty_peticker).last_price
            bnknifty_ceticker_ltp=self.zerodha.live_data(bnknifty_ceticker).last_price
            bnknifty_peticker_ltp=self.zerodha.live_data(bnknifty_peticker).last_price
            print("LTP of NIFTY CE TICKER IS",nifty_ceticker_ltp,"LTP of NIFTY PE TICKER IS",nifty_peticker_ltp)
            print("LTP of BANKNIFTY CE TICKER IS",bnknifty_ceticker_ltp,"LTP of BANKNIFTY PE TICKER IS",bnknifty_peticker_ltp)

####################--------NIFTY & BANKNIFTY LATEST CANDLE DATA------------------############################
            print(self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE))
            self.nifty_latest_open=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-2].open
            self.nifty_latest_high=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-2].high
            self.nifty_latest_low=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-2].low
            self.nifty_latest_close=self.zerodha.historical_data_today("NIFTY 50",HistoricalDataInterval.INTERVAL_5_MINUTE)[-2].close
            self.nifty_latest_cdllength=self.nifty_latest_high-self.nifty_latest_low
            self.nifty_latest_bodylength=self.nifty_latest_open-self.nifty_latest_close
            self.nifty_latest_direction=100 if (self.nifty_latest_bodylength>0) else -100

            self.nifty_latestview=None
            if self.nifty_latest_direction ==100 and abs(self.nifty_latest_bodylength) > (0.8* self.nifty_latest_cdllength):
                self.nifty_latestview="bull"

            elif self.nifty_latest_direction==-100 and abs(self.nifty_latest_bodylength) > (0.8* self.nifty_latest_cdllength):
                self.nifty_latestview="bear"
                        
            print("Latest Open of Nifty is",self.nifty_latest_open,"Latest High of Nifty is",self.nifty_latest_high,"Latest Low of Nifty is",self.nifty_latest_low, "Latest Close of Nifty is",self.nifty_latest_close,"Latest Direction of Nifty is",self.nifty_latest_direction, "Latest View of Nifty is",self.nifty_latestview)
            print("nifty latest body length", self.nifty_latest_bodylength, "nifty_latest_candle length", self.nifty_latest_cdllength)
            print(self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE))
            self.bnknifty_latest_open=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-2].open
            self.bnknifty_latest_high=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-2].high
            self.bnknifty_latest_low=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-2].low
            self.bnknifty_latest_close=self.zerodha.historical_data_today("NIFTY BANK",HistoricalDataInterval.INTERVAL_5_MINUTE)[-2].close
            
            self.bnknifty_latest_cdllength=self.bnknifty_latest_high-self.bnknifty_latest_low
            self.bnknifty_latest_bodylength=self.bnknifty_latest_open-self.bnknifty_latest_close
            self.bnknifty_latest_direction=100 if (self.bnknifty_latest_bodylength>0) else -100

            self.bnknifty_latestview=None
            if self.bnknifty_latest_direction ==100 and abs(self.bnknifty_latest_bodylength) > (0.8* self.bnknifty_latest_cdllength):
                self.bnknifty_latestview="bull"

            elif self.bnknifty_latest_direction==-100 and abs(self.bnknifty_latest_bodylength) > (0.8* self.bnknifty_latest_cdllength):
                self.bnknifty_latestview="bear"  

            print("banknifty latest body length", self.bnknifty_latest_bodylength, "banknifty_latest_candle length", self.bnknifty_latest_cdllength)
            print("Latest HIGH of BANKNifty is",self.bnknifty_latest_high,"Latest OPEN of BANKNifty is",self.bnknifty_latest_open,"Latest LOW of BANKNifty is",self.bnknifty_latest_low, "Latest CLOSE of BANKNifty is",self.bnknifty_latest_close,"Latest DIRECTION of BANKNifty is",self.bnknifty_latest_direction,"Latest VIEW of BANKNifty is",self.bnknifty_latestview)
    ####################--------NIFTY & BANKNIFTY LATEST CANDLE DATA------------------############################
            #Nifty CE entry
            if nifty_currentprice > self.nifty_first5min_high:
                print("yes current price is greater than nifty first five minute high")
                
            if nifty_currentprice < self.nifty_first5min_low:
                print("yes current price is less than nifty first five minute low")
            
            if nifty_currentprice < self.nifty_first5min_high and nifty_currentprice > self.nifty_first5min_low:
                print("current price is neither less than nor more than first five minute low or high")
            
            if self.nifty_latestview == "bull":
                print("nifty latest view is bull")
                
            if self.nifty_latestview =="bear":
                print("nifty latest view is bear")
            
            if self.nifty_latestview!="bull" and self.nifty_latestview!="bear":
                print("nifty latest view is neither bull nor bear")

            if nifty_currentprice > self.nifty_first5min_high and self.nifty_latestview=="bull": #and nifty_currentprice >self.nifty_latest_high:
                print("condition met for niftyCE")
                trade=Trade(
                    endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                    trading_symbol="NIFTY BANK",
                    exchange='NFO',
                    quantity=25,
                    tag=TradeTag.ENTRY,
                    publisher="",
                    entry_price=nifty_ceticker_ltp,
                    price=self.zerodha.live_data(nifty_ceticker).depth.buy[1].price,
                    ltp=nifty_ceticker_ltp,
                    type=TradeType.STOCKOPT,
                )                
                
                self.enter_trade(trade)
            else:
                print("condition no met for niftyCE")
            # Banknifty CE entry
            if bnknifty_currentprice > self.bnknifty_first5min_high and self.bnknifty_latestview=="bull": #and bnknifty_currentprice >self.bnknifty_latest_high:
                print("condition met for banknifty CE")
                trade=Trade(
                    endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                    trading_symbol="NIFTY BANK",
                    exchange='NFO',
                    quantity=25,
                    tag=TradeTag.ENTRY,
                    publisher="",
                    entry_price=bnknifty_ceticker_ltp,
                    price=self.zerodha.live_data(),
                    ltp=1,
                    type=TradeType.STOCKOPT,
                )                               
                
                self.enter_trade(trade)
            else:
                print("condition not met for banknifty CE")
            # Nifty PE Entry
            if nifty_currentprice < self.nifty_first5min_low and self.nifty_latestview=="bear":# and nifty_currentprice<self.nifty_latest_low:
                print("condition met for Nifty PE")

                trade=Trade(
                    endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                    trading_symbol="NIFTY BANK",
                    exchange='NFO',
                    quantity=25,
                    tag=TradeTag.ENTRY,
                    publisher="",
                    entry_price=nifty_peticker_ltp,
                    price=self.zerodha.live_data(nifty_peticker).depth.buy[1].price,
                    ltp=nifty_peticker_ltp,
                    type=TradeType.STOCKOPT,
                )                
                
                self.enter_trade(trade)
            else:
                print("condition not met for NIFTY PE")
            # Banknifty PE Entry
            if bnknifty_currentprice < self.bnknifty_first5min_low and self.bnknifty_latestview=="bear":# and bnknifty_currentprice<self.bnknifty_latest_low:
                print("condition met for Banknifty PE")
                trade=Trade(
                    endpoint=TradeEndpoint.MARKET_ORDER_BUY,
                    trading_symbol="NIFTY BANK",
                    exchange='NFO',
                    quantity=25,
                    tag=TradeTag.ENTRY,
                    publisher="",
                    entry_price=bnknifty_peticker_ltp,
                    price=self.zerodha.live_data(bnknifty_peticker).depth.buy[1].price,
                    ltp=1,
                    type=TradeType.STOCKOPT,
                )
                                                
                self.enter_trade(trade)
            else:
                print("condition not met for banknifty pe")

            time.sleep(300)

    def exit_strategy(self, order: Order):           
           
        nifty_currentprice=self.zerodha.live_data("NIFTY 50")          
        bnknifty_currentprice=self.zerodha.live_data("NIFTY BANK")     
                    
        
        entry_price=order.average_entry_price
        profit=(110/100) * entry_price
        entered_ticker=order.trading_symbol
        entered_ticker_ltp=self.zerodha.live_data(entered_ticker).last_price

        trade = Trade(
            endpoint=TradeEndpoint.MARKET_ORDER_SELL,
            trading_symbol=entered_ticker,
            exchange="NFO",
            quantity=order.total_quantity,
            tag=TradeTag.EXIT,
            publisher="",
            entry_price=entered_ticker_ltp,
            price=entered_ticker_ltp,
            ltp=entered_ticker_ltp,
            type=TradeType.INDEXOPT,
        )

        if "BANKNIFTYCE" in entered_ticker and bnknifty_currentprice<self.bnknifty_latest_low:
            self.exit_trade(trade)
        
        if "BANKNIFTYPE" in entered_ticker and bnknifty_currentprice>self.bnknifty_latest_high:
            self.exit_trade(trade)
        
        if not "BANK" in entered_ticker and "CE" in entered_ticker and nifty_currentprice<self.nifty_latest_low:
            self.exit_trade(trade)
            
        if not "BANK" in entered_ticker and "PE" in entered_ticker and nifty_currentprice>self.nifty_latest_high:
            self.exit_trade(trade)

        if entered_ticker_ltp>=profit:
            self.exit_trade(trade)

        if datetime.datetime.now()>datetime.time(15,1):
            self.exit_trade(trade)
    
    def start(self):
        current_time = datetime.datetime.now()
        current_minute = current_time.time().minute
        current_hour = current_time.time().hour

        if current_hour == 9 and current_minute < 30:
            current_minute = 30
        else:
            while current_minute % 5 != 0:
                current_minute += 1

            current_minute += 2

            if current_minute > 60:
                current_hour += 1
            
            current_hour %= 24
            current_minute %= 60

        self.start_time = datetime.time(current_hour, current_minute, 10)

        print("strategy will wait till : ", self.start_time)

        while True:
            if (
                datetime.datetime.now().time() < self.start_time
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

        self.ticker_generator = TickerGenerator("22", "JAN", "22", "2", "03")

        
        super().start()

