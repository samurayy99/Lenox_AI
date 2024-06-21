import os
import requests
import json
from langchain.agents import tool  # Use the @tool decorator for Langchain compatibility

class APIError(Exception):
    """Custom API Error to handle exceptions from CryptoCompare requests."""
    def __init__(self, status_code, detail):
        super().__init__(f"API Error {status_code}: {detail}")

@tool
def get_current_price(symbol: str, currencies: str = 'USD') -> str:
    """Fetches the current price of a specified cryptocurrency in one or more currencies."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={currencies}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return f"Current prices for {symbol}: {response.json()}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_latest_social_stats(coin_symbol: str) -> str:
    """Retrieves the latest social statistics for a given cryptocurrency symbol."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/social/coin/latest?fsym={coin_symbol}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        coin_url = f"https://www.cryptocompare.com/coins/{coin_symbol}/overview"
        return f"Latest social stats for {coin_symbol}: {data}. More details at: {coin_url}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_historical_social_stats(coin_symbol: str, days: int = 30) -> str:
    """Fetches historical social data for a given cryptocurrency over a specified number of days."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/social/coin/histo/day?fsym={coin_symbol}&limit={days}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        coin_url = f"https://www.cryptocompare.com/coins/{coin_symbol}/overview"
        return f"Historical social stats for {coin_symbol} over the last {days} days: {data}. More details at: {coin_url}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))


@tool
def list_news_feeds_and_categories() -> str:
    """Lists all news feeds and categories available from CryptoCompare."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = "https://min-api.cryptocompare.com/data/news/feedsandcategories"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return f"News feeds and categories: {response.json()}. More details at: <a href='{url}'>CryptoCompare News</a>"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))
    
    

@tool
def get_latest_trading_signals(coin_symbol: str) -> str:
    """Fetches the latest trading signals for a specified cryptocurrency symbol."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/tradingsignals/intotheblock/latest?fsym={coin_symbol}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        coin_url = f"https://www.cryptocompare.com/coins/{coin_symbol}/overview"
        return f"Latest trading signals for {coin_symbol}: {data}. More details at: {coin_url}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_top_exchanges_by_volume(fsym: str, tsym: str, limit: int = 10) -> str:
    """Fetches top exchanges by volume for a specific trading pair."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/top/exchanges?fsym={fsym}&tsym={tsym}&limit={limit}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return f"Top exchanges by volume for {fsym}/{tsym}: {response.json()}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_historical_daily(symbol: str, currency: str = 'USD', limit: int = 30) -> str:
    """Retrieves the daily historical data for a specific cryptocurrency in a given currency."""
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym={currency}&limit={limit}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'Data' not in data or 'Data' not in data['Data']:
            raise KeyError("Missing 'Data' key in the response.")
        historical_data = data['Data']['Data']
        coin_url = f"https://www.cryptocompare.com/coins/{symbol}/overview"
        return f"Historical daily data for {symbol} to {currency}: {historical_data}. More details at: {coin_url}"
    except KeyError as e:
        return f"Error: {str(e)}. Unable to retrieve historical daily data for {symbol}."
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_top_volume_symbols(currency: str = 'USD', limit: int = 10, page: int = 0) -> str:
    """
    Fetches the top cryptocurrencies by 24-hour trading volume in a specific currency.
    Args:
        currency (str): The currency symbol to consider for volume (e.g., 'USD').
        limit (int): Number of top symbols to retrieve.
        page (int): The pagination for the request.
    Returns:
        str: List of top cryptocurrencies by volume.
    """
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    url = f"https://min-api.cryptocompare.com/data/top/totalvolfull?tsym={currency}&limit={limit}&page={page}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Debug logging of the full response
        print(json.dumps(data, indent=4))

        if 'Data' not in data:
            raise KeyError("Missing 'Data' in the response")

        symbols = {item['CoinInfo']['Name']: item['RAW'][currency]['VOLUME24HOURTO'] for item in data['Data'] if 'RAW' in item and currency in item['RAW']}
        return f"Top {limit} symbols by 24-hour volume in {currency}: {symbols}"
    except KeyError as e:
        print(f"Error: Missing expected data in the response: {str(e)}")
        return f"Error: Missing expected data in the response: {str(e)}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))


