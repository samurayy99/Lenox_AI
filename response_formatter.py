import logging

def format_tavily_results(results):
    """Format the Tavily search results."""
    formatted_results = ""
    for result in results:
        try:
            formatted_results += f"URL: {result['url']}\nContent: {result['content']}\n\n"
        except KeyError as e:
            logging.error(f"Error formatting Tavily result: {e}")
            formatted_results += "Error formatting result\n\n"
    return formatted_results

class ResponseFormatter:
    def format_response(self, response):
        if not response:
            return {"results": [], "count": 0}
        info = self.extract_relevant_info(response)
        return self.structure_output(info)

    def extract_relevant_info(self, response):
        # Placeholder for actual data extraction logic
        return response.get("data", [])

    def structure_output(self, info):
        return {
            "results": info,
            "count": len(info)
        }