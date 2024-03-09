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

@tool
def get_liquidity_score(coin_id: str) -> str:
    """
    Fetches and returns the liquidity score of a specified cryptocurrency using CoinGecko API.
    
    Parameters:
    - coin_id (str): The CoinGecko ID of the cryptocurrency.
    
    Returns:
    str: A string containing the liquidity score.
    """
    coin_data_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    
    try:
        response = requests.get(coin_data_url)
        data = response.json()
        liquidity_score = data['liquidity_score']
        
        return f"The liquidity score of {coin_id} is {liquidity_score}."
    except Exception as e:
        return f"Error fetching liquidity score: {str(e)}"     

@tool
def get_macd(coin_id: str, vs_currency: str = "usd", days: int = 26) -> str:
    """
    Calculates the Moving Average Convergence Divergence (MACD) for a specified cryptocurrency.
    
    Parameters:
    - coin_id (str): The CoinGecko ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum').
    - vs_currency (str): The fiat currency to compare against (default: 'usd').
    - days (int): The number of days to calculate the MACD for (default: 26, which is common for MACD calculations).
    
    Returns:
    str: A string containing the MACD value.
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