from typing import Optional, List, Dict, Type, Union
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableWithFallbacks

class TavilyInput(BaseModel):
    """Input for the Tavily tool."""
    query: str = Field(description="The search query to look up using the Tavily Search API.")
    max_results: int = Field(default=3, ge=2, le=6, description="The maximum number of search results to return. Must be between 2 and 6. Default value is 3")

class CustomTavilySearchResults(TavilySearchResults):
    include_answer = False
    include_raw_content = False
    include_image = False
    description: str = (
        "An advanced search engine that delivers comprehensive, accurate, and trustworthy results. "
        "It is particularly useful for answering questions about current events, news, and general knowledge. "
        "The input should be a well-formed search query, and the tool will return up to the specified maximum number of relevant results in JSON format. "
        "In addition to the search query, you can also specify the maximum number of results to retrieve, allowing for dynamic control over the amount of information returned."
    )
    max_results: int = 6
    args_schema: Type[BaseModel] = TavilyInput

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> Union[List[Dict], str]:
        """Use the tool."""
        try:
            return self.api_wrapper.results(
                query=query,
                max_results=self.max_results,
                include_answer=self.include_answer,
                include_raw_content=self.include_raw_content,
                include_images=self.include_image,
            )
        except Exception as e:
            print(f'TAVILY API occur error! {str(e)}')
            raise Exception(str(e))

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> Union[List[Dict], str]:
        """Use the tool asynchronously."""
        try:
            return await self.api_wrapper.results_async(
                query=query,
                max_results=self.max_results,
                include_answer=self.include_answer,
                include_raw_content=self.include_raw_content,
                include_images=self.include_image,
            )
        except Exception as e:
            print(f'TAVILY API occur error! {str(e)}')
            raise Exception(str(e))

class CustomTavilySearchAPIWrapper(TavilySearchAPIWrapper):
    pass

def get_tavily_search_tool(max_results: Optional[int] = None) -> RunnableWithFallbacks:
    if max_results is None:
        max_results = 5

    _tavily_search_tool = CustomTavilySearchResults(
        api_wrapper=CustomTavilySearchAPIWrapper(),
        include_answer=True,
        include_raw_content=True,
        max_results=max_results,
        include_image=True
    )
    _tavily_search_tool_with_fallbacks = _tavily_search_tool.with_fallbacks([_tavily_search_tool] * 60)
    print('@@@@ LOAD TAVILY TOOL SUCCESSFULLY @@@@')
    return _tavily_search_tool_with_fallbacks
