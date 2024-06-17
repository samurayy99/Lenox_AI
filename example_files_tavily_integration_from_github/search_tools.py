import logging
import os
from typing import Any, Dict, List, Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.pydantic_v1 import BaseModel, Field, root_validator
from langchain.tools import BaseTool

logger = logging.getLogger(__name__)


class SearchInput(BaseModel):
    query: str = Field(
        ..., description="The search query to use for the internet search"
    )


class Search(BaseTool):
    search_engine: Optional[str] = Field(
        default="Google",
        description="The search engine to use for the internet search.",
    )
    max_num_results: Optional[int] = Field(
        default=5, description="The maximum search result from search engine."
    )

    name = "Search"
    description = "Search the internet for a given query."
    args_schema: Type[BaseModel] = SearchInput
    return_direct = True
    verbose = True
    handle_tool_error = True

    @root_validator(allow_reuse=True)
    def validate_environment(cls, values: Dict) -> Dict:
        supported_search_engines = ["google", "ddg", "exa", "tavily"]
        search_engine = values["search_engine"]
        if search_engine.lower() not in supported_search_engines:
            raise NotImplementedError(
                f"Search engine '{search_engine}' is not implemented. "
                f"Valid options are: {supported_search_engines}"
            )

        return values

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> List[Dict[str, Any]]:
        """Use the tool."""
        if self.search_engine.lower() == "google":
            if (
                os.environ.get("GOOGLE_SEARCH_API_KEY") is None
                or os.environ.get("GOOGLE_CSE_ID") is None
            ):
                raise ValueError(
                    "Please set your `GOOGLE_SEARCH_API_KEY` "
                    "and `GOOGLE_CSE_ID` environment variables."
                )

            from langchain_community.utilities.google_search import (
                GoogleSearchAPIWrapper,
            )

            results = GoogleSearchAPIWrapper(
                google_api_key=os.getenv("GOOGLE_SEARCH_API_KEY"),
                google_cse_id=os.getenv("GOOGLE_CSE_ID"),
            ).results(query, num_results=self.max_num_results)
            return [
                {"content": r["snippet"], "url": r["link"], "title": r["title"]}
                for r in results
            ]

        if self.search_engine.lower() == "ddg":
            from langchain_community.utilities.duckduckgo_search import (
                DuckDuckGoSearchAPIWrapper,
            )

            results = DuckDuckGoSearchAPIWrapper(
                region="wt-wt", time="y", safesearch="off"
            ).results(query, max_results=self.max_num_results)
            return [
                {"content": r["snippet"], "url": r["link"], "title": r["title"]}
                for r in results
            ]

        if self.search_engine.lower() == "exa":
            if os.environ.get("EXA_API_KEY") is None:
                raise ValueError("Please set your `EXA_API_KEY` environment variables.")

            from exa_py import Exa

            exa = Exa(api_key=os.environ["EXA_API_KEY"])
            results = exa.search_and_contents(
                f"{query}",
                num_results=self.max_num_results,
                # use_autoprompt=True
            )
            return [
                {"content": r.text, "url": r.url, "title": r.title, "author": r.author}
                for r in results.results
            ]

        if self.search_engine.lower() == "tavily":
            if os.environ.get("TAVILY_API_KEY") is None:
                raise ValueError(
                    "Please set your `TAVILY_API_KEY` environment variables."
                )

            from langchain_community.utilities.tavily_search import (
                TavilySearchAPIWrapper,
            )

            response = TavilySearchAPIWrapper().raw_results(
                query,
                max_results=self.max_num_results,
            )
            results = []
            for result in response["results"]:
                results.append(
                    {
                        "content": result["content"],
                        "url": result["url"],
                        "title": result["title"],
                    }
                )
            return results

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> List[Dict[str, Any]]:
        """Use the tool asynchronously."""
        raise NotImplementedError("Search does not support async")
