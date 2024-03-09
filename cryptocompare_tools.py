import requests
import os
from pydantic import BaseModel, Field
import datetime
from langchain.agents import tool  # Use the @tool decorator

# Define models for input validation
class CryptoDataInput(BaseModel):
    symbol: str = Field(..., description="The symbol of the cryptocurrency (e.g., BTC, ETH)")

@tool
def get_crypto_data(symbol: str) -> str:
    """
    Returns the current price of the specified cryptocurrency symbol using CryptoCompare API.
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
    Fetches and returns historical price data for a specified cryptocurrency using CryptoCompare API.

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