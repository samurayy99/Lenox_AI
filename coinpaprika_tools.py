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
        detail_link = f"https://coinpaprika.com/coin/{coin_id}"
        return f"Coin Details:\n{detail_str}\nMore details: {detail_link}"
    except APIError as e:
        return f"Error fetching coin details: {e}"

@tool
@cached(cache)
def get_coin_tags():
    """Fetches and returns a list of all cryptocurrency tags with their description."""
    api_url = "https://api.coinpaprika.com/v1/tags"
    try:
        data = safe_request(api_url)
        tags = "\n".join([f"{tag['name']}: {tag['description']}" for tag in data])
        tags_link = "https://coinpaprika.com/tags/"
        return f"Available Tags:\n{tags}\nExplore more tags: {tags_link}"
    except APIError as e:
        return f"Error fetching tags: {e}"
    
@tool
@cached(cache)
def get_market_overview():
    """Fetches and returns the global cryptocurrency market overview."""
    api_url = "https://api.coinpaprika.com/v1/global"
    try:
        data = safe_request(api_url)
        market_overview = {
            "Total Market Cap (USD)": data["market_cap_usd"],
            "24h Volume (USD)": data["volume_24h_usd"],
            "Bitcoin Dominance (%)": data["bitcoin_dominance_percentage"],
            "Number of Cryptocurrencies": data["cryptocurrencies_number"],
            "Market Cap ATH": data["market_cap_ath_value"],
            "Volume 24h ATH": data["volume_24h_ath_value"],
        }
        overview_str = "\n".join([f"{k}: {v}" for k, v in market_overview.items()])
        overview_link = "https://coinpaprika.com/"
        return f"Market Overview:\n{overview_str}\nCheck the full market overview: {overview_link}"
    except APIError as e:
        return f"Error fetching market overview: {e}"

@tool
@cached(cache)
def get_ticker_info(coin_id: str):
    """Fetches and returns ticker information for a specific coin."""
    api_url = f"https://api.coinpaprika.com/v1/tickers/{coin_id}"
    try:
        data = safe_request(api_url)
        ticker_info = {
            "Name": data["name"],
            "Symbol": data["symbol"],
            "Price (USD)": data.get("quotes", {}).get("USD", {}).get("price"),
            "24h Volume (USD)": data.get("quotes", {}).get("USD", {}).get("volume_24h"),
            "Market Cap (USD)": data.get("quotes", {}).get("USD", {}).get("market_cap"),
            "Percent Change 24h": data.get("quotes", {}).get("USD", {}).get("percent_change_24h"),
        }
        ticker_str = "\n".join([f"{k}: {v}" for k, v in ticker_info.items()])
        ticker_link = f"https://coinpaprika.com/coin/{coin_id}/"
        return f"Ticker Information:\n{ticker_str}\nView on CoinPaprika: {ticker_link}"
    except APIError as e:
        return f"Error fetching ticker info: {e}"
