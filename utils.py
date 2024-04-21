import openai
import json
import logging
import re
from datetime import datetime
from langchain_community.llms import OpenAI
from visualize_data import VisualizationConfig, create_visualization
from typing import Any, Dict, List, Union, Optional
from langchain_core.utils.function_calling import convert_to_openai_function
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
from nltk import word_tokenize
from nltk.corpus import stopwords
from collections import Counter, deque
import requests
from textblob import TextBlob
import spacy


class Lenox:
    def __init__(self, tools, document_handler, prompt_engine=None, duckduckgo_search=None, connection_string="sqlite:///lenox.db", openai_api_key=None):
        self.document_handler = document_handler
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine(tools=tools)
        self.duckduckgo_search = duckduckgo_search
        self.memory = SQLChatMessageHistory(session_id="my_session", connection_string=connection_string)
        self.openai_api_key = openai_api_key  # Save the API key
        self.setup_components(tools)

        
    def setup_components(self, tools):
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.5).bind(functions=self.functions)
        self.prompt = self.configure_prompts()
        self.chain = self.setup_chain()
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=False)        
        
    def configure_prompts(self):
        return ChatPromptTemplate.from_messages([
            ("system", "Hello! 🌟 I'm Lenox, your digital assistant. Whether you're looking for advice, need help navigating complex topics, or just want to chat, I'm here to light up the path ahead. 🚀 Let's make today a stepping stone to new discoveries and achievements. What exciting quest can I assist you with today?"),
            ("user", "Hi Lenox!"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def setup_chain(self):
        return RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(x.get("intermediate_steps", []))
        ) | self.prompt | self.model | OpenAIFunctionsAgentOutputParser()
        

    
    def synthesize_text(self, model, input_text, voice, response_format='mp3', speed=1):
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "input": input_text,
            "voice": voice,
            "response_format": response_format,
            "speed": speed
        }
        
        response = requests.post('https://api.openai.com/v1/audio/speech', headers=headers, json=data)
        
        if response.status_code == 200:
            # Assuming the API returns the direct binary content of the audio file
            audio_file_path = "output.mp3"
            with open(audio_file_path, 'wb') as f:
                f.write(response.content)
            return audio_file_path
        else:
            print(f"Failed to synthesize audio: {response.status_code}, {response.text}")
            return None



    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        if not query:
            return {"type": "text", "content": "Please enter a query."}

        self.memory.session_id = session_id
        new_message = HumanMessage(content=query, sender="user")
        self.memory.add_message(new_message)
        chat_history = self.memory.messages()

        # Check for visualization intent
        if self.is_visualization_query(query):
            vis_type = self.parse_visualization_type(query)
            data = self.fetch_data_for_visualization(query)
            if not data:
                return {"type": "error", "content": "Data for visualization could not be fetched."}
            visualization_config = VisualizationConfig(data=data, visualization_type=vis_type)
            visualization_json = create_visualization(visualization_config)
            self.memory.add_message(AIMessage(content=visualization_json))
            return self.create_response(visualization_json, "visual")

        # Enhanced intent recognition for search using regex to match broader search intents
        if re.search(r"\b(search for|find|lookup|where can i find)\b", query, re.IGNORECASE):
            if self.duckduckgo_search:
                search_result = self.duckduckgo_search.run(query)
                return {"type": "text", "content": search_result}
            else:
                return {"type": "text", "content": "Search tool is not configured."}

        # Handle general inquiries and other types of requests through the conversational model
        result = self.qa.invoke(
            {"input": query, "chat_history": chat_history},
            config={"configurable": {"session_id": session_id}}
        )
        self.memory.add_message(AIMessage(content=result.get('output', '')))
        return {"type": "text", "content": result.get('output', "Error processing the request.")}

    def determine_query_handler(self, query: str):
        # Checking for visualization-related queries
        if self.is_visualization_query(query):
            return self.handle_visualization_query
        # Checking for document-related queries
        elif "document" in query:
            return self.handle_document_query
        # Enhanced to handle search when certain keywords are found
        elif re.search(r"\b(search|find|where|latest|news)\b", query, re.IGNORECASE):
            return self.handle_search_query
        # Default to handling general queries
        else:
            return self.handle_general_query

    def handle_search_query(self, query, chat_history, session_id):
        if self.duckduckgo_search:
            search_result = self.duckduckgo_search.run(query)
            return {"type": "text", "content": search_result}
        else:
            return {"type": "error", "content": "Search tool is not configured."}


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
    

    def get_sample_data(self):
        # Implementation as provided above
        return {
            'x': [1, 2, 3, 4, 5],
            'y': [2, 3, 5, 7, 11],
            'type': 'line'
        }

    def create_visualization(self, x, y, type='line'):
        # Implementation as provided above
        import plotly.graph_objs as go
        import plotly.offline as pyo

        data = [go.Scatter(x=x, y=y, mode=type)]
        layout = go.Layout(title='Sample Visualization')
        fig = go.Figure(data=data, layout=layout)
        return pyo.plot(fig, output_type='div')    
    

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
        response = self.document_handler.query(query)
        if not isinstance(response, str):
            logging.error(f"Expected 'response' to be a string, got {type(response)}")
            return {"type": "error", "content": "Error processing the document query."}
        self.memory.add_message(AIMessage(content=response, sender="system", session_id=session_id))
        return {"type": "text", "content": response}
    

    
    
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
