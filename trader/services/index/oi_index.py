#Open Interest based for Index
from interfaces.tradeapp import TradeApp
import datetime,time


class openinterestindex(TradeApp):

    nifty_5min={}
    nifty_15min={}
    banknifty_5min={}
    banknifty_15min={}
    def entryStrategy(self):
        
        self.nifty_gamechanger = self.data['index']['NSE:NIFTY 50']['ltp']
        self.nifty_totalpower=self.data["index"]["NSE:NIFTY 50"]['total_power']
        self.banknifty_gamechanger = self.data['index']['NSE:NIFTY BANK']['ltp']
        self.banknifty_totalpower=self.data["index"]["NSE:NIFTY BANK"]['total_power']
        date=str(datetime.date.today())
        

        while True:
            if datetime.datetime.now().time()>datetime.time(9,20) and datetime.datetime.now().time()<datetime.time(9,21):
                self.nifty_5min=self.getLiveData('NSE:NIFTY 50')['ohlc']
                self.banknifty_5min=self.getLiveData('NSE:NIFTY BANK')['ohlc']
                break
            
            elif datetime.datetime.now().time()>datetime.time(9,30) and datetime.datetime.now().time()<datetime.time(9,31):
                self.nifty_15min=self.getLiveData('NSE:NIFTY 50')['ohlc']
                self.banknifty_15min=self.getLiveData('NSE:NIFTY BANK')['ohlc']
                break
            else:
                self.nifty_5min=self.getLiveData('NSE:NIFTY 50')['ohlc']
                self.banknifty_5min=self.getLiveData('NSE:NIFTY BANK')['ohlc']
                self.nifty_15min=self.getLiveData('NSE:NIFTY 50')['ohlc']
                self.banknifty_15min=self.getLiveData('NSE:NIFTY BANK')['ohlc']
                break

        while True:

            nifty_live=self.getLiveData('NSE:NIFTY 50')
            banknifty_live=self.getLiveData('NSE:NIFTY BANK')
            nifty_rsi,nifty_slope=self.getRSISlope('NSE:NIFTY 50')
            banknifty_rsi,banknifty_slope=self.getRSISlope('NSE:NIFTY BANK')
            print('nifty_slope',nifty_slope)

            if nifty_live['last_price']>self.nifty_gamechanger and nifty_slope>0 and self.nifty_totalpower>10000: #and nifty_live['last_price']>self.nifty_5min['high']:
                ticker=self.data['index']['NSE:NIFTY 50']['ce_ticker']
                print(nifty_slope)
                trade=self.generateMarketOrderBuyIndexOption(ticker,50,'ENTRY')
                #the below line sends trade to front end
                self.sendTrade(trade)

            if nifty_live['last_price']<self.nifty_gamechanger and nifty_slope<0 and self.nifty_totalpower<-10000:
                ticker=self.data['index']['NSE:NIFTY 50']['pe_ticker']
                trade=self.generateMarketOrderBuyIndexOption(ticker,50,'ENTRY')
                #the below line sends trade to front end
                self.sendTrade(trade)

            print('banknifty_slope',banknifty_slope)
            if banknifty_live['last_price']>self.banknifty_gamechanger and banknifty_slope>0 and self.banknifty_totalpower>30000:
                ticker=self.data['index']['NSE:NIFTY BANK']['ce_ticker']
                trade=self.generateMarketOrderBuyIndexOption(ticker,25,'ENTRY')
                #the below line sends trade to front end
                self.sendTrade(trade)

            if banknifty_live['last_price']<self.banknifty_gamechanger and banknifty_slope<0 and self.banknifty_totalpower<-30000:
                ticker=self.data['index']['NSE:NIFTY BANK']['pe_ticker']
                trade=self.generateMarketOrderBuyIndexOption(ticker,25,'ENTRY')
                #the below line sends trade to front end
                self.sendTrade(trade)

            time.sleep(300)

           
            
     
    def exitStrategy(self):

        while True:
            orders=self.getAllOrders()

            for order in orders:
                ticker=order['ticker']
                entryprice=self.averageEntryprice(order['data'])
                profit_price=entryprice*110/100
                loss_price=entryprice*95/100
                livedata=self.getLiveData(ticker)
                livedata_nifty=self.getLiveData('NSE:NIFTY 50')
                livedata_banknifty=self.getLiveData('NSE:NIFTY BANK')

                if 'CE' in ticker:
                    if livedata_nifty['last_price']<self.nifty_gamechanger and 'BANKNIFTY' not in ticker:
                        trade=self.generateMarketOrderSellIndexOption(ticker,50,'EXIT')
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue
                    
                    elif livedata_banknifty['last_price']<self.banknifty_gamechanger and 'BANKNIFTY' in ticker:
                        trade=self.generateMarketOrderSellIndexOption(ticker,25,'EXIT')
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                elif 'PE' in ticker:
                    if livedata_nifty['last_price']>self.nifty_gamechanger and 'BANKNIFTY' not in ticker:
                        trade=self.generateMarketOrderSellIndexOption(ticker,50,'EXIT')
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                    elif livedata_banknifty['last_price']>self.banknifty_gamechanger and 'BANKNIFTY' in ticker:
                        trade=self.generateMarketOrderSellIndexOption(ticker,25,'EXIT')
                        self.sendTrade(trade)
                        self.deleteOrder(ticker)
                        continue

                

                if livedata['last_price']>=profit_price or datetime.datetime.now().time() >= datetime.time(15, 10):
                    print(profit_price," profit")
                    trade=self.generateMarketOrderSellIndexOption(ticker,50,'EXIT')
                    self.sendTrade(trade)
                    self.deleteOrder(ticker)
                    continue


            time.sleep(10)


def main():
    app=openinterestindex(name='oi_index')
    app.start()







