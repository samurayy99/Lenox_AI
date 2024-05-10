from textblob import TextBlob
import pandas as pd

def analyze_social_sentiment(posts_df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
    """Analyze sentiment across social media posts using TextBlob."""
    def get_sentiment(text):
        blob = TextBlob(text)
        return blob.sentiment.polarity, blob.sentiment.subjectivity
    posts_df['Polarity'], posts_df['Subjectivity'] = zip(*posts_df[text_column].apply(get_sentiment))
    posts_df['Sentiment'] = posts_df['Polarity'].apply(lambda x: 'Positive' if x > 0 else ('Negative' if x < 0 else 'Neutral'))
    return posts_df
