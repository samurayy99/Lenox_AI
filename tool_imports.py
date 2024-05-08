from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics
from cryptocompare_tools import get_current_price, get_historical_daily, get_top_volume_symbols
from coingecko_tools import (
    get_market_data, get_historical_market_data, get_ohlc,
    get_trending_cryptos, calculate_macd, get_exchange_rates, calculate_rsi
)
from youtube_tools import search_youtube, process_youtube_video, query_youtube_video
from coinpaprika_tools import get_coin_details, get_coin_tags

def import_tools():
    """
    Collects and returns a list of functions for various external data retrieval and processing tasks.
    Each tool function is designed to be compatible with LangChain's convert_to_openai_function, which expects
    callable objects.
    """
    return [
        # CryptoCompare Tools
        get_current_price,        # Fetch current price for cryptocurrencies
        get_historical_daily,     # Retrieve historical daily data for price analysis
        get_top_volume_symbols,   # Identify top trading volume symbols in crypto market
        
        # CoinGecko Tools
        get_market_data,          # Get general market data for various cryptocurrencies
        get_historical_market_data,  # Fetch historical market data for trend analysis
        get_ohlc,                 # Obtain open-high-low-close data for specific coins
        get_trending_cryptos,     # Find trending cryptocurrencies
        calculate_macd,           # Calculate Moving Average Convergence Divergence
        get_exchange_rates,       # Retrieve current exchange rates for cryptocurrencies
        calculate_rsi,            # Calculate Relative Strength Index for market analysis

        # Reddit Tools
        get_reddit_data,          # Fetch data from Reddit
        count_mentions,           # Count how often terms are mentioned on Reddit
        analyze_sentiment,        # Analyze the sentiment of Reddit posts
        find_trending_topics,     # Identify trending topics on Reddit

        # YouTube Tools
        search_youtube,           # Search for videos on YouTube
        process_youtube_video,    # Process specific YouTube videos for content extraction
        query_youtube_video,      # Run specific queries against YouTube videos

        # CoinPaprika Tools
        get_coin_details,         # Retrieve details about specific coins from CoinPaprika
        get_coin_tags             # Fetch tags associated with coins for better categorization
    ]
