import os
from langchain.agents import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.documents import Document

# Import the necessary tools from langchain
from langchain.tools import DuckDuckGoSearchResults

@tool
def search_duckduckgo(query: str) -> str:
    """
    Performs a search using DuckDuckGo and returns the result.

    Args:
        query (str): The search query string.

    Returns:
        str: A string containing the search result.
    """
    search = DuckDuckGoSearchRun()
    result = search.run(query)
    return result

@tool
def detailed_duckduckgo_search(query: str, max_results: int = 5) -> str:
    """
    Performs a detailed search using DuckDuckGo and returns the top results along with additional information.

    Args:
        query (str): The search query string.
        max_results (int): Maximum number of detailed search results to return.

    Returns:
        str: A formatted string containing detailed information (title, snippet, link) of the top search results.
    """
    search = DuckDuckGoSearchResults()
    results = search.run(query)
    if len(results) > max_results:
        results = results[:max_results]  # Limit the number of results to max_results
    detailed_results = [f"Title: {result['title']}\nSnippet: {result['snippet']}\nLink: {result['link']}" for result in results]
    return "\n\n".join(detailed_results)



@tool
def duckduckgo_news_search(query: str, max_results: int = 5) -> str:
    """
    Performs a news search using DuckDuckGo and returns the top news articles related to the query.

    Args:
        query (str): The search query string.
        max_results (int): Maximum number of news search results to return.

    Returns:
        str: A formatted string containing titles and URLs of the top news search results.
    """
    api_wrapper = DuckDuckGoSearchAPIWrapper()
    results = api_wrapper.results(query, max_results)  # Removed the backend='news' parameter

    if not results:
        return "No results found."

    news_results = []
    for result in results:
        title = result.get('title', 'No title available')
        link = result.get('link', 'No link available')
        news_results.append(f"Title: {title}\nLink: {link}")

    return "\n\n".join(news_results[:max_results])


