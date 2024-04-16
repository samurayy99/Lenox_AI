# Import the tools you will use in your project
from messari_tools import get_asset_data, get_news_feed, get_research_reports, get_asset_profile, get_latest_news, get_historical_data, get_on_chain_stats, get_market_data_over_time 
from lunarcrush_tools import get_lunarcrush_galaxy_score, analyze_crypto_sentiment, get_influential_crypto_assets, get_latest_social_feeds
from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics
from cryptocompare_tools import get_current_price, get_historical_daily, get_top_volume_symbols
from coingecko_tools import get_coingecko_market_data, get_macd, get_trending_coins, get_public_companies_holdings
from youtube_tools import search_youtube, process_youtube_video, query_youtube_video
from etherscan_tools import get_whale_insights, get_recent_blocks, get_block_transactions
from coinpaprika_tools import get_coin_details, get_tags, search_coinpaprika  
from tavily_tools import tavily_search

def import_tools():
    return [
        get_current_price, get_historical_daily, get_top_volume_symbols,
        get_coingecko_market_data, get_macd, get_trending_coins, get_public_companies_holdings,
        get_lunarcrush_galaxy_score, analyze_crypto_sentiment, get_influential_crypto_assets, get_latest_social_feeds,  # From lunarcrush_tools
        get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics,  # From reddit_tools
        get_asset_data, get_news_feed, get_research_reports, get_latest_news, get_asset_profile, get_historical_data, get_on_chain_stats, get_market_data_over_time,  # From messari_tools
        search_youtube, process_youtube_video, query_youtube_video,  # From youtube_tools
        get_whale_insights, get_recent_blocks, get_block_transactions,  # From etherscan_tools
        get_coin_details, get_tags, search_coinpaprika,
        tavily_search
    ]
