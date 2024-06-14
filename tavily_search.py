# tavily_search.py

import asyncio
from tavily_api_client import TavilyAPIClient

class TavilySearch:
    def __init__(self):
        self.client = TavilyAPIClient()

    async def search(self, query):
        try:
            response = await self.client.fetch(query)
            return self.process_response(response)
        except asyncio.TimeoutError:
            print("Request timed out")
        except Exception as e:
            print(f"Error during Tavily search: {e}")
        return None

    def process_response(self, response):
        # Assuming response is a JSON object that needs processing
        return response.get('results', [])

    async def close(self):
        await self.client.close()
