
import logging
from typing import Dict, List, Any

from enum import Enum

from query_preprocessor import preprocess_query
from api_integration import perform_tavily_search
from response_formatter import format_tavily_results

class IntentType(Enum):
    GREETING = "greeting"
    SEARCH = "search"
    VISUALIZATION = "visualization"
    SMALLTALK = "smalltalk"
    EMOTIONAL_SUPPORT = "emotional_support"
    GRATITUDE = "gratitude"
    AFFIRMATION = "affirmation"
    CURIOSITY = "curiosity"
    FEEDBACK = "feedback"
    GENERAL = "general"
    UNKNOWN = "unknown"

class EmotionLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ANXIETY = "anxiety"
    EXCITEMENT = "excitement"
    FRUSTRATION = "frustration"
    CALM = "calm"

class PromptEngineConfig:
    def __init__(self, context_length: int = 10, max_tokens: int = 4096):
        self.context_length = context_length
        self.max_tokens = max_tokens

class PromptEngine:
    def __init__(self, config: PromptEngineConfig, tools: Dict[str, Any] = None):
        self.config = config
        self.tools = tools or {}

    def classify_intent(self, user_query: str) -> IntentType:
        user_query = user_query.lower()
        if any(greeting in user_query for greeting in ["hi", "hello", "hey"]):
            return IntentType.GREETING
        if any(search in user_query for search in ["search", "find", "what is", "how to", "weather"]):
            return IntentType.SEARCH
        if any(visual in user_query for visual in ["visualize", "graph", "chart", "plot"]):
            return IntentType.VISUALIZATION
        if any(smalltalk in user_query for smalltalk in ["how are you", "what's up"]):
            return IntentType.SMALLTALK
        if any(emotion in user_query for emotion in ["help", "support", "feel"]):
            return IntentType.EMOTIONAL_SUPPORT
        if any(gratitude in user_query for gratitude in ["thank you", "thanks"]):
            return IntentType.GRATITUDE
        if any(affirmation in user_query for affirmation in ["great", "good job", "well done"]):
            return IntentType.AFFIRMATION
        if any(curiosity in user_query for curiosity in ["curious", "wonder"]):
            return IntentType.CURIOSITY
        if any(feedback in user_query for feedback in ["feedback", "comment"]):
            return IntentType.FEEDBACK
        return IntentType.UNKNOWN



    def generate_emotional_response(self, emotion_support: EmotionLevel) -> str:
        responses = {
            EmotionLevel.ANXIETY: "It's okay, take a deep breath. How can I assist you?",
            EmotionLevel.EXCITEMENT: "That's awesome! What's got you excited?",
            EmotionLevel.FRUSTRATION: "I'm here to help. What's bothering you?",
            EmotionLevel.CALM: "I'm glad to hear you're feeling calm. How can I assist you today?"
        }
        return responses.get(emotion_support, "How can I assist you today?")

    def generate_dynamic_prompt(self, user_query: str, context_messages: List[str]) -> str:
        context = " ".join(context_messages[-self.config.context_length:])
        return f"{context} {user_query}"

    def handle_query(self, user_query: str) -> Dict[str, Any]:
        intent = self.classify_intent(user_query)
        logging.debug(f"Classified intent: {intent}")
        if intent == IntentType.SEARCH:
            return self.search_response(user_query)
        elif intent == IntentType.VISUALIZATION:
            return self.visualization_response(user_query)
        return {"response": "Sorry, I don't understand your query."}

    def search_response(self, user_query: str) -> Dict[str, Any]:
        query = preprocess_query(user_query)
        results = perform_tavily_search(query)
        formatted_results = format_tavily_results(results)
        return {"response": formatted_results}

    def visualization_response(self, user_query: str) -> Dict[str, Any]:
        # Your visualization logic here
        return {"response": "Visualization is not implemented yet."}

    def fetch_response_from_model(self, prompt: str) -> str:
        # Your model fetching logic here
        return "This is a mock response."

    def add_interaction(self, input: str, response: str):
        # Your interaction logging logic here
        pass

    def update_tools(self, new_tools: Dict[str, Any]):
        self.tools.update(new_tools)

