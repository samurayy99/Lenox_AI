import requests
from pydantic import BaseModel, Field
from langchain.agents import tool  # Use the @tool decorator
import os
import pandas as pd

# Define models for input validation
class AssetDataInput(BaseModel):
    asset_id: str = Field(..., description="The unique identifier for the cryptocurrency asset (e.g., bitcoin)")

# Utility function to parse response to DataFrame
def parse_response_to_df(data, index_field):
    if 'data' in data:
        df = pd.json_normalize(data['data'])
        if not df.empty:
            df.set_index(index_field, inplace=True)
        return df
    return pd.DataFrame()

@tool
def get_asset_data(asset_id: str) -> str:
    """
    Fetches detailed asset data for a specific cryptocurrency asset from Messari.
    Includes price and volume information for the last 24 hours.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/assets/{validated_input.asset_id}/metrics"
    headers = {"x-messari-api-key": os.getenv('MESSARI_API_KEY')}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        if data.get('data'):
            market_data = data['data']['market_data']
            price_usd = market_data['price_usd']
            volume_last_24_hours = market_data['volume_last_24_hours']
            return f"The current price of {validated_input.asset_id} is ${price_usd}. Volume in the last 24 hours is ${volume_last_24_hours}."
        else:
            return "Asset data not found."
    except Exception as e:
        return f"Error fetching asset data from Messari: {str(e)}"

@tool
def get_news_feed(asset_id: str) -> str:
    """
    Fetches the latest news articles related to a specific cryptocurrency asset from Messari.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/news/{validated_input.asset_id}"
    headers = {"x-messari-api-key": os.getenv('MESSARI_API_KEY')}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        if data.get('data'):
            articles = data['data']
            articles_str = "\n\n".join([f"Title: {article['title']}\nURL: {article['url']}" for article in articles])
            return f"Latest news for {validated_input.asset_id}:\n{articles_str}"
        else:
            return "No news articles found."
    except Exception as e:
        return f"Error fetching news articles from Messari: {str(e)}"

@tool
def get_research_reports(asset_id: str) -> str:
    """
    Fetches the latest research reports for a specific cryptocurrency asset from Messari.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/research/{validated_input.asset_id}"
    headers = {"x-messari-api-key": os.getenv('MESSARI_API_KEY')}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        if data.get('data'):
            reports = data['data']
            reports_str = "\n\n".join([f"Title: {report['title']}\nURL: {report['url']}" for report in reports])
            return f"Latest research reports for {validated_input.asset_id}:\n{reports_str}"
        else:
            return "No research reports found."
    except Exception as e:
        return f"Error fetching research reports from Messari: {str(e)}"

@tool
def get_asset_profile(asset_id: str) -> str:
    """
    Fetches the asset profile for a specific cryptocurrency asset from Messari.

    Parameters:
    asset_id (str): The unique identifier for the cryptocurrency asset (e.g., bitcoin).

    Returns:
    str: A string containing the asset profile or an error message.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/assets/{validated_input.asset_id}/profile"
    headers = {"x-messari-api-key": os.getenv('MESSARI_API_KEY')}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        if data.get('data'):
            profile = data['data']['profile']
            general_info = profile['general']['overview']['project_details']
            return f"Profile for {validated_input.asset_id}: {general_info}"
        else:
            return "Asset profile not found."
    except Exception as e:
        return f"Error fetching asset profile from Messari: {str(e)}"
    


@tool
def get_historical_data(asset_id: str, interval: str = '1d') -> str:
    """
    Fetches historical data for a specific cryptocurrency asset from Messari.
    The interval parameter can be adjusted to fetch data over different time frames.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/assets/{validated_input.asset_id}/metrics/price/time-series?interval={interval}"
    headers = {"x-messari-api-key": os.getenv('MESSARI_API_KEY')}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        df = parse_response_to_df(data, 'timestamp')
        if not df.empty:
            return df.to_csv(index=False)
        else:
            return "No historical data found."
    except Exception as e:
        return f"Error fetching historical data from Messari: {str(e)}"


@tool
def get_market_data_over_time(asset_id: str, interval: str = '1d') -> str:
    """
    Fetches market data over time for a specific cryptocurrency asset from Messari.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/assets/{validated_input.asset_id}/metrics/market-data/time-series?interval={interval}"
    headers = {"x-messari-api-key": os.getenv('MESSARI_API_KEY')}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        df = parse_response_to_df(data, 'timestamp')
        if not df.empty:
            return df.to_csv(index=False)
        else:
            return "No market data found over time."
    except Exception as e:
        return f"Error fetching market data over time from Messari: {str(e)}"

@tool
def get_on_chain_stats(asset_id: str, interval: str = '1d') -> str:
    """
    Fetches on-chain statistics for a specific cryptocurrency asset from Messari.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/assets/{validated_input.asset_id}/metrics/on-chain-data/time-series?interval={interval}"
    headers = {"x-messari-api-key": os.getenv('MESSARI_API_KEY')}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        df = parse_response_to_df(data, 'timestamp')
        if not df.empty:
            return df.to_csv(index=False)
        else:
            return "No on-chain statistics found."
    except Exception as e:
        return f"Error fetching on-chain statistics from Messari: {str(e)}"

@tool
def get_latest_news(asset_id: str) -> str:
    """
    Fetches the latest news related to a specific cryptocurrency asset from Messari.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/news/{validated_input.asset_id}"
    headers = {"x-messari-api-key": os.getenv('MESSARI_API_KEY')}
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        if 'data' in data:
            news_items = data['data']
            news_str = "\n".join([f"{item['title']}: {item['url']}" for item in news_items])
            return f"Latest news for {validated_input.asset_id}:\n{news_str}"
        else:
            return "No latest news found."
    except Exception as e:
        return f"Error fetching the latest news from Messari: {str(e)}"  
    
    
@tool
def display_tokenomics(symbol: str):
    """
    Fetches and displays tokenomics information.
    """
    tokenomics_api = f"https://api.messari.io/v1/assets/{symbol}/metrics"
    response = requests.get(tokenomics_api)
    tokenomics_data = response.json()
    return {
        "Circulating Supply": tokenomics_data['data']['market_data']['circulating_supply'],
        "Total Supply": tokenomics_data['data']['market_data']['total_supply'],
        "Max Supply": tokenomics_data['data']['market_data']['max_supply']
    }          