from prompts import PromptEngine

# Create an instance of PromptEngine
prompt_engine = PromptEngine()

# Define a user query
user_query = "What is the impact of climate change on polar bears?"

# Simulate some context messages (assuming each message has a 'content' attribute or key)
context_messages = [
    {'content': "Polar bears rely on sea ice to hunt."},
    {'content': "Climate change is causing the Arctic to warm twice as fast as the global average."},
    {'content': "Reduction in sea ice has been observed over the past decades."},
    {'content': "Polar bears are experiencing difficulty finding food."},
    {'content': "Conservation efforts are being made to protect polar bear habitats."}
]

# Specify the query type
query_type = "general"

# Generate the dynamic prompt
dynamic_prompt = prompt_engine.generate_dynamic_prompt(user_query, context_messages, query_type)

# Print the generated prompt
print(dynamic_prompt)