import re

def preprocess_query(query: str) -> str:
    query = query.lower().strip()
    query = re.sub(r'\s+', ' ', query)
    query = re.sub(r'[^\w\s]', '', query)
    return query
