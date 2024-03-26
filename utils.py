import openai
import pandas as pd
import json
import logging
import plotly
from visualize_data import VisualizationConfig, create_visualization
from typing import Any, Dict, List, Union
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
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

class Lenox:
    def __init__(self, tools, document_handler: DocumentHandler, prompt_engine: PromptEngine = None):
        # Initialization similar to your original setup.
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.5).bind(functions=self.functions)
        self.document_handler = document_handler
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine()

        # Chat prompt template definition remains the same.
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Hello, Volcano! I'm Lenox, your AI ally, not just in the cryptocurrency domain but also your companion for private and business life. Equipped with advanced NLP techniques, I can understand and engage in more nuanced conversations, making our interactions more dynamic and personalized."),
            ("user", "Hi Lenox! I'm looking forward to our journey together."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("system", "Just so you know, I love learning new things and growing with you. Feel free to joke around or share how you feel!"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])


        # Instead of using RunnableWithMessageHistory directly, we maintain the previous chain structure.
        self.chain = RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_functions(x.get("intermediate_steps", []))
        ) | self.prompt | self.model | OpenAIFunctionsAgentOutputParser()

        # Agent executor initialization remains unchanged.
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=False)

        # Memory management setup using SQLAlchemy for conversation history.
        self.memory = SQLChatMessageHistory(session_id="my_session", connection_string="sqlite:///lenox.db")


    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        logging.debug(f"Received query: {query}")
        if not query:
            return {"type": "text", "content": "Please enter a query."}

        # Update the session ID and add the new message using the correct method.
        self.memory.session_id = session_id
        self.memory.add_message(HumanMessage(content=query, sender="user"))  # Use add_message here.
        chat_history = self.memory.messages()

        # Execute the appropriate query handler leveraging LangChain's routing
        handler = self.determine_query_handler(query)
        return handler(query, chat_history, session_id)

    def determine_query_handler(self, query: str):
        if self.is_visualization_query(query):
            return self.handle_visualization_query
        elif "document" in query:
            return self.handle_document_query
        else:
            return self.handle_general_query
        
        

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
        return chat_history[-5:]

    def create_prompt(self, context_messages: List[Dict[str, str]], user_query: str) -> str:
        # Construct a prompt with the aggregated context and the current user query
        context = " ".join([msg.content for msg in context_messages])
        return f"{context} {user_query}"
    
    def handle_document_query(self, query, chat_history, session_id):
        response = self.document_handler.query(query)
        if not isinstance(response, str):
            logging.error(f"Expected 'response' to be a string, got {type(response)}")
            return {"type": "error", "content": "Error processing the document query."}
        self.memory.add_message(AIMessage(content=response, sender="system", session_id=session_id))
        return {"type": "text", "content": response}
    
    
    def handle_reddit_query(self, query, chat_history, session_id):
        if "sentiment" in query:
            subreddit, keyword = self.extract_reddit_params(query)  # You'll need a helper function for this
            sentiment = analyze_sentiment(subreddit, keyword) 
            return {"type": "text", "content": sentiment}
        elif "trending" in query:
            subreddit = self.extract_reddit_params(query) 
            trends = find_trending_topics([subreddit])  # Assuming subreddits are always in a list
            return {"type": "text", "content": trends}
        else:
            # Handle other Reddit query types...
            parse
    
    
    def handle_visualization_query(self, query, chat_history, session_id):
        data = self.fetch_data_for_visualization(query)
        visualization_type = self.parse_visualization_type(query)
        title = self.parse_title_from_query(query)
        additional_kwargs = self.parse_additional_kwargs(query)

        visualization_config = VisualizationConfig(
            data=data, 
            visualization_type=visualization_type, 
            title=title, 
            additional_kwargs=additional_kwargs
        )
        visualization_content_str = create_visualization(visualization_config)

        response = self.create_response(visualization_content_str, response_type="visual")
        # ... rest of your handling logic... 

    def parse_title_from_query(self, query):
        if "title:" in query:
            return query.split("title:")[1].strip()
        else:
            return "My Visualization"  # Default title

    def parse_additional_kwargs(self, query):
        kwargs = {}
        if "x label:" in query:
            kwargs['x_label'] = query.split("x label:")[1].strip()
        if "y label:" in query:
            kwargs['y_label'] = query.split("y label:")[1].strip()
        return kwargs
    
    
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

    