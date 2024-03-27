from flask import Flask, render_template, request, jsonify
import os
from flask_cors import CORS
from dotenv import load_dotenv
import logging
import plotly.graph_objs
from logging.handlers import RotatingFileHandler
from documents import DocumentHandler, allowed_file
from utils import Lenox



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



# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure structured logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.logger.info('Flask application started')

# Initialize DocumentHandler with correct paths
document_handler = DocumentHandler(document_folder="documents", data_folder="data")


# Initialize Lenox with a broader range of tools and the DocumentHandler
lenox = Lenox(
    tools=[
        get_historical_daily_stats, get_top_trading_pairs, get_news,
        get_coingecko_market_data, get_liquidity_score, get_macd,
        get_lunarcrush_galaxy_score, analyze_crypto_sentiment, get_influential_crypto_assets,
        get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics,
        get_asset_data, get_news_feed, get_research_reports,
        search_with_searchapi, search_youtube, process_youtube_video, query_youtube_video,
        get_whale_insights, get_recent_blocks, get_block_transactions,
        get_global_market_overview, get_coin_social_media_and_dev_activity, get_exchange_info,
        
    ],
    document_handler=document_handler  # Pass the document handler as a named argument
)

@app.before_request
def before_request_logging():
    app.logger.debug(f'Incoming request: {request.method} {request.path}')

@app.after_request
def after_request_logging(response):
    app.logger.debug(f'Outgoing response: {response.status}')
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    query = data.get('query', '')
    session_id = data.get('session_id', 'default_session')  # You might want to handle session ID more dynamically
    if not query:
        return jsonify({'error': 'Empty query.'}), 400
    response = lenox.convchain(query, session_id)
    return jsonify(response)


@app.route('/create_visualization', methods=['POST'])
def create_visualization():
    data = request.get_json()
    x_data = data['x']
    y_data = data['y']
    graphJSON = lenox.create_visualization(x_data, y_data)
    return jsonify(graphJSON)

@app.errorhandler(500)
def handle_error(error):
    app.logger.error(f'Internal Server Error: {error}')
    return jsonify({'error': 'An internal server error has occurred.'}), 500

@app.errorhandler(404)
def handle_404_error(error):
    app.logger.error(f'404 Not Found: {error}')
    return jsonify({'error': 'Resource not found.'}), 404

@app.route('/data', methods=['GET'])
def get_data():
    data = lenox.get_sample_data()
    return jsonify(data)


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



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=os.getenv('FLASK_DEBUG', 'False') == 'True')
