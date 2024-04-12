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
        Generates a dynamic prompt based on the user's query and context messages.
        """
        # Ensure context_messages are processed as strings
        if context_messages and isinstance(context_messages[0], dict) and 'content' in context_messages[0]:
            context = " ".join([msg['content'] for msg in context_messages])
        elif context_messages and (isinstance(context_messages[0], AIMessage) or isinstance(context_messages[0], HumanMessage)):
            # If the messages are AIMessage or HumanMessage instances, extract the 'content' attribute
            context = " ".join([msg.content for msg in context_messages])
        else:
            # Fallback to handling context_messages as a list of strings
            context = " ".join(context_messages)

        prompt = f"{context}\n{user_query}\nWhat would be the best response?"
        return prompt
    
    
    def update_feedback_based_on_result(self, result: dict, feedback: Any) -> None:
        """
        Update the internal state or metrics of the prompt engine based on the result and user feedback.

        :param result: The result from the chat model invocation.
        :param feedback: Feedback received related to the result.
        """
        # Example implementation - this should be expanded based on actual feedback handling logic
        if feedback is not None:
            # Update internal metrics or states based on feedback
            # This is a placeholder logic; actual implementation will depend on feedback structure
            logging.info("Feedback received and processed")
        else:
            logging.info("No feedback received")

    def update_feedback(self, tool_key: str, feedback: int):
        """
        Update the feedback score for a given tool.
        """
        if tool_key not in self.user_feedback:
            self.user_feedback[tool_key] = 0
        self.user_feedback[tool_key] += feedback

    def select_tool(self, query: str):
        """
        Selects the most appropriate tool based on the query.
        """
        doc = self.nlp(query.lower())
        keywords = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]

        tool_mapping = {
            # Example: 'translate': ['translation_tool', 'language_tool']
        }

        keyword_counts = Counter(keywords)
        most_common_keywords = keyword_counts.most_common()
        
        for keyword, _ in most_common_keywords:
            if keyword in tool_mapping:
                possible_tools = tool_mapping[keyword]
                best_tool = max(possible_tools, key=lambda tool: self.user_feedback.get(tool, 0))
                return best_tool

        return 'general_query_handler'

    def classify_input(self, user_query: str) -> str:
        """
        Classifies the user's input into categories such as 'greeting', 'query', etc.
        """
        greetings = ["hi", "hello", "hey", "heyhey"]
        if any(greeting in user_query.lower() for greeting in greetings):
            return "greeting"
        if "how are you" in user_query.lower():
            return "smalltalk"
        return "query"

    def fetch_data(self, query: str, tool_key: str):
        """
        Fetches data based on the query context using the specified tool.
        """
        tool = self.tools.get(tool_key)
        if tool:
            return tool(query)
        return "No data available for this query."

    def generate_dynamic_prompt(self, user_query: str, context_messages: list, prompt_template: str = None) -> str:
        """
        Generates a dynamic prompt with additional context and data.
        """
        try:
            input_type = self.classify_input(user_query)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tool_key = self.select_tool(user_query)
            data = self.fetch_data(user_query, tool_key) if tool_key else ""

            prompt_context, prompt_data, prompt_query = "", "", ""
            if input_type == "greeting":
                prompt = f"Hello! How can I assist you today? It's currently {now}."
            else:
                estimated_query_tokens = len(user_query.split()) + (len(data.split()) if data else 0)
                max_context_tokens = self.max_tokens - estimated_query_tokens - 100

                message_contents = [msg['content'] for msg in context_messages if 'content' in msg][-self.context_length:]
                full_context = " ".join(message_contents)
                context_tokens = full_context.split()
                truncated_context = " ".join(context_tokens[-max_context_tokens:]) if len(context_tokens) > max_context_tokens else full_context

                prompt_context = f"Time: {now}\nContext: {truncated_context}"
                prompt_data = f"\nData: {data}" if data else "\nData: No specific data found for this query."
                prompt_query = f"\nUser Query: {user_query}"
                prompt_instruction = "\nProvide a detailed, accurate answer based on the above query and context."

                if prompt_template:
                    prompt = prompt_template.format(now=now, context=truncated_context, data=prompt_data, user_query=prompt_query, instruction=prompt_instruction)
                else:
                    prompt = f"{prompt_context}{prompt_data}{prompt_query}{prompt_instruction}"

            logging.info(f"Generated prompt: {prompt}")
            return prompt
        except Exception as e:
            logging.error(f"Error generating dynamic prompt: {e}")
            return "Error generating prompt."
