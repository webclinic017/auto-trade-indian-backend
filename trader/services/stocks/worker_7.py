from interfaces.tradeapp import TradeApp
import datetime, time, json

class Worker7(TradeApp):
    
    def entryStrategy(self):
        while True:
            now = datetime.datetime.now()

            if now.time() >= datetime.time(hour=9, minute=15):
                for ticker in self.getTickers():
                    live_data = self.getLiveData(ticker)
                    ohlc = live_data['ohlc']

                    print(json.dumps({
                        'ohlc': ohlc,
                        'ticker': ticker
                    }, indent=2))

                    if ohlc['open'] == ohlc['low'] and 'CE' in ticker:
                        trade = self.generateLimitOrderBuyStockOption(ticker, 'ENTRY_STOCK')
                        self.sendTrade(trade)
                            
                    elif ohlc['open'] == ohlc['high'] and 'PE' in ticker:
                        trade = self.generateLimitOrderBuyStockOption(ticker, 'ENTRY_STOCK')
                        self.sendTrade(trade)


            elif now.time() > datetime.time(hour=9, minute=20):
                return

            time.sleep(5)


    def exitStrategy(self):
        while True:
            orders = self.getAllOrders()
            
            for order in orders:
                ticker = order['ticker']
                entry_price = self.averageEntryprice(order['data'])
                live_data = self.getLiveData(ticker)
                ohlc = live_data['ohlc']

                pnl = self.getPnl(entry_price, live_data['last_price'])
                if pnl >= 4 or live_data['last_price'] < ohlc['low']:
                    print('-'*10 + 'EXIT' + '-'*10)
                    print(json.dumps({
                        'ticker': ticker,
                        'pnl': pnl,
                    }, indent=2))
                    print('-'*10 + 'EXIT' + '-'*10)

                    trade = self.generateLimitOrderSellStockOption(ticker, 'EXIT')
                    self.sendTrade(trade)


def main():
    app = Worker7(name='woker_7_stock')
    app.start()