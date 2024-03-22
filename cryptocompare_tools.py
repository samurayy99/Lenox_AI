import requests
import os
from pydantic import BaseModel, Field
import datetime
from langchain.agents import tool  # Use the @tool decorator

# Define models for input validation
class CryptoDataInput(BaseModel):
    symbol: str = Field(..., description="The symbol of the cryptocurrency (e.g., BTC, ETH)")


@tool
def get_historical_daily_stats(symbol: str, currency: str = "USD") -> str:
    """
    Returns historical day statistics for the specified cryptocurrency symbol using CryptoCompare API.
    """
    api_url = f"https://min-api.cryptocompare.com/data/histoday?fsym={symbol}&tsym={currency}&limit=30&api_key={os.getenv('CRYPTOCOMPARE_API_KEY')}"
    try:
        response = requests.get(api_url)
        data = response.json()
        if not data or 'Data' not in data:
            raise Exception("Error fetching historical day statistics.")
        historical_data = data['Data']
        formatted_data = '\n'.join([f"Date: {datetime.datetime.fromtimestamp(day['time']).strftime('%Y-%m-%d')}, Close: {day['close']}" for day in historical_data])
        return f"Historical daily stats for {symbol} in {currency}:\n{formatted_data}"
    except requests.RequestException as e:
        return f"Error during API request: {str(e)}"

@tool
def get_top_trading_pairs(symbol: str, limit: int = 5) -> str:
    """
    Returns the top trading pairs for the specified cryptocurrency symbol using CryptoCompare API.
    """
    api_url = f"https://min-api.cryptocompare.com/data/top/pairs?fsym={symbol}&limit={limit}&api_key={os.getenv('CRYPTOCOMPARE_API_KEY')}"
    try:
        response = requests.get(api_url)
        data = response.json()
        if not data or 'Data' not in data:
            raise Exception("Error fetching top trading pairs.")
        pairs_data = data['Data']
        formatted_data = '\n'.join([f"Market: {pair['exchange']}, Pair: {pair['toSymbol']}, Volume24h: {pair['volume24h']}" for pair in pairs_data])
        return f"Top trading pairs for {symbol}:\n{formatted_data}"
    except requests.RequestException as e:
        return f"Error during API request: {str(e)}"

@tool
def get_news(symbol: str) -> str:
    """
    Returns the latest news for the specified cryptocurrency symbol using CryptoCompare API.
    """
    api_url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={symbol}&api_key={os.getenv('CRYPTOCOMPARE_API_KEY')}"
    try:
        response = requests.get(api_url)
        data = response.json()
        if not data or 'Data' not in data:
            raise Exception("Error fetching news.")
        news_data = data['Data']
        formatted_news = '\n'.join([f"Title: {news['title']}, URL: {news['url']}" for news in news_data])
        return f"Latest news for {symbol}:\n{formatted_news}"
    except requests.RequestException as e:
        return f"Error during API request: {str(e)}"
