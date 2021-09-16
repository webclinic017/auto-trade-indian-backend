from interfaces.tradeapp import TradeApp
from nsetools import nse

class Worker6(TradeApp):

    def entryStrategy(self):
        for ticker in self.index_tickers:
            q = nse.get_quote(ticker)
            pass


    def exitStrategy(self):
        return



if __name__ == '__main__':
    app = Worker6(name='worker_6_index')