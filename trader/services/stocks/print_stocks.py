from interfaces.bot import TradeBot
from entities.ticker import TickerGenerator


class PrintTickers(TradeBot):
    def entry_strategy(self):
        for ticker in self.ticker_generator.tickers():
            print(ticker.ce_ticker.tradingsymbol, ticker.ce_ticker.lot_size)
            print(ticker.pe_ticker.tradingsymbol, ticker.pe_ticker.lot_size)

    def exit_strategy(self, order):
        return

    def start(self):
        self.ticker_generator = TickerGenerator("22", "JAN")

        super().start()
