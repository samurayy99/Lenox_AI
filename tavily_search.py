import requests
import logging

def perform_tavily_search(api_key: str, query: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.post('https://api.tavily.com/search', headers=headers, json={"query": query})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"Tavily API HTTP error: {http_err}")
        return {"error": f"Tavily API HTTP error: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Tavily API request error: {req_err}")
        return {"error": "Tavily API request error"}

def format_tavily_results(search_results: dict) -> str:
    if 'error' in search_results:
        return search_results['error']
    results = search_results.get('results', [])
    if not results:
        return "No results found."
    
    formatted_results = []
    for result in results:
        title = result.get('title', 'No title')
        snippet = result.get('snippet', 'No snippet')
        url = result.get('url', 'No URL')
        formatted_results.append(f"Title: {title}\nSnippet: {snippet}\nURL: {url}")
    
    return "\n\n".join(formatted_results)
