import os
import requests
from langchain.agents import tool  # Use the @tool decorator for Langchain compatibility

class APIError(Exception):
    """Custom API Error to handle exceptions from CryptoCompare requests."""
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")

@tool
def get_current_price(symbol: str, currencies: str = 'USD') -> str:
    """
    Fetches the current price of a specified cryptocurrency in one or more currencies.
    Args:
        symbol (str): The symbol of the cryptocurrency (e.g., 'BTC', 'ETH').
        currencies (str): Comma-separated string of currency symbols (e.g., 'USD,JPY,EUR').
    Returns:
        str: Current price data in the specified currencies.
    """
    api_url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms={currencies}"
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return f"Current prices for {symbol}: {data}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

@tool
def get_historical_daily(symbol: str, currency: str = 'USD', limit: int = 30) -> str:
    """
    Retrieves the daily historical data for a specific cryptocurrency in a given currency.
    Args:
        symbol (str): The symbol of the cryptocurrency (e.g., 'BTC', 'ETH').
        currency (str): The currency symbol to convert into (e.g., 'USD').
        limit (int): Number of days to retrieve data for.
    Returns:
        str: Daily historical price data.
    """
    api_url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym={currency}&limit={limit}"
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Check for the presence of the 'Data' key
        if 'Data' not in data or 'Data' not in data['Data']:
            raise KeyError("Missing 'Data' key in the response.")

        historical_data = data['Data']['Data']
        return f"Historical daily data for {symbol} to {currency}: {historical_data}"
    except KeyError as e:
        return f"Error: {str(e)}. Unable to retrieve historical daily data for {symbol}."
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))


@tool
def get_top_volume_symbols(currency: str = 'USD', limit: int = 10) -> str:
    """
    Fetches the top cryptocurrencies by 24-hour trading volume in a specific currency.
    Args:
        currency (str): The currency symbol to consider for volume (e.g., 'USD').
        limit (int): Number of top symbols to retrieve.
    Returns:
        str: List of top cryptocurrencies by volume.
    """
    api_url = f"https://min-api.cryptocompare.com/data/top/totalvolfull?limit={limit}&tsym={currency}"
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    headers = {'authorization': f'Apikey {api_key}'} if api_key else {}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()['Data']
        symbols = {item['CoinInfo']['Name']: item['DISPLAY'][currency]['VOLUME24HOURTO'] for item in data}
        return f"Top {limit} symbols by 24-hour volume in {currency}: {symbols}"
    except requests.RequestException as e:
        raise APIError(response.status_code, str(e))

# You can add further functions here following the same pattern.
