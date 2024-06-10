# tavily_search.py
import requests
import logging

def perform_tavily_search(query: str, api_key: str) -> dict:
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"query": query}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Tavily API HTTP error: {http_err}")
        return {"error": f"Tavily API HTTP error: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Tavily API request error: {req_err}")
        return {"error": "Tavily API request error"}
