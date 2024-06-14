# tavily_config.py

import os

# Base URL for Tavily Search API
TAVILY_BASE_URL = "https://api.tavily.com"

# Endpoint configurations
TAVILY_SEARCH_ENDPOINT = f"{TAVILY_BASE_URL}/search"

# API Key - Securely fetched from environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise EnvironmentError("TAVILY_API_KEY not found in environment variables.")

# Other configurations
TIMEOUT = 30  # Request timeout in seconds
RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests
