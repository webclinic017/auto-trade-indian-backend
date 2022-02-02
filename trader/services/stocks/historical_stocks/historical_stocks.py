from interfaces.bot import TradeBot
from entities.orders import Order
from entities.ticker import TickerGenerator
import json

class HistoricalStocks(TradeBot):
    def entry_strategy(self):
        tickers = TickerGenerator("", "", "", "", "").get_stock_historical_tickers()
        print(json.dumps(tickers, indent=2))

    def exit_strategy(self, order: Order):
        return
