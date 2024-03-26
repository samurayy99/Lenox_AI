import praw
from collections import Counter
from textblob import TextBlob
from langchain.agents import tool  # Use the @tool decorator
import os
from typing import Any, Dict, List, Union

from dotenv import load_dotenv
load_dotenv()

# Laden der Reddit API-Anmeldeinformationen aus Umgebungsvariablen
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

@tool
def get_reddit_data(subreddit: str, category: str = 'hot') -> str:
    """
    Fetches and returns the latest posts from a specified subreddit category using PRAW.
    """
    sub = reddit.subreddit(subreddit)
    posts = getattr(sub, category)(limit=5)
    posts_str = "\n\n".join([f"Title: {post.title}\nURL: {post.url}" for post in posts])
    return f"Latest posts from r/{subreddit}:\n{posts_str}"

@tool
def count_mentions(subreddit: str, keyword: str, time_filter='week') -> str:
    """
    Zählt, wie oft ein Keyword in einem Subreddit innerhalb des spezifizierten Zeitraums erwähnt wird.
    """
    mentions = sum(1 for _ in reddit.subreddit(subreddit).search(keyword, time_filter=time_filter))
    return f"'{keyword}' was mentioned {mentions} times in r/{subreddit} over the past {time_filter}."

@tool
def analyze_sentiment(subreddit: str, keyword: str, time_filter='week') -> str:
    """
    Führt eine Sentiment-Analyse für Beiträge und Kommentare durch, die ein bestimmtes Keyword enthalten.
    """
    sentiment_scores = []
    for submission in reddit.subreddit(subreddit).search(keyword, time_filter=time_filter):
        analysis = TextBlob(submission.title)
        sentiment_scores.append(analysis.sentiment.polarity)
        for comment in submission.comments.list():
            if isinstance(comment, praw.models.MoreComments):
                continue
            analysis = TextBlob(comment.body)
            sentiment_scores.append(analysis.sentiment.polarity)
    average_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    return f"Average sentiment for '{keyword}' in r/{subreddit} over the past {time_filter}: {average_sentiment:.2f}"

@tool
def find_trending_topics(subreddits: list, time_filter='day') -> str:
    """
    Identifiziert Trending Topics in den gegebenen Subreddits innerhalb des spezifizierten Zeitraums.
    """
    topics = Counter()
    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit).hot(limit=100):
            for topic in submission.title.split():
                topics[topic] += 1
    most_common_topics = topics.most_common(10)
    topics_str = "\n".join([f"{topic[0]}: {topic[1]} mentions" for topic in most_common_topics])
    return f"Trending topics:\n{topics_str}"



def get_sentiment_vader(text): 
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)
    return score['compound'] 

def clean_reddit_text(docs: List[str]) -> List[str]:
    """Cleans and prepares Reddit text for sentiment analysis"""
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    translator = str.maketrans('', '', string.punctuation)

    clean_docs = []
    docs = [doc.lower().strip() for doc in docs]

    for doc in docs:
        tokens = doc.split()
        clean_tok = [lemmatizer.lemmatize(token) for token in tokens]
        clean_tok = [token for token in clean_tok if token not in stop_words]
        clean_tok = [token.translate(translator) for token in clean_tok] 
        filtered_tokens = [t for t in clean_tok if t]  
        clean_docs.append(" ".join(filtered_tokens))
    return clean_docs