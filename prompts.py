import logging
from typing import Dict, List, Any
from enum import Enum
import re

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
    def __init__(self, config: PromptEngineConfig, tools: List[Any] = None):
        self.config = config
        self.tools = {f"tool_{i}": tool for i, tool in enumerate(tools)} if tools else {}

    def preprocess_query(self, user_query: str) -> str:
        query = user_query.strip().lower()
        query = re.sub(r'\s+', ' ', query)
        query = re.sub(r'[^\w\s]', '', query)
        stopwords = {'the', 'is', 'in', 'and', 'to', 'of'}
        query_words = query.split()
        filtered_words = [word for word in query_words if word not in stopwords]
        return ' '.join(filtered_words)

    def classify_intent(self, user_query: str) -> IntentType:
        user_query = user_query.lower()
        search_keywords = ["search", "find", "lookup", "current", "latest", "information"]
        if any(keyword in user_query for keyword in search_keywords):
            return IntentType.SEARCH
        if any(greeting in user_query for greeting in ["hi", "hello", "hey"]):
            return IntentType.GREETING
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
        logger.debug(f"Classified intent: {intent}")
        if intent == IntentType.SEARCH:
            return {"response": "Search functionality is not implemented."}
        elif intent == IntentType.VISUALIZATION:
            return self.visualization_response(user_query)
        elif intent == IntentType.EMOTIONAL_SUPPORT:
            return self.emotional_support_response(user_query)
        elif intent == IntentType.GREETING:
            return {"response": "Hello! How can I assist you today?"}
        elif intent == IntentType.SMALLTALK:
            return {"response": "I'm here to help. What do you need assistance with?"}
        elif intent == IntentType.GRATITUDE:
            return {"response": "You're welcome!"}
        elif intent == IntentType.AFFIRMATION:
            return {"response": "Thank you! I appreciate it."}
        elif intent == IntentType.CURIOSITY:
            return {"response": "That's an interesting question. What specifically would you like to know more about?"}
        elif intent == IntentType.FEEDBACK:
            return {"response": "I appreciate your feedback. It helps me improve."}
        return {"response": "Sorry, I don't understand your query."}

    def visualization_response(self, user_query: str) -> Dict[str, Any]:
        # Placeholder for visualization logic
        return {"response": "Visualization is not implemented yet."}

    def emotional_support_response(self, user_query: str) -> Dict[str, Any]:
        emotion_level = self.detect_emotion_level(user_query)
        emotional_response = self.generate_emotional_response(emotion_level)
        return {"response": emotional_response}

    def detect_emotion_level(self, user_query: str) -> EmotionLevel:
        if "anxious" in user_query or "nervous" in user_query:
            return EmotionLevel.ANXIETY
        if "excited" in user_query or "thrilled" in user_query:
            return EmotionLevel.EXCITEMENT
        if "frustrated" in user_query or "angry" in user_query:
            return EmotionLevel.FRUSTRATION
        if "calm" in user_query or "relaxed" in user_query:
            return EmotionLevel.CALM
        return EmotionLevel.LOW

    def fetch_response_from_model(self, prompt: str) -> str:
        # Placeholder for model fetching logic
        return "This is a mock response."

    def add_interaction(self, input: str, response: str):
        # Placeholder for interaction logging logic
        logger.debug(f"Interaction logged: {input} -> {response}")

    def update_tools(self, new_tools: Dict[str, Any]):
        self.tools.update(new_tools)
