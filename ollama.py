import logging
from langchain_community.llms import Ollama

class OllamaService:
    def __init__(self, model_name):
        self.model = Ollama(model=model_name)

    def invoke_model(self, query):
        try:
            response = self.model.invoke(query)
            logging.debug(f"Ollama raw output: {response}")
            return response
        except Exception as e:
            logging.error(f"Error invoking Ollama model: {e}")
            return None

# You can instantiate and use this service in other parts of your application