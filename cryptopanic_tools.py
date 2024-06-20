import os
import requests
from dotenv import load_dotenv
from langchain.agents import tool

# Load environment variables from .env file
load_dotenv()

@tool
def get_latest_news() -> str:
    """
    Fetches the latest news from CryptoPanic.
    """
    api_key = os.getenv('CRYPTOPANIC_API_KEY')
    if not api_key:
        return "API key for CryptoPanic not found. Please set it in the environment variables."

    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={api_key}&public=true'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = response.json()
            news_titles = [f"{item['title']} - <a href='{item['url']}'>{item['url']}</a>" for item in news['results']]
            return '<br>'.join(news_titles)
        else:
            return f"Failed to fetch news: {response.status_code}"
    except Exception as e:
        return f"Error occurred while fetching news: {str(e)}"

@tool
def get_news_sources() -> str:
    """
    Fetches the sources of the latest news from CryptoPanic.
    """
    api_key = os.getenv('CRYPTOPANIC_API_KEY')
    if not api_key:
        return "API key for CryptoPanic not found. Please set it in the environment variables."

    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={api_key}&public=true'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = response.json()
            sources = set(item['domain'] for item in news['results'])
            formatted_sources = [f"{i+1}. {source}" for i, source in enumerate(sources)]
            return '<br>'.join(formatted_sources)
        else:
            return f"Failed to fetch news sources: {response.status_code}"
    except Exception as e:
        return f"Error occurred while fetching news sources: {str(e)}"

@tool
def get_last_news_title() -> str:
    """
    Fetches the title of the most recent news from CryptoPanic.
    """
    api_key = os.getenv('CRYPTOPANIC_API_KEY')
    if not api_key:
        return "API key for CryptoPanic not found. Please set it in the environment variables."

    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={api_key}&public=true'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = response.json()
            if news['results']:
                item = news['results'][0]
                return f"{item['title']} - <a href='{item['url']}'>{item['url']}</a>"
            else:
                return "No news available"
        else:
            return f"Failed to fetch the latest news title: {response.status_code}"
    except Exception as e:
        return f"Error occurred while fetching the latest news title: {str(e)}"
