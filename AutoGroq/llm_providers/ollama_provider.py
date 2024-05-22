
import json
import requests
from llm_providers.base_provider import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    def __init__(self, api_url):
        self.api_url = api_url


    def send_request(self, data):
        headers = {
            "Content-Type": "application/json",
        }
        # Construct the request data in the format expected by the Ollama API
        ollama_request_data = {
            "model": data["model"],
            "prompt": data["messages"][0]["content"],
            "temperature": data.get("temperature", 0.1),
            "max_tokens": data.get("max_tokens", 2048),
            "stop": data.get("stop", "TERMINATE"),
            "stream": False,
        }
        # Ensure data is a JSON string
        if isinstance(ollama_request_data, dict):
            json_data = json.dumps(ollama_request_data)
        else:
            json_data = ollama_request_data
        response = requests.post(self.api_url, data=json_data, headers=headers)
        return response


    def process_response(self, response):
        if response.status_code == 200:
            response_data = response.json()
            if "response" in response_data:
                content = response_data["response"].strip()
                if content:
                    return {
                        "choices": [
                            {
                                "message": {
                                    "content": content
                                }
                            }
                        ]
                    }
                else:
                    raise Exception("Empty response received from the Ollama API.")
            else:
                raise Exception("Unexpected response format. 'response' field missing.")
        else:
            raise Exception(f"Request failed with status code {response.status_code}")