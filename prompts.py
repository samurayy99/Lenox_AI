import logging
from datetime import datetime
from collections import deque
from enum import Enum
from typing import List, Dict, Any, Optional
from random import choice
from langchain_community.tools import DuckDuckGoSearchRun
import re

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class EmotionLevel(Enum):
    """Enumeration for emotional support responses."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    ANXIETY = "Anxiety"
    EXCITEMENT = "Excitement"
    FRUSTRATION = "Frustration"
    CALM = "Calm"


class IntentType(Enum):
    """Different types of recognized intents."""
    GREETING = "greeting"
    SMALLTALK = "smalltalk"
    SEARCH = "search"
    VISUALIZATION = "visualization"
    EMOTIONAL_SUPPORT = "emotional_support"
    GENERAL = "general"
    GRATITUDE = "gratitude"
    AFFIRMATION = "affirmation"
    CURIOSITY = "curiosity"
    FEEDBACK = "feedback"


class Interaction:
    """Represents an interaction between user and assistant."""
    def __init__(self, input: str, response: str):
        self.input = input
        self.response = response


class PromptEngineConfig:
    """Configuration class to customize prompt behavior."""
    def __init__(self, model: str = "gpt-3.5-turbo", context_length: int = 10, max_tokens: int = 4096):
        self.model = model
        self.context_length = context_length
        self.max_tokens = max_tokens


class PromptEngine:
    """Engine to generate, manage, and personalize prompts for Lenox."""
    def __init__(
            self,
            tools: Optional[Dict[str, Any]] = None,
            config: Optional[PromptEngineConfig] = None,
            description: str = "",
            emotion_support: EmotionLevel = EmotionLevel.MEDIUM,
    ) -> None:
        self.config = config or PromptEngineConfig()
        self.history: deque[Interaction] = deque(maxlen=self.config.context_length)
        self.tools = tools or {}
        self.description = description
        self.emotion_support = emotion_support
        self.search_tool = DuckDuckGoSearchRun()

    def generate_emotional_response(self, emotion_support: EmotionLevel) -> str:
        """Generate an emotional response based on the specified emotion level."""
        responses: Dict[EmotionLevel, List[str]] = {
            EmotionLevel.HIGH: [
                "You're doing phenomenal! Together, we'll overcome any challenge.",
                "You're incredible! Let's achieve even more together."
            ],
            EmotionLevel.MEDIUM: [
                "You're doing well! Let's refine your strategy further.",
                "You're on the right path. What's next?"
            ],
            EmotionLevel.LOW: [
                "Stay consistent; you're doing great!",
                "Small progress leads to big results. Let's keep moving forward."
            ],
            EmotionLevel.ANXIETY: [
                "Staying calm and diversifying can help. Let's discuss strategies.",
                "Don't worry. I'm here to help manage market fluctuations."
            ],
            EmotionLevel.EXCITEMENT: [
                "Keep that energy up! Excitement is contagious.",
                "Your enthusiasm is motivating. Let's explore new opportunities!"
            ],
            EmotionLevel.FRUSTATION: [
                "Let's tackle challenges together. Frustration is temporary.",
                "Don't be discouraged. We'll find a solution."
            ],
            EmotionLevel.CALM: [
                "A calm, focused approach helps maintain momentum.",
                "Keep your goals steady and balanced. Let's grow step-by-step."
            ]
        }
        return choice(responses.get(emotion_support, ["I'm here to guide and support you."]))

    @staticmethod
    def classify_intent(user_query: str) -> IntentType:
        """Classify user query to identify intent with nuanced strategies."""
        lower_query = user_query.lower()
        greetings = ["hi", "hello", "hey", "howdy", "hola", "salut"]
        if any(greeting in lower_query for greeting in greetings):
            return IntentType.GREETING
        if re.search(r"\b(how are you|what's up|how do you do|how's it going)\b", lower_query):
            return IntentType.SMALLTALK
        if re.search(r"\b(search|find|lookup|explore|where can i find)\b", lower_query):
            return IntentType.SEARCH
        if re.search(r"\b(visualize|graph|chart|plot|display data)\b", lower_query):
            return IntentType.VISUALIZATION
        if re.search(r"\b(worried|excited|stressed|depressed|anxious|fearful|sad|happy|angry|joyful)\b", lower_query):
            return IntentType.EMOTIONAL_SUPPORT
        if re.search(r"\b(thanks|thank you|grateful)\b", lower_query):
            return IntentType.GRATITUDE
        if re.search(r"\b(great|good job|well done|awesome|fantastic|amazing)\b", lower_query):
            return IntentType.AFFIRMATION
        if re.search(r"\b(why|how|what if|when|who|where|which)\b", lower_query):
            return IntentType.CURIOSITY
        if re.search(r"\b(feedback|suggestion|advice|recommendation)\b", lower_query):
            return IntentType.FEEDBACK
        return IntentType.GENERAL

    def generate_dynamic_prompt(self, user_query: str, context_messages: List[Dict[str, Any]]) -> str:
        """Create a dynamic prompt based on user query, context, and emotional support."""
        intent = self.classify_intent(user_query)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_context = " ".join([msg["content"] for msg in context_messages])
        emotional_response = self.generate_emotional_response(self.emotion_support)

        prompt_templates: Dict[IntentType, List[str]] = {
            IntentType.GREETING: [
                f"Hello! It's {now}. {history_context}\nHow can I assist you today?",
                f"Hey there! How are you? {now}. {history_context}\nWhat's on your mind?"
            ],
            IntentType.SMALLTALK: [
                f"Currently, it's {now}. How are you doing today?",
                f"How's everything? I'm here to help with anything you need."
            ],
            IntentType.SEARCH: [
                f"{now} | Context: {history_context}\nSearch Results: {{search_results}}\nWhat would you like to explore further?",
                f"{now} | {history_context}\nI've got these results for you: {{search_results}}. What else can we discover?"
            ],
            IntentType.VISUALIZATION: [
                f"{now} | Context: {history_context}\nLet's create a visualization to understand the data better.",
                f"{now} | {history_context}\nWant to visualize your data? Let's see what insights we can find!"
            ],
            IntentType.EMOTIONAL_SUPPORT: [
                f"{now} | Context: {history_context}\n{emotional_response} How can I offer more support?",
                f"{now} | {history_context}\n{emotional_response} Let's talk and work through this together."
            ],
            IntentType.GRATITUDE: [
                f"{now} | Context: {history_context}\nYou're welcome! What else can I help with today?",
                f"{now} | {history_context}\nI'm always happy to assist. Let me know what more you'd like!"
            ],
            IntentType.AFFIRMATION: [
                f"{now} | Context: {history_context}\nYou're doing awesome! What would you like to tackle next?",
                f"{now} | {history_context}\nFantastic! Let's keep this momentum going. What's next?"
            ],
            IntentType.CURIOSITY: [
                f"{now} | Context: {history_context}\nThat's a fascinating question! Let's explore that together.",
                f"{now} | {history_context}\nIntriguing! I'm excited to uncover more. Let's investigate."
            ],
            IntentType.FEEDBACK: [
                f"{now} | Context: {history_context}\nI'd love to hear your suggestions. What's on your mind?",
                f"{now} | {history_context}\nYour insights are valuable. What ideas do you have?"
            ],
            IntentType.GENERAL: [
                f"{now} | Context: {history_context}\nHow can I assist with '{user_query}'?",
                f"{now} | {history_context}\nTell me how I can help with '{user_query}' today."
            ]
        }

        if intent == IntentType.SEARCH:
            search_results = self.search_tool.run(user_query)
            prompt = prompt_templates[IntentType.SEARCH][0].format(search_results=search_results)
        else:
            prompt = choice(prompt_templates.get(intent, prompt_templates[IntentType.GENERAL]))

        return prompt

    def handle_query(self, user_query: str) -> str:
        """Process the user query and create a response based on the generated prompt."""
        context_messages = [{"content": f"User: {interaction.input}, Assistant: {interaction.response}"} for interaction in self.history]
        prompt = self.generate_dynamic_prompt(user_query, context_messages)
        logging.info(f"Generated Prompt: {prompt}")
        response = f"Simulated Response: I'll do my best to assist with your query about '{user_query}'."
        self.add_interaction(user_query, response)
        return response

    def add_interaction(self, input: str, response: str):
        """Record the interaction between user and assistant."""
        self.history.append(Interaction(input, response))

    def update_tools(self, new_tools: Dict[str, Any]):
        """Update the toolset of the PromptEngine to enhance its capabilities."""
        self.tools.update(new_tools)
        logging.info("Tools updated successfully.")
