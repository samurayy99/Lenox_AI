import openai
import pandas as pd
import json
import logging
import os
import plotly
from langchain.tools import Tool, BaseTool
from autogen import ConversableAgent, OpenAIWrapper 
from autogen.agentchat.contrib.capabilities.teachability import Teachability
from langsmith import wrappers
from openai import OpenAI
from visualize_data import VisualizationConfig, create_visualization
from typing import Any, Dict, List, Union
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents.format_scratchpad import format_to_openai_functions
from lenox_memory import SQLChatMessageHistory
from documents import DocumentHandler
from prompts import PromptEngine
from langchain.chains import load_summarize_chain
from dotenv import load_dotenv


class Lenox(ConversableAgent):
    def __init__(self, tools, document_handler: DocumentHandler, prompt_engine: PromptEngine = None):
        load_dotenv()

        llm_config = {'model': os.getenv('MODEL_NAME', 'gpt-3.5-turbo-0125')}

        super().__init__(name="Lenox", human_input_mode="NEVER", llm_config=llm_config)
        self.logger = logging.getLogger(__name__)
        self.document_handler = document_handler
        self.prompt_engine = prompt_engine or PromptEngine()
        self.memory = SQLChatMessageHistory(session_id=os.getenv("SESSION_ID", "my_session"), connection_string=os.getenv("DB_CONNECTION_STRING", "sqlite:///lenox.db"))

        self.teachability = Teachability(path_to_db_dir=os.getenv("TEACHABILITY_DB_DIR", "./tmp/teachable_agent_db"))
        self.teachability.add_to_agent(self)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Hello, I'm Lenox, your advanced AI assistant."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Registering functions from tools for dynamic invocation
        self.tools = [convert_to_openai_function(f) for f in tools]

        # Double-check if the tools are correctly formatted
        assert all(isinstance(tool, Tool) for tool in self.tools), "All tools should be instances of langchain Tool class."

        # Initialize AgentExecutor after all other setup is complete
        # Ensure that 'agent' is recognized as a valid agent by AgentExecutor
        self.agent_executor = AgentExecutor(agent=self, tools=self.tools, verbose=True)

        for tool in self.tools:
            if hasattr(tool, "description"):
                self.register_function(tool, caller=self, executor=self.agent_executor, name=tool.name, description=tool.description)
            else:
                self.logger.warning(f"Tool {tool.name} lacks a description and wasn't registered.")

    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        if not query:
            return {"type": "text", "content": "Please enter a query."}

        self.memory.session_id = session_id
        self.memory.add_message(HumanMessage(content=query, sender="user"))

        chat_history = self.memory.get_trimmed_messages(limit=15)
        self.process_query_with_teachability(query, chat_history)

        response = self.agent_executor.invoke({"input": query, "chat_history": chat_history})

        self.memory.add_message(AIMessage(content=response['output'], sender="system"))
        return response

    def process_query_with_teachability(self, query: str, chat_history: list):
        self.teachability.process_last_received_message(query)
        related_memos = self.teachability.get_related_memos(query, n_results=10, threshold=1.5)
        if related_memos:
            self.logger.info(f"Recalled information: {related_memos}")
            chat_history.extend(related_memos)


    def handle_query(self, query: str, chat_history: list, session_id: str) -> dict:
        # Implement specific query handling logic here
        # For demonstration, simply returning a placeholder response
        return {"type": "text", "content": "Query handling logic goes here."}


    def determine_query_handler(self, query: str):
        if self.is_visualization_query(query):
            return self.handle_visualization_query
        elif "document" in query:
            return self.handle_document_query
        else:
            return self.handle_general_query

    def handle_visualization_query(self, query, chat_history, session_id):
        data = self.fetch_data_for_visualization(query)
        visualization_type = self.parse_visualization_type(query)
        visualization_config = VisualizationConfig(data=data, visualization_type=visualization_type)
        visualization_content_str = create_visualization(visualization_config)

        response = self.create_response(visualization_content_str, response_type="visual")
        if 'content' in response and isinstance(response['content'], str):
            self.memory.add_message(AIMessage(content=response['content'], sender="system", session_id=session_id))
        else:
            logging.error("Visualization response content is not a string.")
            return {"type": "error", "content": "Error processing the visualization."}
        return response

    def create_response(self, content, response_type="text") -> dict:
        logging.debug(f"Creating response: {content}, Type: {response_type}")
        if response_type == "visual":
            # Check if content is already a JSON string
            if isinstance(content, str):
                try:
                    # Attempt to parse the string to ensure it's valid JSON
                    json.loads(content)
                    # If parsing is successful, use the content directly
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON for visualization data: {e}")
                    return {"type": "error", "content": "Invalid JSON for visualization data."}
            else:
                # If content is not a string, attempt to serialize it to JSON
                try:
                    content = json.dumps(content, cls=plotly.utils.PlotlyJSONEncoder)
                except TypeError as e:
                    logging.error(f"Error serializing visualization data: {e}")
                    return {"type": "error", "content": "Error serializing visualization data."}
        else:
            # For non-visual response types, ensure content is a string
            if not isinstance(content, str):
                content = str(content)
        return {"type": response_type, "content": content}


    def handle_general_query(self, query: str, chat_history: List[Dict[str, Any]], session_id: str) -> dict:
        # Enhanced context aggregation to provide better input for the model
        # Adjusted to access the 'content' attribute directly
        context_messages = [msg.content for msg in self.aggregate_context(chat_history)]
        prompt_text = self.prompt_engine.generate_dynamic_prompt(query, context_messages)

        result = self.qa.invoke(
            {"input": prompt_text, "chat_history": chat_history},
            config={"configurable": {"session_id": session_id}}
        )
        output = result.get('output', "Error processing the request.")
        if isinstance(output, str):
            self.memory.add_message(AIMessage(content=output, sender="system", session_id=session_id))
        else:
            logging.error(f"Expected 'output' to be a string, got {type(output)}")
            return {"type": "error", "content": "Error processing the request."}
        return {"type": "text", "content": output}
    
    
    def aggregate_context(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        # Aggregate recent messages to provide a rich context for the model
        # You can customize the number of messages to include based on your model's capacity and your use case
        return chat_history[-7:]

    

    def create_prompt(self, context_messages: List[Dict[str, str]], user_query: str) -> str:
        # Construct a prompt with the aggregated context and the current user query
        context = " ".join([msg.content for msg in context_messages])
        return f"{context} {user_query}"

        
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
    
    def handle_document_query(self, query, chat_history, session_id):
        doc_response = self.document_handler.query(query)
        if doc_response:
            # Tailor the response based on the content found
            response = f"I found something that might be helpful: '{doc_response}'"
        else:
            # Provide a helpful response when no relevant information is found
            response = "I couldn't find anything specific in the documents. Can I help with something else?"
        
        self.memory.add_message(AIMessage(content=response, sender="system", session_id=session_id))
        return {"type": "text", "content": response}

