import requests

class APIIntegration:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def call_tavily_search(self, query: str) -> dict:
        return perform_tavily_search(query, self.api_key)

def perform_tavily_search(query: str, api_key: str) -> dict:
       url = "https://api.tavily.com/search"
       headers = {
           "Content-Type": "application/json"
       }
       data = {
           "query": query,
           "api_key": api_key
       }
       response = requests.post(url, headers=headers, json=data)
       response.raise_for_status()
       return response.json()
