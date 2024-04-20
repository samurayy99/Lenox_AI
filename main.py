from flask import Flask, render_template, request, jsonify, session, send_file, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler  # Ensure this is correctly imported
from dotenv import load_dotenv
from documents import DocumentHandler
from utils import Lenox
from prompts import PromptEngine
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from tool_imports import import_tools
from datetime import datetime
import numpy as np
import openai



# Load environment variables
load_dotenv()
app = Flask(__name__)
openai_api_key = os.getenv('OPENAI_API_KEY')
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_secret_key')
socketio = SocketIO(app)

# Configure structured logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

# Import tools before they are used
tools = import_tools()



# Create instances of your components
document_handler = DocumentHandler(document_folder="documents", data_folder="data")
prompt_engine = PromptEngine(context_length=5, max_tokens=2048, tools=tools, model_name="gpt-3.5-turbo-0125")
duckduckgo_search = DuckDuckGoSearchResults()

# Initialize Lenox with all necessary components using keyword arguments
lenox = Lenox(tools=tools, document_handler=document_handler, prompt_engine=prompt_engine, duckduckgo_search=duckduckgo_search, openai_api_key=openai_api_key)




@app.before_request
def log_request():
    app.logger.debug(f'Incoming request: {request.method} {request.path}')
    session.setdefault('session_id', os.urandom(24).hex())

@app.after_request
def log_response(response):
    app.logger.debug(f'Outgoing response: {response.status}')
    return response

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('path_to_audio_files_directory', filename)



@app.route('/synthesize', methods=['POST'])
def synthesize_speech():
    data = request.get_json()
    input_text = data.get('input')
    voice = data.get('voice', 'onyx')  # Default to 'alloy' if not specified
    model = data.get('model', 'tts-1-hd')  # Default to 'tts-1' if not specified

    if not input_text:
        return jsonify({'error': 'Input text is missing'}), 400

    try:
        audio_path = lenox.synthesize_text(model, input_text, voice)
        if audio_path:
            directory = os.path.dirname(audio_path)
            filename = os.path.basename(audio_path)
            return send_from_directory(directory=directory, path=filename, as_attachment=True)
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500





@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        query = data.get('query', '').lower()  # Normalize the input to lower case

        if not query:
            app.logger.debug("No query provided in the request.")
            return jsonify({'error': 'Empty query.'}), 400

        # Process the query through Lenox's convchain
        result = lenox.convchain(query, session['session_id'])
        app.logger.debug(f"Processed query with convchain, result: {result}")
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Failed to process request.'}), 500



@app.route('/feedback', methods=['POST'])
def handle_feedback():
    feedback_data = request.get_json()
    if 'feedback' not in feedback_data:
        return jsonify({'error': 'Missing feedback data.'}), 400

    session_id = session.get('session_id')  # Ensure session_id is correctly retrieved
    lenox.process_feedback(feedback_data['feedback'], session_id)
    return jsonify({'message': 'Thank you for your feedback!'})



@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'Empty query.'}), 400
    search_results = duckduckgo_search.run(query)
    app.logger.debug(f"Search results: {search_results}")
    return jsonify({'type': 'search_results', 'results': search_results})



@app.route('/create_visualization', methods=['POST'])
def create_visualization():
    data = request.get_json()
    return jsonify(lenox.create_visualization(data['x'], data['y']))

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(lenox.get_sample_data())

@app.route('/upload', methods=['POST'])
def upload_document():
    file = request.files.get('file')
    if file and file.filename:
        success, message = document_handler.save_document(file)
        return jsonify({'message': message}) if success else jsonify({'error': message}), 400
    return jsonify({'error': 'No file provided'}), 400

@socketio.on('connect')
def on_connect():
    emit('status', {'data': 'Connected to real-time updates'})

@socketio.on('send_feedback')
def on_feedback(data):
    response = lenox.process_feedback(data['feedback'], session['session_id'])
    emit('feedback_response', {'message': 'Feedback processed', 'data': response})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=bool(os.getenv('FLASK_DEBUG')))
