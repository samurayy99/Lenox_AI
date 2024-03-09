import requests
import os
from pydantic import BaseModel, Field
from langchain.agents import tool  # Use the @tool decorator

# Define models for input validation
class CryptoDataInput(BaseModel):
    symbol: str = Field(..., description="The symbol of the cryptocurrency (e.g., BTC, ETH)")

@tool
def get_lunarcrush_galaxy_score(coin: str) -> str:
    """
    Fetches the current Galaxy Score for a given cryptocurrency from LunarCrush.
    """
    api_url = f"https://lunarcrush.com/api4/public/coins/{coin}/v1"
    params = {
        "key": os.getenv('LUNARCRUSH_API_KEY')  # Your LunarCrush API Key
    }
    try:
        response = requests.get(api_url, params=params)
        data = response.json()
        galaxy_score = data.get('data', {}).get('galaxy_score')
        if galaxy_score:
            return f"The LunarCrush Galaxy Score for {coin} is {galaxy_score}."
        else:
            return "Galaxy Score not found."
    except Exception as e:
        return f"Error fetching LunarCrush Galaxy Score: {str(e)}"

@tool
def analyze_crypto_sentiment(coin: str) -> str:
    """
    Analyzes the market sentiment and social influence for a specific cryptocurrency using LunarCrush API.
    """
    lunarcrush_api_key = os.getenv('LUNARCRUSH_API_KEY')
    url = f"https://api.lunarcrush.com/v2?data=assets&key={lunarcrush_api_key}&symbol={coin}&data_points=1&interval=day"

    try:
        response = requests.get(url)
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            asset_data = data['data'][0]
            galaxy_score = asset_data.get('galaxy_score', 'N/A')
            alt_rank = asset_data.get('alt_rank', 'N/A')
            social_volume = asset_data.get('social_volume', 'N/A')
            return (f"Galaxy Score: {galaxy_score}, AltRank: {alt_rank}, "
                    f"Social Volume: {social_volume} for {coin}.")
        else:
            return "No sentiment data available for {coin}."
    except Exception as e:
        return f"Exception occurred while fetching sentiment data: {str(e)}"

@tool
def get_influential_crypto_assets() -> str:
    """
    Identifies and returns information on the most influential crypto assets based on social media data and market performance using LunarCrush API.
    """
    lunarcrush_api_key = os.getenv('LUNARCRUSH_API_KEY')
    api_url = f"https://api.lunarcrush.com/v2?data=market&key={lunarcrush_api_key}"
    try:
        response = requests.get(api_url)
        data = response.json()
        top_assets = sorted(data['data'], key=lambda x: (-x['galaxy_score'], -x['alt_rank'], x['market_cap']))[:10]
        result_str = "Top Influential Crypto Assets:\n"
        for asset in top_assets:
            result_str += f"{asset['name']} (Symbol: {asset['symbol']}), Galaxy Score: {asset['galaxy_score']}, AltRank: {asset['alt_rank']}, Market Cap: {asset['market_cap']}\n"
        return result_str
    except Exception as e:
        return f"Error fetching influential crypto assets: {str(e)}" 