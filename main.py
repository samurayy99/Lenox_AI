from flask import Flask, render_template, request, jsonify
import os
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from documents import DocumentHandler, allowed_file
from utils import Lenox
from langchain.tools import Tool

# Import the tools you will use in your project
from messari_tools import get_asset_data, get_news_feed, get_research_reports
from lunarcrush_tools import get_lunarcrush_galaxy_score, analyze_crypto_sentiment, get_influential_crypto_assets
from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics
from cryptocompare_tools import get_historical_daily_stats, get_top_trading_pairs, get_news
from coingecko_tools import get_coingecko_market_data, get_liquidity_score, get_macd
from websearch_tools import search_with_searchapi
from youtube_tools import search_youtube, process_youtube_video, query_youtube_video
from etherscan_tools import get_whale_insights, get_recent_blocks, get_block_transactions
from coinpaprika_tools import get_global_market_overview, get_coin_social_media_and_dev_activity, get_exchange_info


app = Flask(__name__)
CORS(app)
load_dotenv()

# Configure structured logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.logger.info('Flask application started')

# Initialize DocumentHandler
document_handler = DocumentHandler(document_folder="documents", data_folder="data")


# Wrap your tool functions in the Tool class with descriptions
tools = [
    Tool(name="Get Historical Daily Stats", func=get_historical_daily_stats, description="Gets historical daily statistics."),
    Tool(name="Get Top Trading Pairs", func=get_top_trading_pairs, description="Gets top trading pairs."),
    Tool(name="Get News", func=get_news, description="Gets the latest news."),
    Tool(name="Get CoinGecko Market Data", func=get_coingecko_market_data, description="Gets market data from CoinGecko."),
    Tool(name="Get Liquidity Score", func=get_liquidity_score, description="Gets liquidity score."),
    Tool(name="Get MACD", func=get_macd, description="Gets Moving Average Convergence Divergence."),
    Tool(name="Get LunarCrush Galaxy Score", func=get_lunarcrush_galaxy_score, description="Gets LunarCrush Galaxy Score."),
    Tool(name="Analyze Crypto Sentiment", func=analyze_crypto_sentiment, description="Analyzes cryptocurrency sentiment."),
    Tool(name="Get Influential Crypto Assets", func=get_influential_crypto_assets, description="Gets influential cryptocurrency assets."),
    Tool(name="Get Reddit Data", func=get_reddit_data, description="Gets data from Reddit."),
    Tool(name="Count Mentions", func=count_mentions, description="Counts mentions."),
    Tool(name="Analyze Sentiment", func=analyze_sentiment, description="Analyzes sentiment."),
    Tool(name="Find Trending Topics", func=find_trending_topics, description="Finds trending topics."),
    Tool(name="Get Asset Data", func=get_asset_data, description="Gets asset data."),
    Tool(name="Get News Feed", func=get_news_feed, description="Gets news feed."),
    Tool(name="Get Research Reports", func=get_research_reports, description="Gets research reports."),
    Tool(name="Search with SearchAPI", func=search_with_searchapi, description="Performs searches with SearchAPI."),
    Tool(name="Search YouTube", func=search_youtube, description="Searches YouTube."),
    Tool(name="Process YouTube Video", func=process_youtube_video, description="Processes YouTube video."),
    Tool(name="Query YouTube Video", func=query_youtube_video, description="Queries YouTube video."),
    Tool(name="Get Whale Insights", func=get_whale_insights, description="Gets whale insights."),
    Tool(name="Get Recent Blocks", func=get_recent_blocks, description="Gets recent blocks."),
    Tool(name="Get Block Transactions", func=get_block_transactions, description="Gets block transactions."),
    Tool(name="Get Global Market Overview", func=get_global_market_overview, description="Gets global market overview."),
    Tool(name="Get Coin Social Media and Dev Activity", func=get_coin_social_media_and_dev_activity, description="Gets coin social media and development activity."),
    Tool(name="Get Exchange Info", func=get_exchange_info, description="Gets exchange information."),
]

# Right before initializing Lenox
for tool in tools:
    print(f"Is {tool.name} a Tool instance? {isinstance(tool, Tool)}")



# Initialize Lenox with the wrapped tools and DocumentHandler
lenox = Lenox(tools=tools, document_handler=document_handler)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    query = data.get('query', '')
    session_id = data.get('session_id', 'default_session')  # Sie möchten die Session-ID möglicherweise dynamischer handhaben
    if not query:
        return jsonify({'error': 'Leere Anfrage.'}), 400
    response = lenox.convchain(query, session_id)
    return jsonify(response)

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'Kein Dateiteil'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Keine ausgewählte Datei'}), 400

    if file and allowed_file(file.filename):
        success, message = document_handler.save_document(file)
        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400

@app.errorhandler(500)
def handle_error(error):
    app.logger.error(f'Interner Serverfehler: {error}')
    return jsonify({'error': 'Ein interner Serverfehler ist aufgetreten.'}), 500

@app.errorhandler(404)
def handle_404_error(error):
    app.logger.error(f'404 Nicht gefunden: {error}')
    return jsonify({'error': 'Ressource nicht gefunden.'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=os.getenv('FLASK_DEBUG', 'False') == 'True')
