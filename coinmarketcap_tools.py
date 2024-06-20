import os
from requests import Session, ConnectionError, Timeout, TooManyRedirects
from langchain.tools import tool

# Load API key from environment variable
API_KEY = os.getenv('CMC_PRO_API_KEY')
if not API_KEY:
    raise ValueError("Please set the 'CMC_PRO_API_KEY' environment variable.")

class CoinMarketCapAPI:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = 'https://pro-api.coinmarketcap.com/v1'
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }
        self.session = Session()
        self.session.headers.update(self.headers)

    def make_request(self, endpoint, parameters):
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=parameters)
            data = response.json()
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(f"Error fetching data from CoinMarketCap: {e}")
            return None

cmc_api = CoinMarketCapAPI()

@tool
def get_latest_listings(start=1, limit=10, convert='USD'):
    """
    Get the latest cryptocurrency listings.
    Args:
    - start (int): Starting point of the listings.
    - limit (int): Number of listings to retrieve.
    - convert (str): The fiat or cryptocurrency to convert the listings to.
    """
    endpoint = 'cryptocurrency/listings/latest'
    parameters = {
        'start': start,
        'limit': limit,
        'convert': convert
    }
    return cmc_api.make_request(endpoint, parameters)

@tool
def get_crypto_metadata(crypto_id):
    """
    Get metadata for a specific cryptocurrency.
    Args:
    - crypto_id (int): The CoinMarketCap ID of the cryptocurrency.
    """
    endpoint = f'cryptocurrency/info'
    parameters = {'id': crypto_id}
    return cmc_api.make_request(endpoint, parameters)


@tool
def get_global_metrics(convert='USD'):
    """
    Get the latest global cryptocurrency market metrics.
    Args:
    - convert (str): The fiat or cryptocurrency to convert the metrics to.
    """
    endpoint = 'global-metrics/quotes/latest'
    parameters = {'convert': convert}
    return cmc_api.make_request(endpoint, parameters)
