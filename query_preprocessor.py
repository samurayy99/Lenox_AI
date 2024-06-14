import re

class QueryPreprocessor:
    def preprocess(self, query: str) -> str:
        """
        Preprocess the input query by normalizing case, removing extra spaces,
        punctuation, and stopwords.
        """
        query = query.strip().lower()
        query = re.sub(r'\s+', ' ', query)  # Replace multiple spaces with a single space
        query = re.sub(r'[^\w\s]', '', query)  # Remove punctuation
        return self.remove_stopwords(query)

    def remove_stopwords(self, query: str) -> str:
        """
        Remove common stopwords from the query.
        """
        stopwords = {'the', 'is', 'in', 'and', 'to', 'of'}
        query_words = query.split()
        filtered_words = [word for word in query_words if word not in stopwords]
        return ' '.join(filtered_words)