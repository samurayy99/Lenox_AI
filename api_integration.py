import requests
import logging

class APIIntegration:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def call_tavily_search(self, query: str) -> dict:
        try:
            return perform_tavily_search(query, self.api_key)
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Tavily API HTTP error: {http_err}")
            return {"error": f"Tavily API HTTP error: {http_err}"}
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Tavily API request error: {req_err}")
            return {"error": "Tavily API request error"}

def perform_tavily_search(query: str, api_key: str) -> dict:
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "api_key": api_key,
        "query": query
    }

    logging.debug(f"Sending request to Tavily API: {data}")

    response = requests.post(url, headers=headers, json=data)
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Tavily API HTTP error: {http_err}, Response: {response.text}")
        raise

    logging.debug(f"Received response from Tavily API: {response.json()}")
    return response.json()
