import logging
from langchain.agents import tool
from langchain_community.tools.tavily_search import TavilySearchResults

@tool
def tavily_search(query: str) -> str:
    """
    Performs a search using the Tavily search engine and returns the results.

    Args:
        query (str): The search query.

    Returns:
        str: A string representation of the search results.
    """
    try:
        tavily_tool = TavilySearchResults()
        results = tavily_tool.invoke({"query": query})
        logging.info(f"Tavily search results for '{query}': {results}")
        formatted_results = '\n'.join([f"{result['url']}: {result['content']}" for result in results])
        return formatted_results
    except Exception as e:
        logging.error(f"Error performing Tavily search: {e}")
        return "An error occurred during the Tavily search."
