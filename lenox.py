import logging
import requests
from typing import Dict, List, Union, Any
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents.format_scratchpad import format_to_openai_functions
from lenox_memory import SQLChatMessageHistory
from prompts import PromptEngine, IntentType
from visualize_data import VisualizationConfig, create_visualization
from query_preprocessor import preprocess_query
from api_integration import APIIntegration
from langchain_community.tools.tavily_search import TavilySearchResults

class Lenox:
    def __init__(self, tools: Dict[str, Any], document_handler, prompt_engine=None, tavily_search=None, connection_string="sqlite:///lenox.db", openai_api_key=None, api_integration=None):
        self.document_handler = document_handler
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine(tools=tools)
        self.tavily_search = tavily_search if tavily_search else TavilySearchResults()
        self.memory = SQLChatMessageHistory(session_id="my_session", connection_string=connection_string)
        self.openai_api_key = openai_api_key
        self.api_integration = api_integration if api_integration else APIIntegration(openai_api_key)
        self.setup_components(tools)
        
    def setup_components(self, tools: Dict[str, Any]):
        assert tools is not None and len(tools) > 0, "Tools are not initialized or empty"
        
        self.functions = [convert_to_openai_function(f) for f in tools.values()]
        self.model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.8).bind(functions=self.functions)
        self.prompt = self.configure_prompts()
        self.chain = self.setup_chain()
        
        # Ensure the chain is properly initialized
        assert self.chain is not None, "Agent chain is not initialized"
        
        self.qa = AgentExecutor(agent=self.chain, tools=list(tools.values()), verbose=False)

    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        if not query:
            return {"type": "text", "content": "Please enter a query."}

        self.memory.session_id = session_id
        new_message = HumanMessage(content=query)
        self.memory.add_message(new_message)
        chat_history = self.memory.messages()

        formatted_chat_history = [
            {"role": "user", "content": m.content} if isinstance(m, HumanMessage) else {"role": "assistant", "content": m.content}
            for m in chat_history
        ]

        processed_query = preprocess_query(query)
        intent = self.prompt_engine.classify_intent(processed_query)

        logging.debug(f"Processed query: {processed_query}, Intent: {intent}")

        if intent == IntentType.SEARCH:
            logging.debug("Entering SEARCH intent block")
            search_results = self.api_integration.call_tavily_search(processed_query)
            formatted_result = self.format_tavily_results(search_results)
            logging.debug(f"Formatted result: {formatted_result}")
            self.memory.add_message(AIMessage(content=formatted_result, type="ai"))
            return {"type": "ai", "content": formatted_result}

        if intent == IntentType.VISUALIZATION:
            logging.debug("Entering VISUALIZATION intent block")
            vis_type = self.parse_visualization_type(query)
            data = self.fetch_data_for_visualization(query)
            if not data:
                return {"type": "error", "content": "Data for visualization could not be fetched."}
            visualization_config = VisualizationConfig(data=data, visualization_type=vis_type)
            visualization_json = create_visualization(visualization_config)
            self.memory.add_message(AIMessage(content=visualization_json, type="ai"))
            return {"type": "ai", "content": visualization_json}

        logging.debug("Entering default intent block")
        result = self.qa.invoke({"input": query, "chat_history": formatted_chat_history})
        output = result.get('output', 'Error processing the request.')
        if not isinstance(output, str):
            output = str(output)
        self.memory.add_message(AIMessage(content=output, type="ai"))
        return {"type": "ai", "content": output}

    def format_tavily_results(self, results):
        """Format the Tavily search results."""
        formatted_results = ""
        for result in results:
            formatted_results += f"URL: {result['url']}\nContent: {result['content']}\n\n"
        return formatted_results

    def configure_prompts(self):
        """Configure the prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", "Hello! 🌟 I'm Lenox, your digital assistant. Whether you're looking for advice or need help navigating complex topics, I'm here to assist."),
            ("user", "Hi Lenox!"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def setup_chain(self):
        """Set up the agent chain."""
        return (
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: format_to_openai_functions(x.get("intermediate_steps", []))
            )
            | self.prompt
            | self.model
            | OpenAIFunctionsAgentOutputParser()
        )

    def create_visualization(self, query: str) -> dict:
        """Implement the method to handle visualization queries."""
        # Placeholder implementation
        return {"type": "text", "content": "Visualization created for the query: " + query}

    def is_visualization_query(self, query: str) -> bool:
        """Identify visualization-based queries."""
        visualization_keywords = ["visualize", "graph", "chart", "plot", "show me a graph of", "display data"]
        return any(keyword in query.lower() for keyword in visualization_keywords)

    def parse_visualization_type(self, query: str) -> str:
        """Parse the type of visualization requested."""
        visualization_keywords = {
            'line': ['line', 'linear'],
            'bar': ['bar', 'column'],
            'scatter': ['scatter', 'point'],
            'pie': ['pie', 'circle']
        }
        for vis_type, keywords in visualization_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                return vis_type
        return 'line'  # Default to line if unspecified

    def fetch_data_for_visualization(self, query: str) -> Dict[str, List[Union[int, float, str]]]:
        """Extract data for visualization."""
        numbers = [int(s) for s in query.split() if s.isdigit()]
        if numbers:
            return {'x': list(range(1, len(numbers) + 1)), 'y': [float(n) for n in numbers]}
        else:
            return {'x': [1, 2, 3, 4], 'y': [10.0, 11.0, 12.0, 13.0]}

    def create_response(self, content, response_type="text") -> dict:
        """Create a structured response."""
        if response_type == "visual":
            return {"type": response_type, "content": content}
        return {"type": "text", "content": str(content)}

    def handle_document_query(self, query: str) -> str:
        """Query the document index."""
        return self.document_handler.query(query)

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
            audio_file_path = "output.mp3"
            with open(audio_file_path, 'wb') as f:
                f.write(response.content)
            return audio_file_path
        else:
            print(f"Failed to synthesize audio: {response.status_code}, {response.text}")
            return None
