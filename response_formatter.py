import re

def format_response(response: dict) -> str:
    if 'type' in response and response['type'] == 'search_results':
        return format_tavily_results(response['results'])
    return response.get('content', 'No content available.')

def format_tavily_results(search_results: list, max_results: int = 3, content_length: int = 200) -> str:
    if not search_results:
        return "No relevant search results found."
    limited_results = search_results[:max_results]
    formatted_results = [f"**[{res['url']}]**\n{extract_title(res['content'])}\n{res['content'][:content_length]}..." for res in limited_results]
    return "\n\n".join(formatted_results)

def extract_title(content: str) -> str:
    title_search = re.search(r'(.*?)(?: - |: )', content)
    return title_search.group(1) if title_search else content.split('\n')[0]
