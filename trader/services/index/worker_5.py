from interfaces.tradeapp import TradeApp
import time

class Worker5(TradeApp):
    
    tickers = ['NIFTY', 'BANKNIFTY']
    quantity = 50
    
    ticker_pairs = []
    
    def entryStrategy(self):
        while True:
            for ticker in self.tickers:
                data = self.getDataIndexTicker(ticker)['data'].pop()
                CE_KEY = 'CE_Strikes'
                PE_KEY = 'PE_Strikes'
                PERCENTAGE = 0.1
                
                ce_documents = data[CE_KEY]
                pe_documents = data[PE_KEY]
                
                pairs = set()
                
                for strike in ce_documents:
                    ltp_ce = ce_documents[strike]['lastPrice']
                    min_ltp_ce = ltp_ce*(1-PERCENTAGE)
                    max_ltp_ce = ltp_ce*(1+PERCENTAGE)
                    
                    for strike_ in pe_documents:
                        ltp_pe = pe_documents[strike_]['lastPrice']
                        
                        if ltp_pe >= min_ltp_ce and ltp_pe <= max_ltp_ce:
                            pairs.add((ce_documents[strike]['monthly_Options_CE'], pe_documents[strike_]['monthly_Options_PE']))
                
                    
                for strike in pe_documents:
                    ltp_pe = pe_documents[strike]['lastPrice']
                    min_ltp_pe = ltp_pe*(1-PERCENTAGE)
                    max_ltp_pe = ltp_pe*(1+PERCENTAGE)
                    
                    for strike_ in ce_documents:
                        ltp_ce = ce_documents[strike_]['lastPrice']
                        
                        if ltp_ce >= min_ltp_pe and ltp_ce <= max_ltp_pe:
                            pairs.add((ce_documents[strike_]['monthly_Options_CE'], pe_documents[strike]['monthly_Options_PE']))
                
    
                # remove duplicate elements from the set
                pairs = set(pairs)
                
                for pair in pairs:
                    ticker_a, ticker_b = pair
                       
                    trade_a = self.generateMarketOrderBuyIndexOption(ticker_a, self.quantity, 'ENTRY')
                    trade_b = self.generateMarketOrderBuyIndexOption(ticker_b, self.quantity, 'ENTRY')
                    
                    self.sendTrade(trade_a)
                    self.sendTrade(trade_b)
                    
                    self.insertOrder(ticker_a, trade_a)
                    self.insertOrder(ticker_b, trade_b)
                    
                    self.ticker_pairs.append(f'{ticker_a}-{ticker_b}')
                
                
            time.sleep(300)
    
    def exitStrategy(self):
        while True:
            for ticker_pair in self.ticker_pairs:
                ticker_a, ticker_b = ticker_pair.split('-')
                
                orders_a = self.getOrder(ticker_a)['data']
                orders_b = self.getOrder(ticker_b)['data']
                
                entry_a, entry_b = 0, 0
                count_a, count_b = 0, 0
                
                for order_a, order_b in zip(orders_a, orders_b):
                    entry_a += order_a['entry_price']
                    entry_b += order_b['entry_price']
                    
                    count_a += 1; count_b += 1
                
                entry_a /= count_a
                entry_b /= count_b
                
                live_a = self.getLiveData(ticker_a, 'index')
                live_b = self.getLiveData(ticker_b, 'index')
                
                pnl_a = (live_a['last_price'] - entry_a) / live_a['last_price']
                pnl_b = (live_b['last_price'] - entry_b) / live_b['last_price']
                
                if pnl_a + pnl_b >= 4:
                    trade_a = self.generateMarketOrderSellIndexOption(ticker_a, self.quantity, 'EXIT')
                    trade_b = self.generateMarketOrderSellIndexOption(ticker_b, self.quantity, 'EXIT')
                    
                    self.sendTrade(trade_a)
                    self.sendTrade(trade_b)
            
            time.sleep(5)

def main():
    app = Worker5('worker_5_index')
    app.start()