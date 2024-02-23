import datetime 
from pydantic import BaseModel, Field
import requests
import os
import logging
from langchain.agents import tool  # Use the @tool decorator

# Configure logging at the beginning of the script
logging.basicConfig(level=logging.DEBUG)

# Define models for input validation
class CryptoDataInput(BaseModel):
    symbol: str = Field(..., description="The symbol of the cryptocurrency (e.g., BTC, ETH)")

class RedditDataInput(BaseModel):
    subreddit: str = Field(..., description="Name of the subreddit (e.g., 'CryptoCurrency')")
    category: str = Field(default='hot', description="Category of posts to fetch ('hot', 'new', 'top')")

# Reddit data fetching function
@tool
def get_reddit_data(subreddit: str, category: str = 'hot') -> str:
    """
    Fetches and returns the latest posts from a specified subreddit category.
    """
    access_token = os.getenv("REDDIT_ACCESS_TOKEN")  # Ensure you have this environment variable set
    validated_input = RedditDataInput(subreddit=subreddit, category=category)
    headers = {
        'Authorization': f'bearer {access_token}',
        'User-Agent': os.getenv("REDDIT_USER_AGENT", "RedditDataFetcher/0.1")
    }
    api_url = f"https://oauth.reddit.com/r/{validated_input.subreddit}/{validated_input.category}"
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        posts = data['data']['children']
        posts_str = "\n\n".join([f"Title: {post['data']['title']}\nURL: {post['data']['url']}" for post in posts[:5]])
        return f"Latest posts from r/{validated_input.subreddit}:\n{posts_str}"
    else:
        return f"Error: Unable to fetch data from Reddit. Status code: {response.status_code}"

# Function to fetch current price data from CoinGecko
@tool
def get_coingecko_market_data(coin_id: str, vs_currency: str = "usd") -> str:
    """
    Fetches and returns market data for a specified cryptocurrency using CoinGecko API.
    """
    api_url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "ids": coin_id,
    }
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        if data and len(data) > 0:
            coin_data = data[0]  # Assuming the first item is the coin we're interested in
            price = coin_data['current_price']
            market_cap = coin_data['market_cap']
            volume_24h = coin_data['total_volume']
            return (f"Price: {price} {vs_currency}, Market Cap: {market_cap}, "
                    f"24h Volume: {volume_24h} for {coin_id}.")
        else:
            return "Failed to fetch data from CoinGecko or coin not found."
    except Exception as e:
        return f"Exception occurred: {str(e)}"


@tool  # Markiere diese Funktion als ein Tool
def get_crypto_data(symbol: str) -> str:
    """
    Returns the current price of the specified cryptocurrency symbol.
    """
    validated_input = CryptoDataInput(symbol=symbol)
    api_url = "https://min-api.cryptocompare.com/data/price"
    params = {
        "fsym": validated_input.symbol,
        "tsyms": "USD",
        "api_key": os.getenv('CRYPTOCOMPARE_API_KEY')
    }
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        if not data:
            raise Exception("Error fetching cryptocurrency data.")
        price = data['USD']
        return f"The current price of {validated_input.symbol} is ${price}."
    except requests.RequestException as e:
        return f"Error during API request: {str(e)}"


@tool
def get_historical_crypto_price(symbol: str, currency: str = "USD", limit: int = 30, aggregate: int = 1, toTs: datetime.datetime = datetime.datetime.now()) -> str:
    """
    Fetches and returns historical price data for a specified cryptocurrency.

    Parameters:
    - symbol (str): The symbol of the cryptocurrency (e.g., BTC, ETH).
    - currency (str): The fiat currency to convert into (default: USD).
    - limit (int): The number of data points to return.
    - aggregate (int): Aggregation level (default: 1).
    - toTs (datetime): Last data point timestamp (default: now).

    Returns:
    str: A string containing historical prices.
    """
    try:
        timestamp = int(toTs.timestamp())
        api_url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym={currency}&limit={limit}&aggregate={aggregate}&toTs={timestamp}&api_key={os.getenv('CRYPTOCOMPARE_API_KEY')}"
        response = requests.get(api_url)
        data = response.json()
        if data.get("Response") == "Success":
            prices = data["Data"]["Data"]
            prices_str = "\n".join([f"Time: {datetime.datetime.fromtimestamp(price['time']).strftime('%Y-%m-%d')}, Price: {price['close']}" for price in prices])
            return f"Historical prices for {symbol} in {currency}:\n{prices_str}"
        else:
            return "Error: Unable to fetch historical price data."
    except Exception as e:
        return f"Exception occurred: {str(e)}" 


@tool
def get_lunarcrush_galaxy_score(coin: str) -> str:
    """Fetches the current Galaxy Score for a given cryptocurrency."""
    api_url = f"https://lunarcrush.com/api4/public/coins/{coin}/v1"
    params = {
        "key": os.getenv('LUNARCRUSH_API_KEY')  # Your LunarCrush API Key
    }
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        galaxy_score = data.get('data', {}).get('galaxy_score')
        if galaxy_score:
            return f"The LunarCrush Galaxy Score for {coin} is {galaxy_score}."
        else:
            return "Galaxy Score not found."
    except Exception as e:
        return f"Error fetching LunarCrush Galaxy Score: {str(e)}"

@tool
def get_lunarcrush_alt_rank(coin: str) -> str:
    """Fetches the current AltRank for a given cryptocurrency."""
    api_url = f"https://lunarcrush.com/api4/public/coins/{coin}/v1"
    params = {
        "key": os.getenv('LUNARCRUSH_API_KEY')  # Your LunarCrush API Key
    }
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        altrank = data.get('data', {}).get('altrank')
        if altrank:
            return f"The LunarCrush AltRank for {coin} is {altrank}."
        else:
            return "AltRank not found."
    except Exception as e:
        return f"Error fetching LunarCrush AltRank: {str(e)}"          
     