import openai
import pandas as pd
import json
import plotly
import logging
from visualize_data import VisualizationConfig, create_visualization
from typing import Any, Dict, List, Union
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents.format_scratchpad import format_to_openai_functions
from lenox_memory import SQLChatMessageHistory
from documents import DocumentHandler
from prompts import PromptEngine
from tavily_tools import tavily_search
from nltk import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import requests
from textblob import TextBlob

class Lenox:
    def __init__(self, tools, document_handler: DocumentHandler, prompt_engine: PromptEngine = None):
        self.document_handler = document_handler
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine(tools=tools)
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.7).bind(functions=self.functions)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Hello, Volcano! 🌟 As your uniquely crafted digital companion, Lenox, I'm here to illuminate our path through the digital realm and beyond. 🚀 Tailored by your vision, I stand ready to navigate the crypto landscapes, offer bespoke insights, and provide steadfast support through life's twists and turns. Together, we'll transform challenges into opportunities and aspirations into achievements. 🌐 What journey shall we embark on today, creating our own legacy? 🤝"),
            ("user", "Hi Lenox! I'm excited to have you as my partner."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),      
        ])
        self.chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(x.get("intermediate_steps", []))
        ) | self.prompt | self.model | OpenAIFunctionsAgentOutputParser()
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=False)
        self.memory = SQLChatMessageHistory(session_id="my_session", connection_string="sqlite:///lenox.db")

    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        logging.debug(f"Received query: {query}")
        if not query:
            return {"type": "text", "content": "Please enter a query."}

        self.memory.session_id = session_id
        self.memory.add_message(HumanMessage(content=query, sender="user"))
        chat_history = self.memory.messages()

        if self.is_visualization_query(query):
            vis_type = self.parse_visualization_type(query)
            data = self.fetch_data_for_visualization(query)
            if not data:
                return {"type": "error", "content": "Data for visualization could not be fetched."}
            visualization_config = VisualizationConfig(data=data, visualization_type=vis_type)
            visualization_json = create_visualization(visualization_config)
            self.memory.add_message(AIMessage(content=visualization_json))
            return self.create_response(visualization_json, "visual")
        else:
            result = self.qa.invoke(
                {"input": query, "chat_history": chat_history},
                config={"configurable": {"session_id": session_id}}
            )
            self.memory.add_message(AIMessage(content=result.get('output', '')))
            return {"type": "text", "content": result.get('output', "Error processing the request.")}

    def handle_visualization_query(self, query, chat_history, session_id):
        data = self.fetch_data_for_visualization(query)
        visualization_type = self.parse_visualization_type(query)
        visualization_config = VisualizationConfig(data=data, visualization_type=visualization_type)
        visualization_content = create_visualization(visualization_config)
        self.memory.add_message(AIMessage(content=visualization_content, sender="system", session_id=session_id))
        return {"type": "visual", "content": visualization_content}

    def handle_general_query(self, query: str, chat_history: List[Dict[str, Any]], session_id: str) -> dict:
        context_messages = self.aggregate_context(chat_history)
        prompt_text = self.prompt_engine.generate_prompt(query, context_messages)
        result = self.qa.invoke(
            {"input": prompt_text.text, "chat_history": chat_history},
            config={"configurable": {"session_id": session_id}}
        )
        output = result.get('output', "Lass mich darüber nachdenken und ich komme darauf zurück.")
        self.memory.add_message(AIMessage(content=output, sender="system", session_id=session_id))
        return {"type": "text", "content": output}

    def aggregate_context(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        enriched_context = []
        for message in chat_history[-10:]:
            sentiment = TextBlob(message['content']).sentiment
            enriched_context.append({
                "content": message['content'],
                "sentiment": sentiment.polarity
            })
        return enriched_context

    def is_visualization_query(self, query: str) -> bool:
        visualization_keywords = ["visualize", "graph", "chart", "plot", "show me a graph of", "display data"]
        return any(keyword in query.lower() for keyword in visualization_keywords)

    def parse_visualization_type(self, query: str) -> str:
        visualization_keywords = {'line': ['line', 'linear'], 'bar': ['bar', 'column'], 'scatter': ['scatter', 'point'], 'pie': ['pie', 'circle']}
        for vis_type, keywords in visualization_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                return vis_type
        return 'line'

    def fetch_data_for_visualization(self, query: str) -> Dict[str, Union[List[int], List[str]]]:
        # This is a placeholder implementation. You should replace it with actual data fetching logic.
        numbers = [int(s) for s in query.split() if s.isdigit()]
        if numbers:
            data = {'x': list(range(1, len(numbers) + 1)), 'y': numbers, 'type': 'line'}
        else:
            data = {'x': [1, 2, 3, 4], 'y': [10, 11, 12, 13], 'type': 'scatter'}
        return data

    def handle_document_query(self, query, chat_history, session_id):
        response = self.document_handler.query(query)
        if not isinstance(response, str):
            logging.error(f"Expected 'response' to be a string, got {type(response)}")
            return {"type": "error", "content": "Error processing the document query."}
        self.memory.add_message(AIMessage(content=response, sender="system", session_id=session_id))
        return {"type": "text", "content": response}
    
    
    def create_response(self, content, response_type):
        return {"type": response_type, "content": content}