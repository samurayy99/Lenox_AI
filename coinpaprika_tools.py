import requests
from cachetools import cached, TTLCache
from langchain.agents import tool  # Use the @tool decorator
import pandas as pd

# Define a simple cache to store responses
cache = TTLCache(maxsize=100, ttl=300)

@tool
@cached(cache)
def get_global_market_overview() -> str:
    """
    Fetches and returns an overview of the global cryptocurrency market.
    """
    api_url = "https://api.coinpaprika.com/v1/global"
    try:
        response = requests.get(api_url)
        data = response.json()
        market_cap_usd = data['market_cap_usd']
        volume_24h_usd = data['volume_24h_usd']
        bitcoin_dominance_percentage = data['bitcoin_dominance_percentage']
        return f"Global Market Cap: ${market_cap_usd}, 24h Volume: ${volume_24h_usd}, Bitcoin Dominance: {bitcoin_dominance_percentage}%"
    except Exception as e:
        return f"Error fetching global market overview: {e}"

@tool
@cached(cache)
def get_coin_social_media_and_dev_activity(coin_id: str) -> str:
    """
    Fetches and returns social media and development activity for a specified coin.
    """
    api_url = f"https://api.coinpaprika.com/v1/coins/{coin_id}"
    try:
        response = requests.get(api_url)
        data = response.json()
        twitter_followers = data['twitter_followers']
        reddit_subscribers = data['reddit_subscribers']
        github_commits = sum([repo['commit_count_4_weeks'] for repo in data['development']['github']])
        return f"Twitter Followers: {twitter_followers}, Reddit Subscribers: {reddit_subscribers}, GitHub Commits (last 4 weeks): {github_commits}"
    except Exception as e:
        return f"Error fetching social media and development activity: {e}"

@tool
@cached(cache)
def get_exchange_info(exchange_id: str) -> pd.DataFrame:
    """
    Fetches and returns detailed information about an exchange and its markets.
    """
    api_url = f"https://api.coinpaprika.com/v1/exchanges/{exchange_id}/markets"
    try:
        response = requests.get(api_url)
        data = response.json()
        df = pd.DataFrame(data)
        return df[['pair', 'base_currency_name', 'quote_currency_name', 'market_url', 'category', 'reported_volume_24h_share']]
    except Exception as e:
        return pd.DataFrame({'error': str(e)})


@tool
@cached(cache)
def get_coin_details(coin_id: str) -> str:
    """
    Fetches and returns detailed information about a specified coin.
    """
    api_url = f"https://api.coinpaprika.com/v1/coins/{coin_id}"
    try:
        response = requests.get(api_url)
        data = response.json()
        details = {
            "Name": data["name"],
            "Symbol": data["symbol"],
            "Type": data["type"],
            "Rank": data["rank"],
            "Active": data["is_active"],
            "Description": data["description"],
            "Development Status": data["development_status"],
            "Hardware Wallet": data["hardware_wallet"],
            "Proof Type": data["proof_type"],
            "Org Structure": data["org_structure"],
            "Hash Algorithm": data["hash_algorithm"],
        }
        return details
    except Exception as e:
        return f"Error fetching coin details: {e}"

@tool
@cached(cache)
def get_coin_markets(coin_id: str) -> pd.DataFrame:
    """
    Fetches and returns market data for a specified coin.
    """
    api_url = f"https://api.coinpaprika.com/v1/coins/{coin_id}/markets"
    try:
        response = requests.get(api_url)
        data = response.json()
        df = pd.DataFrame(data)
        return df[['exchange_id', 'pair', 'base_currency_name', 'quote_currency_name', 'market_url', 'category', 'reported_volume_24h_share']]
    except Exception as e:
        return pd.DataFrame({'error': str(e)})

@tool
@cached(cache)
def get_coin_events(coin_id: str) -> pd.DataFrame:
    """
    Fetches and returns events related to a specified coin.
    """
    api_url = f"https://api.coinpaprika.com/v1/coins/{coin_id}/events"
    try:
        response = requests.get(api_url)
        data = response.json()
        df = pd.DataFrame(data)
        return df[['date', 'name', 'description', 'is_conference']]
    except Exception as e:
        return pd.DataFrame({'error': str(e)})