import os
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults
from youtube_tools import search_youtube

class WebSearchManager:
    def __init__(self):
        serpapi_key = os.getenv('SERPAPI_API_KEY')
        if not serpapi_key:
            raise ValueError("SERPAPI_API_KEY not found in environment variables.")
        
        self.serpapi_search = SerpAPIWrapper(serpapi_api_key=serpapi_key)
        self.duckduckgo_search = DuckDuckGoSearchResults()

    def detect_intent(self, query: str) -> str:
        if any(keyword in query.lower() for keyword in ["search youtube", "youtube video", "youtube"]):
            return "youtube"
        if any(keyword in query.lower() for keyword in ["search", "find", "lookup"]):
            return "search"
        if any(keyword in query.lower() for keyword in ["weather", "forecast"]):
            return "weather"
        if any(keyword in query.lower() for keyword in ["result", "score", "match"]):
            return "sports"
        if any(keyword in query.lower() for keyword in ["visualize", "graph", "chart", "plot"]):
            return "visualization"
        return "unknown"

    def search_serpapi(self, query: str) -> str:
        try:
            results = self.serpapi_search.run(query)
            return f"SerpAPI results: {results}"
        except Exception as e:
            return f"Error using SerpAPI: {e}"

    def search_duckduckgo(self, query: str) -> str:
        try:
            results = self.duckduckgo_search.run(query)
            return f"DuckDuckGo results: {results}"
        except Exception as e:
            return f"Error using DuckDuckGo: {e}"

    def aggregate_search_results(self, query: str) -> str:
        serpapi_result = self.search_serpapi(query)
        duckduckgo_result = self.search_duckduckgo(query)
        return f"Aggregated results:\n\n{serpapi_result}\n\n{duckduckgo_result}"

    def handle_intent(self, intent: str, query: str) -> dict:
        if intent == "search":
            search_result = self.aggregate_search_results(query)
            return {"type": "text", "content": search_result}
        if intent == "youtube":
            search_result = search_youtube(query.replace("search youtube", "").strip())
            return {"type": "text", "content": search_result}
        if intent == "weather":
            weather_result = self.aggregate_search_results(query)  # Assuming similar handling for now
            return {"type": "text", "content": weather_result}
        if intent == "sports":
            sports_result = self.aggregate_search_results(query)  # Assuming similar handling for now
            return {"type": "text", "content": sports_result}
        if intent == "visualization":
            return {"type": "visualization", "content": "Visualization logic not implemented yet."}
        return {"type": "text", "content": "I don't understand your query."}