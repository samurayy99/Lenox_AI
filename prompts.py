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
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Dynamically adjust context length based on the length of the user query
            estimated_query_tokens = len(user_query.split())
            max_context_tokens = self.max_tokens - estimated_query_tokens - 100  # Reserve tokens for template text

            # Safely extract the 'content' from each message dictionary
            message_contents = [msg['content'] for msg in context_messages if 'content' in msg]
            
            # Concatenate context messages and truncate if necessary
            full_context = " ".join(message_contents[-self.context_length:])  # Use message_contents here
            context_tokens = full_context.split()
            if len(context_tokens) > max_context_tokens:
                truncated_context = " ".join(context_tokens[-max_context_tokens:])
            else:
                truncated_context = full_context

            # Construct the prompt
            prompt = prompt_template if prompt_template else f"Time: {now}\nContext: {truncated_context}\nUser Query: {user_query}\n"
            prompt += "Provide a detailed, accurate answer based on the above query and context.\n"
            prompt = prompt.format(now=now, context=truncated_context, user_query=user_query)

            logging.info(f"Generated prompt: {prompt}")
            return prompt
        except Exception as e:
            logging.error(f"Error generating dynamic prompt: {e}")
            return "Error generating prompt. Please check the input data."
