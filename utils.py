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
    def __init__(self, tools, document_handler: DocumentHandler, prompt_engine=None):
        self.document_handler = document_handler
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine(tools=tools)
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.5).bind(functions=self.functions)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Hello, Volcano! 🌟 I'm Lenox, your AI sidekick in the crypto universe. Whether you're looking to crack market trends, need strategic advice, or just feel like chatting about your financial goals, I'm here for you. With robust market analysis and a splash of empathy, let's make sure our journey is not only informative but also enjoyable. Ready to explore what the markets have in store for us? 🚀"),
            ("user", "Hi Lenox! Excited to start this journey with you. Let's dive right into the market. 📈"),
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
        chat_history = self.memory.messages(limit=5)  # This now correctly uses the updated method

        if self.is_visualization_query(query):
            return self.handle_visualization_query(query, chat_history, session_id)
        else:
            return self.handle_general_query(query, chat_history, session_id)


    

    def handle_general_query(self, query: str, chat_history, session_id: str) -> dict:
        # Generate a dynamic prompt using PromptEngine
        prompt_text = self.prompt_engine.generate_prompt(query, chat_history)
        result = self.qa.invoke({"input": prompt_text, "chat_history": chat_history},
                                config={"configurable": {"session_id": session_id}})
        output = result.get('output', "Let me think about that and get back to you.")
        self.memory.add_message(AIMessage(content=output, sender="system", session_id=session_id))
        
        return {"type": "text", "content": output}

    def truncate_history(self, query, chat_history):
        # This function needs to handle the complexity of message objects and token count accurately
        total_tokens = len(query.split())
        max_tokens = 1500  # Adjust the token limit as needed
        optimized_history = []

        for message in reversed(chat_history):
            if isinstance(message, HumanMessage) or isinstance(message, AIMessage):
                message_tokens = len(message.content.split())
                if total_tokens + message_tokens > max_tokens:
                    break
                total_tokens += message_tokens
                optimized_history.insert(0, message)

        return optimized_history

    def handle_visualization_query(self, query, chat_history, session_id):
        data = self.fetch_data_for_visualization(query)
        if not data:
            return {"type": "error", "content": "Data for visualization could not be fetched."}
        
        visualization_type = self.parse_visualization_type(query)
        visualization_config = VisualizationConfig(data=data, visualization_type=visualization_type)
        visualization_content = create_visualization(visualization_config)
        self.memory.add_message(AIMessage(content=visualization_content, sender="system", session_id=session_id))
        
        return self.create_response(visualization_content, "visual")

    def aggregate_context(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        enriched_context = []
        recent_content = " ".join(msg['content'] for msg in chat_history[-5:])  # Consider only the last 5 messages

        # Basic keyword extraction using simple split and filter method
        keywords = set(word.lower() for word in recent_content.split() if len(word) > 4 and word.isalpha())

        # Sentiment analysis on recent messages to reduce processing
        sentiment = TextBlob(recent_content).sentiment

        for message in chat_history:
            msg_sentiment = TextBlob(message['content']).sentiment
            enriched_context.append({
                "content": message['content'],
                "sentiment": msg_sentiment.polarity,
                "keywords": list(keywords)
            })

        # Adding summary sentiment for the context
        enriched_context.append({
            "overall_sentiment": sentiment.polarity,
            "summary_keywords": list(keywords)
        })

        return enriched_context


    def process_feedback(self, feedback: str, message: str) -> dict:
        # Process the feedback and associated message
        logging.info(f"Feedback received: {feedback} for message: {message}")
        # Add additional logic as needed based on the feedback and message content
        return {"message": "Feedback received and processed"}




    def is_visualization_query(self, query: str) -> bool:
        visualization_keywords = ["visualize", "graph", "chart", "plot"]
        query_tokens = set(query.lower().split())
        return any(keyword in query_tokens for keyword in visualization_keywords)


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