import re
# Enhance preprocessing in query_preprocessor.py
def preprocess_query(query: str) -> str:
    query = query.lower().strip()
    query = re.sub(r'\s+', ' ', query)
    query = re.sub(r'[^\w\s]', '', query)
    query = re.sub(r'\b(?:a|an|the|is|it|on|in|at|to|of)\b', '', query)  # Remove common stopwords
    return query
