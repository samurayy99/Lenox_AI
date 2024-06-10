import logging
import pandas as pd
from pycoingecko import CoinGeckoAPI
from typing import List
import numpy as np
from functools import lru_cache
from langchain.agents import tool

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize CoinGecko API client
cg = CoinGeckoAPI()

@tool
def get_market_data(coin_ids: List[str], vs_currency: str = 'usd') -> str:
    """
    Fetches and returns current market data for specified cryptocurrencies.
    """
    try:
        data = cg.get_price(ids=','.join(coin_ids), vs_currencies=vs_currency)
        return str(data)
    except Exception as e:
        logging.error(f"Exception occurred while fetching market data: {str(e)}")
        return "Failed to fetch market data."

@tool
@lru_cache(maxsize=100)
def get_historical_market_data(coin_id: str, vs_currency: str = 'usd', days: int = 90) -> str:
    """
    Fetches historical market data for a specified cryptocurrency over a number of days.
    """
    try:
        data = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency=vs_currency, days=days)
        return str(data)
    except Exception as e:
        logging.error(f"Exception occurred while fetching historical market data: {str(e)}")
        return "Failed to fetch historical market data."

@tool
def get_ohlc(coin_id: str, vs_currency: str = 'usd', days: int = 1) -> str:
    """
    Fetches OHLC (Open, High, Low, Close) data for a specified cryptocurrency for the last number of days.
    """
    try:
        data = cg.get_coin_ohlc_by_id(id=coin_id, vs_currency=vs_currency, days=days)
        return str(data)
    except Exception as e:
        logging.error(f"Exception occurred while fetching OHLC data: {str(e)}")
        return "Failed to fetch OHLC data."

@tool
def get_trending_cryptos() -> str:
    """
    Retrieves the list of trending cryptocurrencies on CoinGecko.
    """
    try:
        data = cg.get_search_trending()
        trending_names = [item['item']['name'] for item in data['coins']]
        return ', '.join(trending_names)
    except Exception as e:
        logging.error(f"Exception occurred while fetching trending cryptocurrencies: {str(e)}")
        return "Failed to fetch trending cryptocurrencies."

@tool
def calculate_macd(prices: List[float], slow: int = 26, fast: int = 12, signal: int = 9) -> str:
    """
    Calculates the Moving Average Convergence Divergence (MACD) for a series of prices.
    """
    try:
        exp1 = pd.Series(prices)
        ema_fast = exp1.ewm(span=fast, adjust=False).mean()
        ema_slow = exp1.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        macd_value = macd.iloc[-1]
        signal_line_value = signal_line.iloc[-1]
        trend = "bullish" if macd_value > signal_line_value else "bearish"
        return (
            f"The Moving Average Convergence Divergence (MACD) for Solana for the last month is {macd_value:.2f}, "
            f"and the Signal Line is {signal_line_value:.2f}. The MACD is a trend-following momentum indicator "
            f"that shows the relationship between two moving averages of a security’s price. A MACD above the "
            f"Signal Line suggests a bullish trend, indicating it might be a good time to consider buying. Conversely, "
            f"a MACD below the Signal Line suggests a bearish trend, which might not be the best time to buy. "
            "Always consult with a financial advisor or do further research before making investment decisions."
        )
    except Exception as e:
        logging.error(f"Exception occurred while calculating MACD: {str(e)}")
        return "Failed to calculate MACD."


@tool
def get_exchange_rates(coin_id: str = 'bitcoin') -> str:
    """
    Retrieves exchange rates for a given coin (default is Bitcoin) to all other currencies.
    """
    try:
        data = cg.get_exchange_rates()
        rates = data['rates']
        base_rate = rates[coin_id]['value']
        exchange_rates = {cur: rate['value'] / base_rate for cur, rate in rates.items()}
        return str(exchange_rates)
    except Exception as e:
        logging.error(f"Exception occurred while fetching exchange rates: {str(e)}")
        return "Failed to fetch exchange rates."

@tool
def calculate_rsi(prices: List[float], period: int = 14) -> str:
    """
    Calculates the Relative Strength Index (RSI) for a given series of prices.
    """
    try:
        prices = np.array(prices)
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1.+rs)

        for i in range(period, len(prices)):
            delta = deltas[i-1]  # because the diff is 1 shorter
            upval = delta if delta > 0 else 0.
            downval = -delta if delta < 0 else 0.

            up = (up*(period-1) + upval)/period
            down = (down*(period-1) + downval)/period

            rs = up/down
            rsi[i] = 100. - 100./(1.+rs)

        return f"RSI: {rsi[-1]}"
    except Exception as e:
        logging.error(f"Exception occurred while calculating RSI: {str(e)}")
        return "Failed to calculate RSI."
