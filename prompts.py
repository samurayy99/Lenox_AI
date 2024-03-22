from datetime import datetime
import logging

class PromptEngine:
    """
    A refined prompt engine for Lenox, designed to leverage the capabilities of
    the ChatGPT-3.5-turbo model for generating responses across various domains.
    This version introduces more flexibility and customization options, including dynamic context trimming to manage token limits.
    """

    def __init__(self, context_length: int = 10, max_tokens: int = 4096):
        """
        Initializes the PromptEngine with customizable options.

        :param context_length: Number of context messages to include in the prompt.
        :param max_tokens: Maximum number of tokens allowed in the prompt.
        """
        self.context_length = context_length
        self.max_tokens = max_tokens

    def generate_dynamic_prompt(self, user_query: str, context_messages: list, prompt_template: str = None) -> str:
        """
        Generates a dynamic prompt based on the user query, context messages, and an optional template, while managing token limits.

        :param user_query: The user's query.
        :param context_messages: A list of context messages.
        :param prompt_template: An optional template for generating the prompt.
        :return: A dynamically generated prompt.
        """
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            context = " ".join(context_messages[-self.context_length:])  # Initial context based on context_length

            # Initial prompt template
            prompt = prompt_template if prompt_template else f"Time: {now}\nContext: {context}\nUser Query: {user_query}\n"
            prompt += "Provide a detailed, accurate answer based on the above query and context.\n"

            # Replace placeholders with actual values
            prompt = prompt.format(now=now, context=context, user_query=user_query)

            # Check if the generated prompt exceeds the max_tokens limit
            if len(prompt.split()) > self.max_tokens:
                # If it does, reduce the context until the prompt is within the token limit
                while len(prompt.split()) > self.max_tokens and self.context_length > 0:
                    self.context_length -= 1  # Reduce context length
                    context = " ".join(context_messages[-self.context_length:])  # Regenerate context
                    prompt = prompt_template if prompt_template else f"Time: {now}\nContext: {context}\nUser Query: {user_query}\n"
                    prompt += "Provide a detailed, accurate answer based on the above query and context.\n"
                    prompt = prompt.format(now=now, context=context, user_query=user_query)  # Reapply formatting

            logging.info(f"Generated prompt: {prompt}")
            return prompt
        except Exception as e:
            logging.error(f"Error generating dynamic prompt: {e}")
            return "Error generating prompt. Please check the input data."
