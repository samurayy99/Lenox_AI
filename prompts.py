import logging
from datetime import datetime
from typing import List, Dict, Any
from langchain_community.tools import DuckDuckGoSearchRun

class PromptEngine:
    """
    An advanced prompt engine designed to dynamically manage conversational context, utilize external tools,
    and provide context-aware, intelligent responses. This engine integrates a direct search capability,
    handles different types of queries, and customizes prompts to enhance interaction with a ChatGPT-like model.
    """

    def __init__(self, tools, model_name: str, context_length: int = 10, max_tokens: int = 4096):
        """
        Initializes the PromptEngine with settings to handle detailed conversational contexts.

        :param tools: A dictionary of tools for data retrieval and external functionalities.
        :param model_name: The name of the AI model used for generating responses.
        :param context_length: Number of context messages to consider for creating prompts.
        :param max_tokens: Maximum number of tokens allowed in the prompt.
        """
        self.context_length = context_length
        self.max_tokens = max_tokens
        self.tools = tools
        self.model_name = model_name
        self.search_tool = DuckDuckGoSearchRun()  # Initialize the search tool
        logging.basicConfig(level=logging.INFO)

    def classify_intent(self, user_query: str) -> str:
        """
        Determines the user's intent to tailor the response strategy, integrating search directly when needed.
        """
        if any(keyword in user_query.lower() for keyword in ["search", "find", "latest news", "update"]):
            return "search"
        if "visualize" in user_query.lower() or "chart" in user_query.lower():
            return "visualization"
        if any(keyword in user_query.lower() for keyword in ["help", "support", "how do I", "what is"]):
            return "informational"
        return "general"

    def generate_prompt(self, user_query: str, context_messages: List[Dict[str, Any]]) -> str:
        """
        Generates a dynamic prompt based on the user's query and historical context, tailoring the prompt
        for the AI model based on detected intent and user interaction history.
        """
        intent = self.classify_intent(user_query)
        context_text = " ".join(msg['content'] for msg in context_messages[-self.context_length:])
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if intent == "search":
            search_results = self.search_tool.run(user_query)
            prompt = f"{now} | Context: {context_text}\nSearch Results: {search_results}\nAI: What more would you like to know about this?"
        elif intent == "visualization":
            prompt = f"{now} | Context: {context_text}\nAI: Let's create a visualization based on your request."
        else:
            prompt = f"{now} | Context: {context_text}\nAI: How can I assist you further with '{user_query}'?"

        return prompt

    def update_tools(self, new_tools: Dict[str, Any]):
        """
        Updates the toolset of the PromptEngine to enhance its capabilities.
        """
        self.tools.update(new_tools)
        logging.info("Tools updated successfully.")

    def process_query(self, user_query: str, context_messages: List[Dict[str, Any]]) -> str:
        """
        Processes the user query by generating a dynamic prompt and invoking the AI model to get a response.
        """
        prompt = self.generate_prompt(user_query, context_messages)
        return self.invoke_ai_model(prompt)

    def invoke_ai_model(self, prompt: str) -> str:
        """
        Simulates invoking an AI model with the dynamically generated prompt. Replace this with actual API calls.
        """
        logging.info(f"Invoking AI model with prompt: {prompt}")
        return "This is a simulated response based on the prompt."
