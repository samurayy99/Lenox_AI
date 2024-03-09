import openai
import pandas as pd
import json
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

class Lenox:
    def __init__(self, tools):
        # Initialize the AI model with a set of tools that can be called as functions within the chat.
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(temperature=0.5).bind(functions=self.functions)

        # Define the chat prompt template with placeholders for dynamic content.
        # This setup allows for a flexible conversation structure that can include system messages, user inputs, and dynamically generated content.
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Hello, Volcano! I'm Lenox, your AI ally in the cryptocurrency domain, equipped with a range of tools to assist you."),
            ("user", "Hi Lenox! I'm excited to have you as my partner."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create a processing chain that formats intermediate steps, sets up the prompt, invokes the model, and parses the output.
        self.chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(x.get("intermediate_steps", []))
        ) | self.prompt | self.model | OpenAIFunctionsAgentOutputParser()

        # Initialize the agent executor with verbose logging disabled for cleaner output.
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=False)

        # Set up a memory system to store and retrieve chat history from a SQL database.
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
        
        
        # Handle other types of queries
        dynamic_prompt = self.generate_dynamic_prompt(query)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", dynamic_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        if self.is_visualization_query(query):
            visualization_data = self.fetch_data_for_visualization(query)
            vis_type = self.parse_visualization_type(query)
            visualization_config = VisualizationConfig(data=visualization_data, visualization_type=vis_type)
            visualization_json = create_visualization(visualization_config)
            self.memory.add_message(AIMessage(content=visualization_json))
            return self.create_response(visualization_json, "visual")
        else:
            result = self.qa.invoke(
                {"input": query, "session_id": session_id, "chat_history": chat_history},
                config={"configurable": {"session_id": session_id}}
            )
            self.memory.add_message(AIMessage(content=result.get('output', '')))
            return {"type": "text", "content": result.get('output', "")}

   
    def is_visualization_query(self, query: str) -> bool:
        visualization_keywords = ["visualize", "graph", "chart", "plot", "show me a graph of", "display data"]
        return any(keyword in query.lower() for keyword in visualization_keywords)

    def parse_visualization_type(self, query: str) -> str:
        visualization_keywords = {'line': ['line', 'linear'], 'bar': ['bar', 'column'], 'scatter': ['scatter', 'point'], 'pie': ['pie', 'circle']}
        for vis_type, keywords in visualization_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                return vis_type
        return 'line'  # Default to line if no specific type is mentioned

    def fetch_data_for_visualization(self, query: str) -> Dict[str, Union[List[int], List[str]]]:
        numbers = [int(s) for s in query.split() if s.isdigit()]
        if numbers:
            data = {'x': list(range(1, len(numbers) + 1)), 'y': numbers, 'type': 'line'}
        else:
            data = {'x': [1, 2, 3, 4], 'y': [10, 11, 12, 13], 'type': 'scatter'}
        return data

    def create_response(self, content, response_type="text") -> dict:
        logging.debug(f"Creating response: {content}, Type: {response_type}")
        if response_type == "visual":
            try:
                content = json.loads(content) if isinstance(content, str) else content
                if 'data' not in content or 'layout' not in content:
                    raise ValueError("Missing 'data' or 'layout' in visualization content.")
            except (json.JSONDecodeError, ValueError) as e:
                logging.error(f"Error processing visualization data: {e}")
                return {"type": "error", "content": f"Error processing visualization data: {e}"}
        return {"type": response_type, "content": content}