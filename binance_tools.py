import os
from requests import Session, ConnectionError, Timeout, TooManyRedirects
from langchain.tools import tool

# Load API key from environment variable
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
if not API_KEY or not API_SECRET:
    raise ValueError("Please set the 'BINANCE_API_KEY' and 'BINANCE_API_SECRET' environment variables.")

class BinanceAPI:
    def __init__(self):
        self.api_key = str(API_KEY)  # Ensure the API key is a string
        self.api_secret = str(API_SECRET)  # Ensure the API secret is a string
        self.base_url = 'https://api.binance.com'
        self.session = Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-MBX-APIKEY': self.api_key,
        })

    def make_request(self, endpoint, parameters=None):
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=parameters)
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response.json()
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(f"Error fetching data from Binance: {e}")
            return None

binance_api = BinanceAPI()

@tool
def get_binance_ticker(symbol='BTCUSDT'):
    """
    Get the current ticker price for a specific symbol.
    Args:
    - symbol (str): The trading pair symbol (e.g., 'BTCUSDT').
    """
    endpoint = 'api/v3/ticker/price'
    parameters = {'symbol': symbol}
    return binance_api.make_request(endpoint, parameters)

@tool
def get_binance_order_book(symbol='BTCUSDT', limit=10):
    """
    Get the order book for a specific symbol.
    Args:
    - symbol (str): The trading pair symbol (e.g., 'BTCUSDT').
    - limit (int): Limit the number of returned results.
    """
    endpoint = 'api/v3/depth'
    parameters = {'symbol': symbol, 'limit': limit}
    return binance_api.make_request(endpoint, parameters)

@tool
def get_binance_recent_trades(symbol='BTCUSDT', limit=10):
    """
    Get the recent trades for a specific symbol.
    Args:
    - symbol (str): The trading pair symbol (e.g., 'BTCUSDT').
    - limit (int): Limit the number of returned results.
    """
    endpoint = 'api/v3/trades'
    parameters = {'symbol': symbol, 'limit': limit}
    return binance_api.make_request(endpoint, parameters)
