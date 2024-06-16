from typing import Optional, Union, List, Dict, Type
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableWithFallbacks
from CustomHelper.Custom_Error_Handler import PAR_ERROR
import os

class TavilyInput(BaseModel):
    """Input for the Tavily tool."""
    query: str = Field(description="The search query to look up using the Tavily Search API.")
    max_results: int = Field(default=3, ge=2, le=6, description="The maximum number of search results to return. Must be between 2 and 6. Default value is 3")

class Custom_TavilySearchResults(TavilySearchResults):
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
            print(f'TAVILY API error occurred! {str(e)}')
            raise PAR_ERROR(str(e))

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
            print(f'TAVILY API error occurred! {str(e)}')
            raise PAR_ERROR(str(e))

class Custom_TavilySearchAPIWrapper(TavilySearchAPIWrapper):
    def results(
        self,
        query: str,
        max_results: Optional[int] = 5,
        search_depth: Optional[str] = "advanced",
        include_domains: Optional[List[str]] = [],
        exclude_domains: Optional[List[str]] = [],
        include_answer: Optional[bool] = False,
        include_raw_content: Optional[bool] = False,
        include_images: Optional[bool] = False,
    ) -> Dict:
        """Run query through Tavily Search and return metadata."""
        raw_search_results = self.raw_results(
            query,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
            include_images=include_images,
        )
        if include_answer:
            return self.clean_results(raw_search_results["results"], raw_search_results.get("answer"), raw_search_results.get("follow_up_questions"), raw_search_results.get("images"))
        else:
            return self.clean_results(raw_search_results["results"])

    async def results_async(
        self,
        query: str,
        max_results: Optional[int] = 5,
        search_depth: Optional[str] = "advanced",
        include_domains: Optional[List[str]] = [],
        exclude_domains: Optional[List[str]] = [],
        include_answer: Optional[bool] = False,
        include_raw_content: Optional[bool] = False,
        include_images: Optional[bool] = False,
    ) -> Dict:
        """Run query through Tavily Search and return metadata."""
        raw_search_results = await self.raw_results_async(
            query,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
            include_images=include_images,
        )
        if include_answer:
            return self.clean_results(raw_search_results["results"], raw_search_results.get("answer"), raw_search_results.get("follow_up_questions"), raw_search_results.get("images"))
        else:
            return self.clean_results(raw_search_results["results"])

    def clean_results(self, results: List[Dict], answer: Optional[str] = None, follow_up_questions: Optional[list] = None, images: Optional[list] = None) -> Dict:
        final_results = {}
        clean_results = []
        if answer is not None:
            final_results["answer"] = answer
        if follow_up_questions is not None:
            final_results["follow_up_questions"] = follow_up_questions
        if images is not None:
            final_results["images"] = images

        for result in results:
            clean_result = {
                "url": result["url"],
                "content": result["content"]
            }
            if "raw_content" in result:
                clean_result["raw_content"] = result["raw_content"]
            clean_results.append(clean_result)
        final_results["results"] = clean_results
        return final_results

class APIIntegration:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("API_KEY")

def get_tavily_search_tool(max_results: Optional[int] = None) -> RunnableWithFallbacks:
    if max_results is None:
        max_results = 5

    _tavily_search_tool = Custom_TavilySearchResults(
        api_wrapper=Custom_TavilySearchAPIWrapper(tavily_api_key=os.getenv("TAVILY_API_KEY")),
        include_answer=True,
        include_raw_content=True,
        max_results=max_results,
        include_image=True
    )
    _tavily_search_tool_with_fallbacks = _tavily_search_tool.with_fallbacks([_tavily_search_tool] * 60)
    print('@@@@ LOAD TAVILY TOOL SUCCESSFULLY @@@@')
    return _tavily_search_tool_with_fallbacks  # Ensure this line is correctly indented and always executed

# Ensure all return statements are within function or method bodies
