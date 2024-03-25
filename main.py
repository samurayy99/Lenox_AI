from flask import Flask, render_template, request, jsonify
import os
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from documents import DocumentHandler, allowed_file
from utils import Lenox
from slack_service import SlackService
from langchain_community.agent_toolkits import SlackToolkit
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI



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

# Initialize the LLM and agent
llm = ChatOpenAI(temperature=0, model="gpt-4")
prompt = hub.pull("hwchase17/openai-tools-agent")
agent = create_openai_tools_agent(
    tools=toolkit.get_tools(),
    llm=llm,
    prompt=prompt,
)
agent_executor = AgentExecutor(agent=agent, tools=toolkit.get_tools(), verbose=True)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
slack_service = SlackService()
toolkit = SlackToolkit()

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    query = data.get('query', '')
    session_id = data.get('session_id', os.urandom(16).hex())
    channel_id = data.get('channel_id', None)  # Extract channel_id from the request data, default to None if not provided

    if not query:
        return jsonify({'error': 'Empty request.'}), 400

    # Pass channel_id to the convchain method
    response = lenox.convchain(query, session_id, channel_id)
    return jsonify(response)


@app.route('/slack_interaction', methods=['POST'])
def slack_interaction():
    data = request.get_json()
    input_text = data.get("input")
    response = agent_executor.invoke({"input": input_text})
    return jsonify(response)


@app.route('/fetch_slack_messages', methods=['POST'])
def fetch_slack_messages():
    data = request.get_json()
    channel_id = data.get('channel_id')
    latest = data.get('latest', None)
    oldest = data.get('oldest', None)
    limit = data.get('limit', 100)  # Default to 100 messages if not specified

    messages = slack_service.fetch_channel_messages(channel_id, latest, oldest, limit)
    return jsonify({"success": True, "messages": messages})



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
    # Ensure FLASK_DEBUG environment variable is set to 'False' in production.
    app.run(host='0.0.0.0', debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')

