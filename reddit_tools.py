import praw
from collections import Counter
from textblob import TextBlob
from langchain.agents import tool  # Use the @tool decorator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
from typing import List, Union
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string

from dotenv import load_dotenv
load_dotenv()

# Initialize Reddit API with credentials from environment variables
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
    Counts how often a keyword is mentioned in a subreddit within the specified time period.
    """
    mentions = sum(1 for _ in reddit.subreddit(subreddit).search(keyword, time_filter=time_filter))
    return f"'{keyword}' was mentioned {mentions} times in r/{subreddit} over the past {time_filter}."

@tool
def analyze_sentiment(subreddit: str, keyword: str, time_filter='week') -> str:
    """
    Conducts a sentiment analysis for posts and comments containing a specific keyword, providing both the average score and a qualitative interpretation.
    """
    sentiment_analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = []
    for submission in reddit.subreddit(subreddit).search(keyword, time_filter=time_filter):
        # Using TextBlob
        analysis_tb = TextBlob(submission.title)
        sentiment_scores.append(analysis_tb.sentiment.polarity)
        
        # Using VADER
        analysis_vader = sentiment_analyzer.polarity_scores(submission.title)
        sentiment_scores.append(analysis_vader['compound'])
        
        for comment in submission.comments.list():
            if isinstance(comment, praw.models.MoreComments):
                continue
            analysis_tb = TextBlob(comment.body)
            sentiment_scores.append(analysis_tb.sentiment.polarity)
            
            analysis_vader = sentiment_analyzer.polarity_scores(comment.body)
            sentiment_scores.append(analysis_vader['compound'])

    if sentiment_scores:
        average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        sentiment_description = interpret_sentiment(average_sentiment)
    else:
        average_sentiment = 0
        sentiment_description = "No sentiment data available."

    return f"Average sentiment for '{keyword}' in r/{subreddit} over the past {time_filter}: {average_sentiment:.2f} ({sentiment_description})"

def interpret_sentiment(score: float) -> str:
    """
    Provides a qualitative interpretation of a sentiment score.
    """
    if score > 0.05:
        return "mostly positive"
    elif score < -0.05:
        return "mostly negative"
    else:
        return "neutral"


@tool
def find_trending_topics(subreddits: List[str], time_filter='day') -> str:
    """
    Identifies trending topics in the given subreddits within the specified time period.
    """
    topics = Counter()
    stopwords_set = set(stopwords.words('english'))  # Ensure stopwords are being used to filter
    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit).hot(limit=100):
            words = [word for word in submission.title.split() if word.lower() not in stopwords_set]
            topics.update(words)
    most_common_topics = topics.most_common(10)
    topics_str = "\n".join([f"{topic[0]}: {topic[1]} mentions" for topic in most_common_topics])
    return f"Trending topics:\n{topics_str}"


def clean_reddit_text(docs: List[str]) -> List[str]:
    """
    Cleans and prepares Reddit text for sentiment analysis.
    """
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    translator = str.maketrans('', '', string.punctuation)

    clean_docs = []
    for doc in docs:
        tokens = doc.split()
        clean_tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words and token.isalpha()]
        clean_doc = ' '.join(clean_tokens).translate(translator)
        clean_docs.append(clean_doc)
    return clean_docs
