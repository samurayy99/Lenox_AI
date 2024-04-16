import spacy
from collections import Counter
import openai
import logging
from utils import AIMessage, HumanMessage
from datetime import datetime
from typing import Any

class PromptEngine:
    def __init__(self, context_length: int = 10, max_tokens: int = 4096, tools=None, model_name: str = "gpt-3.5-turbo", nlp_model: str = "en_core_web_sm"):
        self.context_length = context_length
        self.max_tokens = max_tokens
        self.tools = tools or {}
        self.model_name = model_name
        self.nlp = spacy.load(nlp_model)
        self.user_feedback = {}  # Store feedback for each tool

    def generate_prompt(self, user_query: str, context_messages: list) -> str:
        """
        Generates a dynamic and engaging prompt that incorporates the user's query
        and any relevant context from previous interactions.
        """
        context = " ".join([msg.content for msg in context_messages]) if context_messages else "What can I do for you today? 🌍"
        prompt = f"{context}\n\n🤖: How might I assist with this query?\n👤: {user_query}\n"
        return prompt

    def update_feedback_based_on_result(self, result: dict, feedback: Any) -> None:
        """
        Adjusts the internal metrics based on user feedback to improve future interactions.
        """
        if feedback is not None:
            self.user_feedback[result['tool']] = self.user_feedback.get(result['tool'], 0) + feedback

    def select_tool(self, query: str):
        """
        Selects the most appropriate tool for handling the query based on extracted keywords.
        """
        doc = self.nlp(query.lower())
        keywords = [token.lemma_ for token in doc if not token.is_stop]
        keyword_counts = Counter(keywords)
        most_common_keywords = keyword_counts.most_common(1)
        tool_mapping = {
            'analyze': 'data_analysis_tool',
            'forecast': 'market_forecasting_tool',
            'compare': 'comparative_analysis_tool',
            'visualize': 'data_visualization_tool'
        }

        for keyword, count in most_common_keywords:
            if keyword in tool_mapping:
                return tool_mapping[keyword]
        return 'general_query_handler'

    def generate_dynamic_prompt(self, user_query: str, context_messages: list, prompt_template: str = None) -> str:
        """
        Creates a custom prompt that adapts to the user's current needs, incorporating contextual data and user history.
        """
        tool_key = self.select_tool(user_query)
        data = self.fetch_data(user_query, tool_key) if tool_key else ""
        input_type = self.classify_input(user_query)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_context = f"Time: {now}\nContext: Recent interactions suggest interest in topics such as {data}."

        if input_type == "greeting":
            prompt = f"👋 Hello again! What's on your mind today?"
        else:
            prompt = f"{prompt_context}\n🧐 Let's dive deeper into your query: {user_query}\nHow can I enhance your understanding today?"
        return prompt

    def classify_input(self, user_query: str) -> str:
        """
        Determines the nature of the user's input to tailor the interaction appropriately.
        """
        if any(word in user_query.lower() for word in ['hello', 'hi', 'greetings']):
            return "greeting"
        return "query"
