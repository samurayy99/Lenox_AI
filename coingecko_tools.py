import requests
import numpy as np
from pydantic import BaseModel, Field
from langchain.agents import tool  # Use the @tool decorator

# Define models for input validation
class CryptoDataInput(BaseModel):
    symbol: str = Field(..., description="The symbol of the cryptocurrency (e.g., BTC, ETH)")

@tool
def get_coingecko_market_data(coin_id: str, vs_currency: str = "usd") -> str:
    """
    Fetches and returns market data for a specified cryptocurrency using CoinGecko API.
    """
    api_url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "ids": coin_id,
    }
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        if data and len(data) > 0:
            coin_data = data[0]  # Assuming the first item is the coin we're interested in
            price = coin_data['current_price']
            market_cap = coin_data['market_cap']
            volume_24h = coin_data['total_volume']
            return (f"Price: {price} {vs_currency}, Market Cap: {market_cap}, "
                    f"24h Volume: {volume_24h} for {coin_id}.")
        else:
            return "Failed to fetch data from CoinGecko or coin not found."
    except Exception as e:
        return f"Exception occurred: {str(e)}"

# Since we determined the liquidity score is not available, we will not include the get_liquidity_score function.

@tool
def get_macd(coin_id: str, vs_currency: str = "usd", days: int = 26) -> str:
    """
    Calculates the Moving Average Convergence Divergence (MACD) for a specified cryptocurrency.
    """
    historical_data_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days
    }
    
    try:
        response = requests.get(historical_data_url, params=params)
        data = response.json()
        prices = [price[1] for price in data['prices']]
        
        # Calculate MACD
        short_ema = np.mean(prices[-12:])  # 12-day EMA
        long_ema = np.mean(prices[-26:])  # 26-day EMA
        macd = short_ema - long_ema
        signal_line = np.mean(prices[-9:])  # 9-day EMA of MACD for signal line
        
        return f"MACD: {macd:.2f}, Signal Line: {signal_line:.2f} for {coin_id} in {vs_currency}."
    except Exception as e:
        return f"Error calculating MACD: {str(e)}"

@tool
def get_trending_coins():
    """
    Retrieves the list of trending coins from CoinGecko.
    """
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        response = requests.get(url)
        data = response.json()
        trending_coins = [coin['item']['name'] for coin in data['coins']]
        return f"Trending coins: {', '.join(trending_coins)}"
    except Exception as e:
        return f"Error fetching trending coins: {str(e)}"

@tool
def get_public_companies_holdings():
    """
    Retrieves the list of public companies and their cryptocurrency holdings.
    """
    url = "https://api.coingecko.com/api/v3/companies/public_treasury/bitcoin"
    try:
        response = requests.get(url)
        data = response.json()
        holdings = {company['name']: company['total_holdings'] for company in data['companies']}
        return f"Public companies holdings: {', '.join([f'{k}: {v}' for k, v in holdings.items()])}"
    except Exception as e:
        return f"Error fetching public companies holdings: {str(e)}"

# Additional functions for other endpoints can be implemented in a similar pattern.
