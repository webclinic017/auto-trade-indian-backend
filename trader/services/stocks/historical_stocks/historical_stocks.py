from interfaces.bot import TradeBot
from entities.orders import Order
from entities.ticker import TickerGenerator


class HistoricalStocks(TradeBot):
    def entry_strategy(self):
        TickerGenerator("", "", "", "", "").stocks_historical_prices()

    def exit_strategy(self, order: Order):
        return
