import sqlite3
from typing import Dict, List, Union, Any
from visualize_data import VisualizationConfig, create_visualization
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents.format_scratchpad import format_to_openai_functions
from lenox_memory import SQLChatMessageHistory
from prompts import PromptEngine, PromptEngineConfig
import requests
import json
from web_search import WebSearchManager


class Lenox:
    def __init__(self, tools, document_handler, prompt_engine=None, connection_string="sqlite:///lenox.db", openai_api_key=None):
        self.document_handler = document_handler
        self.prompt_engine = prompt_engine if prompt_engine else PromptEngine(config=PromptEngineConfig(), tools=tools)
        self.memory = SQLChatMessageHistory(session_id="my_session", connection_string=connection_string)
        self.openai_api_key = openai_api_key  # Save the API key
        self.db_path = 'lenox.db'
        self.web_search_manager = WebSearchManager()
        self.setup_components(tools)
        self._init_feedback_table()

    def setup_components(self, tools):
        self.functions = [convert_to_openai_function(f) for f in tools]
        self.model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.8).bind(functions=self.functions)
        self.prompt = self.configure_prompts()
        self.chain = self.setup_chain()
        self.qa = AgentExecutor(agent=self.chain, tools=tools, verbose=False)

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

    
    def convchain(self, query: str, session_id: str = "my_session") -> dict:
        """Process a user query."""
        if not query:
            return {"type": "text", "content": "Please enter a query."}

        self.memory.session_id = session_id
        new_message = HumanMessage(content=query)
        self.memory.add_message(new_message)
        chat_history = self.memory.messages()

        # Use the intent detection from WebSearchManager
        intent = self.web_search_manager.detect_intent(query)

        # Handle intent using the WebSearchManager
        response = self.web_search_manager.handle_intent(intent, query)

        # If response type is text, add to memory
        if response["type"] == "text":
            self.memory.add_message(AIMessage(content=response["content"]))
        elif response["type"] == "visualization":
            # If visualization, handle visualization logic
            return self.handle_visualization_query(query, session_id=session_id)

        # If intent is unknown or response type is not handled, use general conversational handling
        if intent == "unknown" or response["type"] not in ["text", "visualization"]:
            result = self.qa.invoke({"input": query, "chat_history": chat_history})
            output = result.get('output', 'Error processing the request.')

            # Ensure output is a string
            if not isinstance(output, str):
                output = str(output)

            self.memory.add_message(AIMessage(content=output))
            return {"type": "text", "content": output}

        return response




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

    def fetch_data_for_visualization(self, query: str) -> Dict[str, Union[List[int], List[str]]]:
        """Extract data for visualization."""
        numbers = [int(s) for s in query.split() if s.isdigit()]
        if numbers:
            return {'x': list(range(1, len(numbers) + 1)), 'y': numbers}
        else:
            return {'x': [1, 2, 3, 4], 'y': [10, 11, 12, 13]}

    def handle_visualization_query(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Handle visualization-related queries.
        """
        vis_type = self.parse_visualization_type(query)
        data = self.fetch_data_for_visualization(query)
        if not data:
            return {"type": "error", "content": "Data for visualization could not be fetched."}
        
        # Ensure the data type matches the expected type
        visualization_data = {key: [float(value) if isinstance(value, int) else value for value in values] 
                              for key, values in data.items()}

        visualization_config = VisualizationConfig(data=visualization_data, visualization_type=vis_type)
        visualization_json = create_visualization(visualization_config)
        return {"type": "visualization", "content": json.loads(visualization_json)}

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

    def _init_feedback_table(self):
        # Initialize the feedback table if it does not exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            query TEXT NOT NULL,
                            feedback TEXT NOT NULL,
                            session_id TEXT NOT NULL
                        )''')
        conn.commit()
        conn.close()

    def teach_from_feedback(self, query: str, feedback: str, session_id: str) -> None:
        """
        Update the model or system based on user feedback.

        Parameters:
        - query (str): The query for which feedback is provided.
        - feedback (str): The feedback from the user.
        - session_id (str): The session ID of the user providing the feedback.
        """
        # Store feedback in the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO feedback (query, feedback, session_id) VALUES (?, ?, ?)', 
                       (query, feedback, session_id))
        conn.commit()
        conn.close()

    def process_feedback(self, feedback: str, session_id: str) -> str:
        """
        Process feedback in real-time.

        Parameters:
        - feedback (str): The feedback provided by the user.
        - session_id (str): The session ID of the user providing the feedback.

        Returns:
        - str: Response after processing feedback.
        """
        # Here you can add logic to process the feedback in real-time
        print(f"Processing feedback '{feedback}' for session '{session_id}'")
        return "Feedback processed successfully"
