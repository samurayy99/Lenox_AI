import requests
import logging

class APIIntegration:
    def __init__(self, api_key):
        self.api_key = api_key

    def call_tavily_search(self, query: str) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.post('https://api.tavily.com/search', headers=headers, json={"query": query})
            response.raise_for_status()
            logging.debug(f"Tavily response: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as err:
            logging.error(f"An error occurred: {err}")
            return {}