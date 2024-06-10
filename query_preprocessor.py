# query_preprocessor.py
import re

def preprocess_query(query: str) -> str:
    query = query.lower().strip()
    query = re.sub(r'\s+', ' ', query)  # Replace multiple spaces with a single space
    query = re.sub(r'[^\w\s]', '', query)  # Remove non-alphanumeric characters
    return query
