from interfaces.tradeapp import TradeApp
import datetime, time, json

class Worker7(TradeApp):

    tickers = []
    year = '21'
    month = 'SEP'

    entered_tickers = set()

    def entryStrategy(self):
        while True:
            now = datetime.datetime.now()

            if now.time() >= datetime.time(hour=9, minute=15):
                for ticker in self.tickers:
                    live_data = self.getLiveData(ticker)
                    ohlc = live_data['ohlc']

                    print(json.dumps({
                        'ohlc': ohlc,
                        'ticker': ticker
                    }, indent=2))

                    if ohlc['open'] == ohlc['low']:
                        
                        try:
                            compare_file = self.getDataStockTicker(ticker)
                        except:
                            time.sleep(1)
                            continue

                        latest_compare = compare_file['data'].pop()
                        atm = latest_compare['atm']
                        ticker_ = ticker + self.year + self.month + atm + 'CE'
                        
                        print('ENTERED: ' + ticker_)
                        
                        if ticker_ not in self.entered_tickers:
                            trade = self.generateLimitOrderBuyStockOption(ticker, 'ENTRY_STOCK')
                            self.sendTrade(trade)
                            self.entered_tickers.add((ticker_, ticker))
                    elif ohlc['open'] == ohlc['high']:
                        
                        try:
                            compare_file = self.getDataStockTicker(ticker)
                        except:
                            time.sleep(1)
                            continue

                        latest_compare = compare_file['data'].pop()
                        atm = latest_compare['atm']
                        ticker_ = ticker + self.year + self.month + atm + 'PE'

                        if ticker_ not in self.entered_tickers:
                            trade = self.generateLimitOrderBuyStockOption(ticker, 'ENTRY_STOCK')
                            self.sendTrade(trade)
                            self.entered_tickers.add((ticker_, ticker))


            elif now.time() > datetime.time(hour=9, minute=20):
                return

            time.sleep(5)


    def exitStrategy(self):
        while True:
            for ticker, ticker_mod in self.entered_tickers:
                order = self.getOrder(ticker_mod)
                entry_price = self.averageEntryprice(order['data'])
                live_data = self.getLiveData(ticker)
                ohlc = live_data['ohlc']

                pnl = self.getPnl(entry_price, live_data['last_price'])
                if pnl >= 4 or live_data['last_price'] < ohlc['low']:
                    print('-'*10 + 'EXIT' + '-'*10)
                    print(json.dumps({
                        'ticker': ticker_mod,
                        'pnl': pnl,
                    }, indent=2))
                    print('-'*10 + 'EXIT' + '-'*10)

                    trade = self.generateLimitOrderSellStockOption(ticker_mod, 'EXIT')
                    self.sendTrade(trade)


def main():
    app = Worker7(name='woker_7_stock')
    app.start()