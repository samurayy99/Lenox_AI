import requests
from langchain.tools import tool

class FearAndGreedIndexAPI:
    def __init__(self):
        self.base_url = 'https://api.alternative.me/fng/'

    def make_request(self, parameters):
        try:
            response = requests.get(self.base_url, params=parameters)
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Alternative.me: {e}")
            return None

fng_api = FearAndGreedIndexAPI()

@tool
def get_fear_and_greed_index(limit=1, format='json', date_format=''):
    """
    Get the latest data of the Fear and Greed Index.
    Args:
    - limit (int): Limit the number of returned results. Default is 1.
    - format (str): Format of the data ('json' or 'csv'). Default is 'json'.
    - date_format (str): Date format ('us', 'cn', 'kr', or 'world'). Default is '' (unixtime).
    """
    parameters = {
        'limit': limit,
        'format': format,
        'date_format': date_format
    }
    return fng_api.make_request(parameters)
