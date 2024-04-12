import requests
import os
import datetime
from pydantic import BaseModel, Field
from langchain.agents import tool  # Use the @tool decorator

# Define models for input validation
class CryptoDataInput(BaseModel):
    symbol: str = Field(..., description="The symbol of the cryptocurrency (e.g., BTC, ETH)")
    limit: int = Field(30, description="The limit for how many days to fetch data for.")



@tool
def get_social_stats(symbol: str, limit: int = 5) -> str:
    """
    Returns social media statistics for the specified cryptocurrency symbol using CryptoCompare API.
    """
    # Manually construct the CryptoDataInput object if needed
    # input = CryptoDataInput(symbol=symbol, limit=limit)
    
    api_url = f"https://min-api.cryptocompare.com/data/social/coin/latest?coinId={symbol}&api_key={os.getenv('CRYPTOCOMPARE_API_KEY')}"
    try:
        response = requests.get(api_url)
        data = response.json()
        if not data or 'Data' not in data:
            raise Exception("Error fetching social media statistics.")
        social_data = data['Data']
        twitter_followers = social_data['Twitter']['followers']
        reddit_subscribers = social_data['Reddit']['subscribers']
        formatted_social_stats = f"Twitter Followers: {twitter_followers}, Reddit Subscribers: {reddit_subscribers}"
        return f"Social stats for {symbol}:\n{formatted_social_stats}"
    except requests.RequestException as e:
        return f"Error during API request: {str(e)}"

@tool
def get_top_trading_pairs(symbol: str, limit: int = 5) -> str:
    """
    Returns the top trading pairs for the specified cryptocurrency symbol using CryptoCompare API.
    """
    api_url = f"https://min-api.cryptocompare.com/data/top/pairs?fsym={input.symbol}&limit={input.limit}&api_key={os.getenv('CRYPTOCOMPARE_API_KEY')}"
    try:
        response = requests.get(api_url)
        data = response.json()
        if not data or 'Data' not in data:
            raise Exception("Error fetching top trading pairs.")
        pairs_data = data['Data']
        formatted_data = '\n'.join([f"Market: {pair['exchange']}, Pair: {pair['toSymbol']}, Volume24h: {pair['volume24h']}" for pair in pairs_data])
        return f"Top trading pairs for {input.symbol}:\n{formatted_data}"
    except requests.RequestException as e:
        return f"Error during API request: {str(e)}"

@tool
def get_news(symbol: str, limit: int = 5) -> str:
    """
    Returns the latest news for the specified cryptocurrency symbol using CryptoCompare API.
    """
    api_url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={input.symbol}&api_key={os.getenv('CRYPTOCOMPARE_API_KEY')}"
    try:
        response = requests.get(api_url)
        data = response.json()
        if not data or 'Data' not in data:
            raise Exception("Error fetching news.")
        news_data = data['Data']
        formatted_news = '\n'.join([f"Title: {news['title']}, URL: {news['url']}" for news in news_data])
        return f"Latest news for {input.symbol}:\n{formatted_news}"
    except requests.RequestException as e:
        return f"Error during API request: {str(e)}"
