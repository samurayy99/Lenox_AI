import spacy
from collections import Counter
import openai
import logging
from textblob import TextBlob
from datetime import datetime
from typing import Any, List, Dict
from utils import AIMessage, HumanMessage  # Correct import based on your project structure
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

class PromptEngine:
    def __init__(self, context_length: int = 10, max_tokens: int = 4096, tools=None, model_name: str = "gpt-3.5-turbo-0125", nlp_model: str = "en_core_web_sm"):
        self.context_length = context_length
        self.max_tokens = max_tokens
        self.tools = tools or {}
        self.model_name = model_name
        self.nlp = spacy.load(nlp_model)
        self.vectorizer = TfidfVectorizer()
        self.model_knn = NearestNeighbors(n_neighbors=1, algorithm='auto')

    def generate_prompt(self, user_query: str, context_messages: list, parsed_data: dict) -> str:
        context = " ".join([msg.content for msg in context_messages[-self.context_length:]]) if context_messages else "How may I assist you today?"
        entities = ', '.join([f"{ent[0]} ({ent[1]})" for ent in parsed_data['entities']])
        keywords = ', '.join(parsed_data['keywords'])
        sentiment = self.calculate_sentiment(context)

        prompt = f"Context: {context}\nSentiment: {sentiment}\nRecognized entities: {entities}\nKey terms: {keywords}\n\n🤖: What specific assistance can I provide regarding '{user_query}'?\n👤: "
        return prompt

    def calculate_sentiment(self, text):
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def select_tool(self, query: str) -> str:
        query_vec = self.vectorizer.transform([query])
        _, indices = self.model_knn.kneighbors(query_vec)
        return self.tools[indices[0][0]]

    def generate_dynamic_prompt(self, user_query: str, context_messages: list) -> str:
        context = " ".join([msg.content for msg in context_messages])
        tool_key = self.select_tool(context + " " + user_query)
        prompt = f"Latest Interaction: {context}\nSelected Tool: {tool_key}\n🧐 Let's explore your query further: {user_query}\nHow can we refine your request?"
        return prompt

    def train_context_model(self, dataset: List[str]):
        X = self.vectorizer.fit_transform(dataset)
        self.model_knn.fit(X)
        
    def update_feedback_based_on_result(self, session_id: str, feedback: Any) -> None:
        # Your code to update feedback here
        print("Feedback has been updated based on results.")
    

    def handle_user_interaction(self, query: str, session_id: str, feedback: Any):
        # Process query and feedback, dynamically adapt future interactions
        context_messages = self.retrieve_context(session_id)  # Assume a method to retrieve past messages
        prompt = self.generate_dynamic_prompt(query, context_messages)
        self.update_feedback_based_on_result(session_id, feedback)  # Corrected method call
        return prompt