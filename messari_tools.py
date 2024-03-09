import requests
from pydantic import BaseModel, Field
from langchain.agents import tool  # Use the @tool decorator
import os

# Define models for input validation
class AssetDataInput(BaseModel):
    asset_id: str = Field(..., description="The unique identifier for the cryptocurrency asset (e.g., bitcoin)")

@tool
def get_asset_data(asset_id: str) -> str:
    """
    Fetches detailed asset data for a specific cryptocurrency asset from Messari.
    """
    validated_input = AssetDataInput(asset_id=asset_id)
    api_url = f"https://data.messari.io/api/v1/assets/{validated_input.asset_id}/metrics"
    headers = {
        "x-messari-api-key": os.getenv('MESSARI_API_KEY')
    }
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        if data.get('data'):
            market_data = data['data']['market_data']
            price_usd = market_data['price_usd']
            return f"The current price of {validated_input.asset_id} is ${price_usd}."
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
    headers = {
        "x-messari-api-key": os.getenv('MESSARI_API_KEY')
    }
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
    headers = {
        "x-messari-api-key": os.getenv('MESSARI_API_KEY')
    }
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