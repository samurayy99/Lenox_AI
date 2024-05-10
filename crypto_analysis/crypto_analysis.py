from .market_structure import analyze_market_structure
from .sentiment_analysis import analyze_social_sentiment
from .correlation_analysis import calculate_and_plot_correlations

class CryptoAnalysis:
    def __init__(self):
        """Initialize the CryptoAnalysis class."""
        pass

    def market_structure(self, data, **kwargs):
        return analyze_market_structure(data, **kwargs)

    def sentiment(self, social_data):
        return analyze_social_sentiment(social_data)

    def correlation(self, prices_df):
        return calculate_and_plot_correlations(prices_df)
