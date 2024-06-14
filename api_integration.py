# api_integration.py

from cache_manager import set_cache, get_cache, invalidate_cache

class APIIntegration:
    def __init__(self, api_key):
        self.api_key = api_key

    def perform_tavily_search(self, query):
        # Implement the search logic here
        pass

    def fetch_data(self, endpoint, params):
        cache_key = self.generate_cache_key(endpoint, params)
        cached_data = get_cache(cache_key)
        if cached_data:
            return cached_data

        response = self.make_request(endpoint, params)
        if response:
            set_cache(cache_key, response)
        return response

    def make_request(self, endpoint, params):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Example using requests
        import requests
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch data with status {response.status_code}")
        except requests.RequestException as e:
            print(f"Request failed: {e}")
        return {}

    def generate_cache_key(self, endpoint, params):
        key = f"{endpoint}:{str(params)}"
        return key

    def invalidate_cache(self, endpoint, params):
        cache_key = self.generate_cache_key(endpoint, params)
        invalidate_cache(cache_key)