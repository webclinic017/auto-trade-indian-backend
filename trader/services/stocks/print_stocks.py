from interfaces.bot import TradeBot
from entities.ticker import TickerGenerator


class PrintTickers(TradeBot):
    def entry_strategy(self):
        for tick in self.ticker_generator.index(5):
            print(tick.ce_ticker.tradingsymbol,tick.pe_ticker.tradingsymbol)
        
        for ticker in self.ticker_generator.stocks():
            print(ticker.ce_ticker.tradingsymbol, ticker.ce_ticker.lot_size)
            print(ticker.pe_ticker.tradingsymbol, ticker.pe_ticker.lot_size)
            

    def exit_strategy(self, order):
        return

    def start(self):
        self.ticker_generator = TickerGenerator("22", "JAN", "22", "2", "03")

        super().start()
