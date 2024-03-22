import requests
import numpy as np
from pydantic import BaseModel, Field
from langchain.agents import tool  # Use the @tool decorator
from cachetools import cached, TTLCache

# Define a simple cache to store responses
cache = TTLCache(maxsize=100, ttl=300)

# Define models for input validation
class CryptoDataInput(BaseModel):
    symbol: str = Field(..., description="The symbol of the cryptocurrency (e.g., BTC, ETH)")

@tool
@cached(cache)
def get_coingecko_market_data(coin_id: str, vs_currency: str = "usd") -> str:
    """
    Fetches and returns market data for a specified cryptocurrency using CoinGecko API.
    """
    api_url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": vs_currency, "ids": coin_id}
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()[0]  # Get the first item from the list
        return {
            "Price": data.get('current_price'),
            "Market Cap": data.get('market_cap'),
            "24h Volume": data.get('total_volume'),
            "24h Change": data.get('price_change_percentage_24h'),
            "7d Change": data.get('price_change_percentage_7d'),
        }
    except Exception as e:
        return f"Error fetching market data: {e}"

@tool
@cached(cache)
def get_liquidity_score(coin_id: str) -> str:
    """
    Fetches and returns the liquidity score of a specified cryptocurrency using CoinGecko API.
    """
    coin_data_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    try:
        response = requests.get(coin_data_url)
        response.raise_for_status()
        data = response.json()
        return f"The liquidity score of {coin_id} is {data.get('liquidity_score', 'N/A')}."
    except Exception as e:
        return f"Error fetching liquidity score: {e}"

@tool
@cached(cache)
def get_market_data_overview() -> str:
    """
    Fetches and returns an overview of market data including total market cap, volume, and Bitcoin dominance.
    """
    api_url = "https://api.coingecko.com/api/v3/global"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json().get('data', {})
        total_market_cap = data.get('total_market_cap', {}).get('usd', 'N/A')
        total_volume = data.get('total_volume', {}).get('usd', 'N/A')
        bitcoin_dominance = data.get('market_cap_percentage', {}).get('btc', 'N/A')
        return {
            "Total Market Cap": total_market_cap,
            "Total Volume": total_volume,
            "Bitcoin Dominance": f"{bitcoin_dominance} %",
        }
    except Exception as e:
        return f"Error fetching market data overview: {e}"

@tool
@cached(cache)
def get_top_gainers(vs_currency: str = "usd", limit: int = 10) -> str:
    """
    Fetches and returns the top gainers in the market.
    """
    api_url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h",
    }
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        gainers = sorted(data, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)
        return [{coin['id']: coin['price_change_percentage_24h']} for coin in gainers]
    except Exception as e:
        return f"Error fetching top gainers: {e}"

@tool
@cached(cache)
def get_top_losers(vs_currency: str = "usd", limit: int = 10) -> str:
    """
    Fetches and returns the top losers in the market.
    """
    api_url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h",
    }
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        losers = sorted(data, key=lambda x: x.get('price_change_percentage_24h', 0))
        return [{coin['id']: coin['price_change_percentage_24h']} for coin in losers]
    except Exception as e:
        return f"Error fetching top losers: {e}"

@tool
@cached(cache)
def get_trending_coins() -> str:
    """
    Fetches and returns the trending coins on CoinGecko.
    """
    api_url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        coins = data.get('coins', [])
        return [coin['item']['id'] for coin in coins]
    except Exception as e:
        return f"Error fetching trending coins: {e}"
    
    
@tool
@cached(cache)
def get_macd(coin_id: str, vs_currency: str = "usd", short_term: int = 12, long_term: int = 26, signal: int = 9) -> str:
    """
    Calculates the Moving Average Convergence Divergence (MACD) for a specified cryptocurrency.

    Parameters:
    coin_id (str): The CoinGecko ID of the cryptocurrency.
    vs_currency (str): The fiat currency to compare against (default: 'usd').
    short_term (int): The number of days for the short term EMA (default: 12).
    long_term (int): The number of days for the long term EMA (default: 26).
    signal (int): The number of days for the signal line EMA (default: 9).

    Returns:
    str: A string containing the MACD value.
    """
    historical_data_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {'vs_currency': vs_currency, 'days': max(long_term, short_term, signal)}

    try:
        response = requests.get(historical_data_url, params=params)
        response.raise_for_status()
        data = response.json()
        prices = [price[1] for price in data['prices']]

        # Calculate EMAs
        short_ema = pd.Series(prices).ewm(span=short_term).mean().iloc[-1]
        long_ema = pd.Series(prices).ewm(span=long_term).mean().iloc[-1]
        macd = short_ema - long_ema
        signal_line = pd.Series(macd).ewm(span=signal).mean().iloc[-1]

        return f"MACD: {macd:.2f}, Signal Line: {signal_line:.2f} for {coin_id} in {vs_currency}."
    except requests.RequestException as e:
        return f"HTTP error occurred: {e}"
    except ValueError as e:
        return f"Error decoding JSON: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    
    
