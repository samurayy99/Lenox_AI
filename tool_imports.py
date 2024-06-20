from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics
from cryptocompare_tools import get_current_price, get_historical_daily, get_top_volume_symbols
from coingecko_tools import (
    get_market_data, get_historical_market_data, get_ohlc,
    get_trending_cryptos, calculate_macd, get_exchange_rates, calculate_rsi
)
from youtube_tools import search_youtube, process_youtube_video, query_youtube_video
from coinpaprika_tools import get_coin_details, get_coin_tags
from cryptopanic_tools import get_latest_news, get_news_sources, get_last_news_title
from coinmarketcap_tools import get_latest_listings, get_crypto_metadata, get_global_metrics
from fearandgreed_tools import get_fear_and_greed_index
from whale_alert_tools import get_whale_alert_status, get_transaction_by_hash, get_recent_transactions
from binance_tools import get_binance_ticker, get_binance_order_book, get_binance_recent_trades

def import_tools():
    """
    Collects and returns a list of functions for various external data retrieval and processing tasks.
    Each tool function is designed to be compatible with LangChain's convert_to_openai_function, which expects
    callable objects.
    """
    tools = [
        # CryptoCompare Tools
        get_current_price,
        get_historical_daily,
        get_top_volume_symbols,
        
        # CoinGecko Tools
        get_market_data,
        get_historical_market_data,
        get_ohlc,
        get_trending_cryptos,
        calculate_macd,
        get_exchange_rates,
        calculate_rsi,

        # Reddit Tools
        get_reddit_data,
        count_mentions,
        analyze_sentiment,
        find_trending_topics,

        # YouTube Tools
        search_youtube,
        process_youtube_video,
        query_youtube_video,

        # CoinPaprika Tools
        get_coin_details,
        get_coin_tags,

        # CryptoPanic Tools
        get_latest_news,
        get_news_sources,
        get_last_news_title,

        # CoinMarketCap Tools
        get_latest_listings,
        get_crypto_metadata,
        get_global_metrics,

        # Fear and Greed Index Tools
        get_fear_and_greed_index,

        # Whale Alert Tools
        get_whale_alert_status,
        get_transaction_by_hash,
        get_recent_transactions,

        # Binance Tools
        get_binance_ticker,
        get_binance_order_book,
        get_binance_recent_trades,
    ]

    return tools
