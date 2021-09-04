from interfaces.tradeapp import TradeApp
import time, json, threading

class Worker4(TradeApp):
    
    tickers = ['NIFTY2190216650CE','NIFTY2190216600PE','BANKNIFTY2190235600CE','BANKNIFTY2190235500PE']
    buy_quantity = 1
    sell_quantity = 1
    
    def scalpBuy(self, ticker, data):
        rsi, slope = self.getRSISlope(ticker)
        live_data = self.getLiveData(ticker)
        ltp = live_data['last_price']
        
        log = {
            'rsi': rsi,
            'slope': slope,
            'ticker': ticker,
            'ltp': ltp,
            'cheaper_option': data['chaper_option']
        }
        
        print(json.dumps(log, indent=2))
        if rsi > 40 and slope > 0:
            trade = self.generateIndexOptionBuyTrade(ticker, self.buy_quantity, 'ENTRY_INDEX')
            self.sendTrade(trade)
            return
    
    # strategy for entry
    def entryStrategy(self):
        while True:
            latest_nifty = self.getDataIndexTicker('NIFTY')
            latest_banknifty = self.getDataIndexTicker('BANKNIFTY')
            
            if latest_nifty['data'] == 0 or latest_banknifty['data'] == 0:
                time.sleep(10)
                continue
            
            latest_nifty = latest_nifty['data'].pop()
            latest_banknifty = latest_banknifty['data'].pop()
            
            for ticker in self.tickers:
                if 'BANKNIFTY' in ticker:
                    data = latest_banknifty
                else:
                    data = latest_nifty
                threading.Thread(target=self.scalpBuy, args=[ticker, data]).start()
            
            time.sleep(310)
            
    
    # strategy for exit
    def exitStrategy(self):
        return


def main():
    app = TradeApp(name='worker_4')
    app.start()