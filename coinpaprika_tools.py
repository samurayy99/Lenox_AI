import requests
from cachetools import TTLCache, cached
from langchain.agents import tool  # Use the @tool decorator

# Define a robust cache to manage API rate limits
cache = TTLCache(maxsize=100, ttl=600)

class APIError(Exception):
    """Exception class for API errors"""
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(f"API Error {status}: {message}")

def safe_request(url, params=None):
    """Safely perform HTTP requests and handle common errors."""
    headers = {"User-Agent": "coinpaprika/python"}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise APIError(404, "The requested resource was not found.")
        else:
            raise APIError(response.status_code, str(e))
    except requests.RequestException as e:
        raise APIError(500, f"An error occurred while handling your request: {str(e)}")

@tool
@cached(cache)
def get_coin_details(coin_id: str) -> str:
    """Fetches and returns details for a specified coin."""
    api_url = f"https://api.coinpaprika.com/v1/coins/{coin_id}"
    try:
        data = safe_request(api_url)
        details = {
            "Name": data["name"],
            "Symbol": data["symbol"],
            "Type": data["type"],
            "Active": str(data["is_active"]),
            "Rank": data["rank"],
            "Description": data["description"]
        }
        detail_str = "\n".join([f"{k}: {v}" for k, v in details.items()])
        return f"Coin Details:\n{detail_str}"
    except APIError as e:
        return f"Error fetching coin details: {e}"

@tool
@cached(cache)
def get_tags():
    """Fetches and returns a list of all cryptocurrency tags with their description."""
    api_url = "https://api.coinpaprika.com/v1/tags"
    try:
        data = safe_request(api_url)
        tags = "\n".join([f"{tag['name']}: {tag['description']}" for tag in data])
        return f"Available Tags:\n{tags}"
    except APIError as e:
        return f"Error fetching tags: {e}"

