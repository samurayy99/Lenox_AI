# tavily_api_client.py

import aiohttp
import asyncio
from tavily_config import TAVILY_SEARCH_ENDPOINT, TAVILY_API_KEY, TIMEOUT, RETRY_ATTEMPTS

class TavilyAPIClient:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def fetch(self, query, retries=RETRY_ATTEMPTS):
        headers = {
            "Authorization": f"Bearer {TAVILY_API_KEY}",
            "Content-Type": "application/json"
        }
        params = {"query": query}
        for _ in range(retries):  # Changed from 'attempt' to '_'
            try:
                async with self.session.get(TAVILY_SEARCH_ENDPOINT, headers=headers, params=params, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Request failed with status {response.status}, retrying...")
            except aiohttp.ClientError as e:
                print(f"Client error: {e}, retrying...")
            await asyncio.sleep(1)  # Exponential backoff could be considered here
        raise Exception(f"Failed to fetch data from Tavily API after {retries} attempts")

    async def close(self):
        await self.session.close()