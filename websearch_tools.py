import os
import requests
from langchain.agents import tool
import logging
import urllib.parse
from cachetools import cached, TTLCache

# Assuming you've set your SEARCHAPI_API_KEY in the environment
api_key = os.getenv("SEARCHAPI_API_KEY")
logging.debug(f"Using API Key: {api_key}")

cache = TTLCache(maxsize=100, ttl=300)  # Cache up to 100 items, each for 5 minutes

@tool
@cached(cache)
def search_with_searchapi(query: str, engine="google", limit=3, **kwargs) -> str:
    """
    Performs a search using SearchApi and returns a concise summary of the top results, with improvements for dynamic engine selection, caching, and advanced error handling.
    """
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.searchapi.io/api/v1/search?engine={engine}&q={encoded_query}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "LenoxBot/1.0"
        }

        logging.debug(f"Request URL: {url}")
        logging.debug(f"Request headers: {headers}")

        response = requests.get(url, headers=headers, params={**kwargs, 'num': limit})
        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response body: {response.text}")

        response.raise_for_status()
        results = response.json()

        summary = [f"{i}. {result.get('title', 'No title available')} - {result.get('snippet', 'No snippet available')}"
                   for i, result in enumerate(results.get('results', [])[:limit], 1)]

        return "\n".join(summary)
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return f"Failed to fetch search results: {e}"
