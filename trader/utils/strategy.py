from entities.zerodha import LiveTicker, ZerodhaKite
from entities.orders import Order
from typing import List
import numpy as np


class StrategyUtil:
    @classmethod
    def get_average_entry_price_of_orders(cls, orders: List[Order]):
        return np.average(np.array([order.average_entry_price for order in orders]))

    @classmethod
    def get_average_price_of_orders(cls, orders: List[Order], zerodha: ZerodhaKite):
        return np.average(
            np.array(
                [zerodha.live_data(order.trading_symbol).last_price for order in orders]
            )
        )
