import openai
import pandas as pd
import json
import logging
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
        self.model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5).bind(functions=self.functions)
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

    def handle_visualization_query(self, query, chat_history, session_id):
        data = self.fetch_data_for_visualization(query)
        visualization_type = self.parse_visualization_type(query)
        visualization_config = VisualizationConfig(data=data, visualization_type=visualization_type)
        # Assume create_visualization stores the config and returns an ID
        visualization_id = create_visualization(visualization_config)

        simplified_response = f"Visualization created. [View Visualization](visualization_id={visualization_id})"
        self.memory.add_message(AIMessage(content=simplified_response, sender="system", session_id=session_id))

        # Return a response that includes the visualization ID instead of the full config
        return {"type": "visual", "content": visualization_id}

    def create_response(self, content, response_type="text") -> dict:
        logging.debug(f"Creating response: {content}, Type: {response_type}")
        if response_type == "visual":
            if isinstance(content, str):
                try:
                    json.loads(content)  # Attempt to parse the string to ensure it's valid JSON
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON for visualization data: {e}. Content: {content}")
                    return {"type": "error", "content": "Invalid JSON for visualization data."}
            else:
                try:
                    content = json.dumps(content, cls=plotly.utils.PlotlyJSONEncoder)
                except TypeError as e:
                    logging.error(f"Error serializing visualization data: {e}. Content type: {type(content)}")
                    return {"type": "error", "content": "Error serializing visualization data."}
        else:
            if not isinstance(content, str):
                content = str(content)
        return {"type": response_type, "content": content}

    def handle_general_query(self, query: str, chat_history: List[Dict[str, Any]], session_id: str) -> dict:
        # Enhanced context aggregation to provide better input for the model
        # Adjusted to access the 'content' attribute directly
        context_messages = [msg.content for msg in self.aggregate_context(chat_history)]
        
        # Introduce more conversational and empathetic elements into the prompt
        personalized_intro = "I'm here to help you with anything you need. Let's make this conversation helpful and enjoyable. "
        query_acknowledgement = f"You asked: '{query}'. Let me think about that."
        
        # Incorporating personalized introduction and query acknowledgement into the prompt
        prompt_text = self.prompt_engine.generate_dynamic_prompt(query, context_messages)
        prompt_text = personalized_intro + query_acknowledgement + prompt_text

        result = self.qa.invoke(
            {"input": prompt_text, "chat_history": chat_history},
            config={"configurable": {"session_id": session_id}}
        )
        output = result.get('output', "Error processing the request.")
        if isinstance(output, str):
            # Adjust the tone of the AI's response to be more conversational and empathetic directly here
            # For example, appending a friendly sign-off to each response
            output += " Is there anything else I can help with?"
            self.memory.add_message(AIMessage(content=output, sender="system", session_id=session_id))
        else:
            logging.error(f"Expected 'output' to be a string, got {type(output)}")
            return {"type": "error", "content": "Error processing the request."}
        return {"type": "text", "content": output}
    def aggregate_context(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        # Aggregate recent messages to provide a rich context for the model
        # You can customize the number of messages to include based on your model's capacity and your use case
        return chat_history[-5:]


        
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