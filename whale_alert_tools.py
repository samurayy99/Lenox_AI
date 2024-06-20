import os
from requests import Session, ConnectionError, Timeout, TooManyRedirects
from langchain.tools import tool

# Load API key from environment variable
API_KEY = os.getenv('WHALE_ALERT_API_KEY')
if not API_KEY:
    raise ValueError("Please set the 'WHALE_ALERT_API_KEY' environment variable.")

class WhaleAlertAPI:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = 'https://api.whale-alert.io/v1'
        self.headers = {
            'Accepts': 'application/json',
        }
        self.session = Session()
        self.session.headers.update(self.headers)

    def make_request(self, endpoint, parameters):
        try:
            parameters['api_key'] = self.api_key
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=parameters)
            data = response.json()
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(f"Error fetching data from Whale Alert: {e}")
            return None

whale_alert_api = WhaleAlertAPI()

@tool
def get_whale_alert_status():
    """
    Get the current status of Whale Alert.
    """
    endpoint = 'status'
    parameters = {}
    return whale_alert_api.make_request(endpoint, parameters)

@tool
def get_transaction_by_hash(blockchain, hash):
    """
    Get a transaction by its hash.
    Args:
    - blockchain (str): The blockchain to search for the specific hash (e.g., 'bitcoin', 'ethereum').
    - hash (str): The hash of the transaction to return.
    """
    endpoint = f'transaction/{blockchain}/{hash}'
    parameters = {}
    return whale_alert_api.make_request(endpoint, parameters)

@tool
def get_recent_transactions(start, min_value=10000, limit=100, currency=None):
    """
    Get recent transactions after a set start time.
    Args:
    - start (int): Unix timestamp for retrieving transactions from timestamp (exclusive).
    - min_value (int): Minimum USD value of transactions returned.
    - limit (int): Maximum number of results returned.
    - currency (str): Returns transactions for a specific currency code.
    """
    endpoint = 'transactions'
    parameters = {
        'start': start,
        'min_value': min_value,
        'limit': limit
    }
    if currency:
        parameters['currency'] = currency
    return whale_alert_api.make_request(endpoint, parameters)
