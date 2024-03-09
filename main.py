from flask import Flask, render_template, request, jsonify
import os
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import json
import plotly
import plotly.graph_objs as go
from utils import Lenox

# Import the tools you use in your project
from messari_tools import get_asset_data, get_news_feed, get_research_reports
from lunarcrush_tools import get_lunarcrush_galaxy_score, analyze_crypto_sentiment, get_influential_crypto_assets
from reddit_tools import get_reddit_data, count_mentions, analyze_sentiment, find_trending_topics
from coingecko_tools import get_coingecko_market_data, get_liquidity_score, get_macd
from cryptocompare_tools import get_crypto_data, get_historical_crypto_price

app = Flask(__name__)
CORS(app)
load_dotenv()

# Database initialization with Flask-Migrate

# Initialize Lenox with a broader range of tools
lenox = Lenox([
    get_crypto_data, get_reddit_data, get_coingecko_market_data,
    get_liquidity_score, get_macd, get_historical_crypto_price,
    get_lunarcrush_galaxy_score, analyze_sentiment, find_trending_topics,
    get_influential_crypto_assets, analyze_crypto_sentiment,
    get_asset_data, get_news_feed, get_research_reports
])

# Configure structured logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app.logger.info('Flask application has started')

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

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True')