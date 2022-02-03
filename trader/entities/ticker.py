from datetime import datetime
from entities.zerodha import HistoricalDataInterval, ZerodhaKite
from kiteconnect import KiteConnect
import json
import os
import math
import datetime


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

        for i in range(1, n + 1):
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
        banknifty_atm = (math.ceil(bank_nifty_live.last_price) // 100) * 100

        for i in range(1, n + 1):
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

            yield IndexTicker(ce, pe, "BANKNIFTY")

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

    def stocks_historical_prices(self):
        factors = json.loads(open("/app/data/factors.json", "r").read())
        historical_tickers = {}

        for ticker in factors:
            historical_data = self.zerodha.historical_data(
                ticker,
                datetime.date.today() - datetime.timedelta(days=365),
                datetime.date.today() - datetime.timedelta(days=1),
                HistoricalDataInterval.INTERVAL_1_DAY,
            )

            prev_day_open = historical_data[-1].open
            prev_day_high = historical_data[-1].high
            prev_day_low = historical_data[-1].low
            prev_day_close = historical_data[-1].close
            df = self.zerodha.get_ohlc_data_frame(historical_data)
            df["4weekhigh"] = df["high"].rolling(20).max()
            df["4weeklow"] = df["low"].rolling(20).min()
            df["high3"] = df["high"].rolling(3).max()
            df["low3"] = df["low"].rolling(3).min()

            cpr = (prev_day_high + prev_day_low + prev_day_close) / 3
            bc = (prev_day_high + prev_day_low) / 2
            tc = (cpr - bc) + cpr
            cpr_range = "narrow" if ((tc - bc) / prev_day_close) < 0.002 else "broad"
            gann22 = ((prev_day_close) ** 0.5 + 0.125) ** 2
            gann45 = ((prev_day_close) ** 0.5 + 0.25) ** 2
            gann90 = ((prev_day_close) ** 0.5 + 0.5) ** 2
            gann135 = ((prev_day_close) ** 0.5 + 0.75) ** 2
            gann180 = ((prev_day_close) ** 0.5 + 1) ** 2
            gann225 = ((prev_day_close) ** 0.5 + 1.25) ** 2
            gann270 = ((prev_day_close) ** 0.5 + 1.5) ** 2
            gann315 = ((prev_day_close) ** 0.5 + 1.75) ** 2
            gann360 = ((prev_day_close) ** 0.5 + 2) ** 2

            gannminus22 = ((prev_day_close) ** 0.5 - 0.125) ** 2
            gannminu45 = ((prev_day_close) ** 0.5 - 0.25) ** 2
            gannminu90 = ((prev_day_close) ** 0.5 - 0.5) ** 2
            gannminus135 = ((prev_day_close) ** 0.5 - 0.75) ** 2
            gannminus180 = ((prev_day_close) ** 0.5 - 1) ** 2
            gannminus225 = ((prev_day_close) ** 0.5 - 1.25) ** 2
            gannminus270 = ((prev_day_close) ** 0.5 - 1.5) ** 2
            gannminus315 = ((prev_day_close) ** 0.5 - 1.75) ** 2
            gannminus360 = ((prev_day_close) ** 0.5 - 2) ** 2

            four_week_high = df["4weekhigh"].iloc[-1]
            four_week_low = df["4weeklow"].iloc[-1]
            three_day_high = df["high3"].iloc[-1]
            three_day_low = df["low3"].iloc[-1]

            historical_cal = {
                "ticker": ticker,
                "prev_high": prev_day_high,
                "prev_low": prev_day_low,
                "4weekhigh": four_week_high,
                "4weeklow": four_week_low,
                "cpr": cpr,
                "bc": bc,
                "tc": tc,
                "cpr_range": cpr_range,
                "gann22": gann22,
            }

            historical_tickers[ticker] = historical_cal

        return historical_tickers

    def get_stock_historical_tickers(self):
        with open("/tmp/stock_tickers.json", "r") as f:
            data = json.loads(f.read())

        return data
