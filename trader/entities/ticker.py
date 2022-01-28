from entities.zerodha import ZerodhaKite
from kiteconnect import KiteConnect
import json
import os
import math


class Ticker:
    def __init__(self, tradingsymbol, lot_size, instrument_token):
        self.tradingsymbol = tradingsymbol
        self.lot_size = lot_size
        self.instrument_token = instrument_token


class StockTicker:
    def __init__(self, ce_ticker: Ticker, pe_ticker: Ticker, ticker: Ticker):
        self.ce_ticker = ce_ticker
        self.pe_ticker = pe_ticker
        self.ticker = ticker


class IndexTicker:
    def __init__(self, ce_ticker: Ticker, pe_ticker: Ticker, ticker_type: str):
        self.ce_ticker = ce_ticker
        self.pe_ticker = pe_ticker
        self.ticker_type = ticker_type


class TickerGenerator:
    NIFTY_50 = "NIFTY 50"
    BANK_NIFTY = "NIFTY BANK"

    def __init__(
        self,
        stock_year: str,
        stock_month: str,
        index_year: str,
        index_month: str,
        index_week: str,
    ):
        self.zerodha = ZerodhaKite(
            KiteConnect(
                api_key=os.environ["API_KEY"], access_token=os.environ["ACCESS_TOKEN"]
            )
        )
        self.stock_year = stock_year
        self.stock_month = stock_month

        self.index_year = index_year
        self.index_month = index_month
        self.index_week = index_week

        self.instruments = self.zerodha.token_map

    def index(self, n: int):
        nifty_live = self.zerodha.live_data(self.NIFTY_50)
        nifty_atm = (math.ceil(nifty_live.last_price) // 50) * 50

        for i in range(1, n+1):
            ce_ticker = (
                "NIFTY"
                + self.index_year
                + self.index_month
                + self.index_week
                + str(i * 50 + nifty_atm)
                + "CE"
            )

            pe_ticker = (
                "NIFTY"
                + self.index_year
                + self.index_month
                + self.index_week
                + str(nifty_atm - i * 50)
                + "PE"
            )

            
            if (ce_ticker not in self.instruments) or (
                pe_ticker not in self.instruments
            ):
                continue

            ce = Ticker(
                ce_ticker,
                self.instruments[ce_ticker]["lot_size"],
                self.instruments[ce_ticker]["instrument_token"],
               
            )
            pe = Ticker(
                pe_ticker,
                self.instruments[pe_ticker]["lot_size"],
                self.instruments[pe_ticker]["instrument_token"],
               
            )

            yield IndexTicker(ce, pe, "NIFTY")

        
        bank_nifty_live = self.zerodha.live_data(self.BANK_NIFTY)
        banknifty_atm = (math.ceil(bank_nifty_live.last_price)//100) * 100

        for i in range(1, n+1):
            ce_ticker = (
                "BANKNIFTY"
                + self.index_year
                + self.index_month
                + self.index_week
                + str(i * 100 + banknifty_atm)
                + "CE"
            )

            pe_ticker = (
                "BANKNIFTY"
                + self.index_year
                + self.index_month
                + self.index_week
                + str(banknifty_atm - i * 100)
                + "PE"
            )
            
            if (ce_ticker not in self.instruments) or (pe_ticker not in self.instruments):
                continue
            
            ce = Ticker(ce_ticker, self.instruments[ce_ticker]['lot_size'], self.instruments[ce_ticker]['instrument_token'])
            pe = Ticker(pe_ticker, self.instruments[pe_ticker]['lot_size'], self.instruments[pe_ticker]['instrument_token'])
            
            yield IndexTicker(ce, pe, 'BANKNIFTY')

    def stocks(self):
        factors = json.loads(open("/app/data/factors.json", "r").read())

        for tradingsymbol in factors:
            try:
                live_data = self.zerodha.live_data(tradingsymbol)
            except:
                continue

            atm_price = (
                math.ceil(live_data.last_price) // factors[tradingsymbol]
            ) * factors[tradingsymbol]

            ce_ticker = (
                tradingsymbol
                + self.stock_year
                + self.stock_month
                + str(atm_price + factors[tradingsymbol])
                + "CE"
            )
            pe_ticker = (
                tradingsymbol
                + self.stock_year
                + self.stock_month
                + str(atm_price - factors[tradingsymbol])
                + "PE"
            )

            if (
                (ce_ticker not in self.instruments)
                or (pe_ticker not in self.instruments)
                or (tradingsymbol not in self.instruments)
            ):
                continue

            ce = Ticker(
                ce_ticker,
                self.instruments[ce_ticker]["lot_size"],
                self.instruments[ce_ticker]["instrument_token"],
            )
            pe = Ticker(
                pe_ticker,
                self.instruments[pe_ticker]["lot_size"],
                self.instruments[pe_ticker]["instrument_token"],
            )

            ticker = Ticker(
                tradingsymbol,
                self.instruments[tradingsymbol]["lot_size"],
                self.instruments[tradingsymbol]["instrument_token"],
            )

            yield StockTicker(ce, pe, ticker)
