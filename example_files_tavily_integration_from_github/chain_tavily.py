import os
from typing import TypedDict, Annotated, Sequence
import operator
import json

from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.utils.function_calling import convert_to_openai_function
from langgraph.prebuilt import ToolExecutor, ToolInvocation

from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph, END

from src.common import get, PREFERENCES_PATH

from pydantic import BaseModel

import streamlit as st

from src.flows import LangChainConstruct


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]



class TavilyBotSettings(BaseModel):
    max_results: int = 3
    temperature: float = 0.7


# TODO which OpenAI model do I want to use for this chain?  I should hardcode this, right?

class TavilyBot(LangChainConstruct):
    name = "🔍 :blue[Tavily Web Search]"
    avatar_filename = "assistant.png" # should I place this into the base class and overload it here?  Is that possible?
    preamble = "OpenAI GPT-4 equipped with a Tavily internet search tool."

    def __init__(self):
        super().__init__()


    def setup(self):
        self._is_setup = True

        # load settings from file
        try:
            settings_filename = PREFERENCES_PATH / f"botsettings_{self.name}.json"
            with open(settings_filename, "r") as f:
                settings = json.loads(f.read())
                self.settings = TavilyBotSettings(**settings)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = TavilyBotSettings()

        self.graph = compile_runnable(self.settings)


    def display_settings(self):
        def update(key):
            new_value = st.session_state[key]
            self.settings.__dict__[key] = new_value

            # save to file
            settings_filename = PREFERENCES_PATH / f"botsettings_{self.name}.json"
            with open(settings_filename, "w") as f:
                f.write(json.dumps(self.settings.model_dump()))

            self.setup() # we have to re-init the graph with the new settings

        st.select_slider("Number of :green[Search Results]", options=[1, 2, 3, 4, 5], key="max_results", value=self.settings.max_results, on_change=update, args=("max_results",))
        st.slider("LLM :red[Temperature]", min_value=0.0, max_value=1.0, key="temperature", value=self.settings.temperature, on_change=update, args=("temperature",))

        # TODO if temperature is very high, we could display a warning here!

        # with st.expander(":blue[API KEYS]", expanded=False):
            # st.text_input(":blue[TAVILY_API_KEY]", key="TAVILY_API_KEY", value=self.settings.TAVILY_API_KEY, on_change=update, args=("TAVILY_API_KEY",))
            # st.text_input(":blue[OPENAI_API_KEY]", key="OPENAI_API_KEY", value=self.settings.OPENAI_API_KEY, on_change=update, args=("OPENAI_API_KEY",))


    def display_model_card(self):
        st.write(self.preamble)
        st.write("TODO...") #TODO
    

    def run(self, prompt, **kwargs):
        if not self._is_setup:
            raise Exception("TavilyBot.run(): not setup yet! Run `setup()` first!")

        inputs = {"messages": [HumanMessage(content=prompt)]}
        for output in self.graph.stream(inputs):
            # stream() yields dictionaries with output keyed by node name
            for key, value in output.items():
                yield key, value



    # def invoke(self, prompt, **kwargs):
        # return self.run(prompt, **kwargs)



def compile_runnable(settings: TavilyBotSettings):
    # check the settings to ensure that all needed API keys are set
    # if not settings.TAVILY_API_KEY:
    #     st.error("TAVILY_API_KEY is not set!")
    #     return None
    #     # raise ValueError("TAVILY_API_KEY is not set!")
    # if not settings.OPENAI_API_KEY:
    #     st.error("OPENAI_API_KEY is not set!")
    #     return None
        # raise ValueError("OPENAI_API_KEY is not set!")

    tavily_api_key = os.getenv("TAVILY_API_KEY", None)
    openai_api_key = os.getenv("OPENAI_API_KEY", None)

    if not tavily_api_key or not openai_api_key:
        st.error("API keys are not set!")
        return None

    # tavily_basetool = TavilySearchAPIWrapper(tavily_api_key=settings.TAVILY_API_KEY)
    tavily_basetool = TavilySearchAPIWrapper(tavily_api_key=tavily_api_key)

    tools = [TavilySearchResults(max_results=settings.max_results, api_wrapper=tavily_basetool)]
    tool_executor = ToolExecutor(tools)

    model = ChatOpenAI(temperature=settings.temperature, streaming=True, api_key=openai_api_key)

    # TODO use this instead langchain_core.utils.function_calling.convert_to_openai_function
    functions = [format_tool_to_openai_function(t) for t in tools]
    model = model.bind_functions(functions)


    def should_continue(state):
        messages = state["messages"]
        last_message = messages[-1]
        if "function_call" not in last_message.additional_kwargs:
            return "end"
        else:
            return "continue"

    def call_model(state):
        messages = state["messages"]
        response = model.invoke(messages)
        return {"messages": [response]}

    def call_tool(state):
        messages = state["messages"]
        last_message = messages[-1]
        action = ToolInvocation(
            tool=last_message.additional_kwargs["function_call"]["name"],
            tool_input=json.loads(
                last_message.additional_kwargs["function_call"]["arguments"]
            ),
        )
        response = tool_executor.invoke(action)
        function_message = FunctionMessage(content=str(response), name=action.tool)
        return {"messages": [function_message]}


    # TODO - if there's no API key.. the tool fails and I need the AI to understand this and stop the flow
    # TODO... alternatively... we could prevent the user from even starting the flow if the API key is missing
    ## Function returned: HTTPError('400 Client Error: Bad Request for url: https://api.tavily.com/search')


    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("action", call_tool)

    workflow.set_entry_point("agent")

    cond_edges = {
            "continue": "action",
            "end": END,
        }
    workflow.add_conditional_edges( "agent", should_continue, cond_edges)
    workflow.add_edge("action", "agent")
    app = workflow.compile()
    return app
