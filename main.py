import subprocess
from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import datetime
from documents import DocumentHandler, allowed_file
from utils import Lenox
from prompts import PromptEngine, PromptEngineConfig
from werkzeug.utils import secure_filename
from langchain_community.tools import DuckDuckGoSearchResults
from tool_imports import import_tools
import whisper
from dashboards.dashboard import create_dashboard
import requests  # Ensure requests is imported

# Load environment variables
load_dotenv()
app = Flask(__name__)
whisper_model = whisper.load_model("base")  # Rename the Whisper model for clarity
openai_api_key = os.getenv('OPENAI_API_KEY')
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_secret_key')
app.config['UPLOAD_FOLDER'] = '/Users/lenox27/LENOX/documents'
socketio = SocketIO(app)

# Pass the `app` object to `create_dashboard` to integrate Dash
app = create_dashboard(app)

# Configure structured logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

# Import tools before they are used
tools = import_tools()

# Create instances of your components
document_handler = DocumentHandler(document_folder="documents", data_folder="data")
prompt_engine_config = PromptEngineConfig(context_length=10, max_tokens=4096)
prompt_engine = PromptEngine(config=prompt_engine_config, tools=tools)

duckduckgo_search = DuckDuckGoSearchResults()

# Initialize Lenox with all necessary components
lenox = Lenox(tools=tools, document_handler=document_handler, prompt_engine=prompt_engine, duckduckgo_search=duckduckgo_search, openai_api_key=openai_api_key)


@app.route('/dashboard')
def dashboard_page():
    return redirect('/dashboard/')


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
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    audio_file = request.files.get('file')
    if not audio_file:
        return jsonify({'error': 'No file provided'}), 400

    # Save the audio file
    audio_path = secure_filename(audio_file.filename)
    audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], audio_path))

    # Perform transcription using the Whisper model
    result = whisper_model.transcribe(os.path.join(app.config['UPLOAD_FOLDER'], audio_path))
    transcription = result['text']
    detected_language = result['language']

    # Clean up the saved file after processing
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], audio_path))

    return jsonify({
        'transcription': transcription,
        'language': detected_language
    })

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        success, message = document_handler.save_document(file)
        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 500
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

@app.route('/document_query', methods=['POST'])
def document_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        if not query:
            return jsonify({'error': 'Empty query.'}), 400

        result = lenox.handle_document_query(query)
        return jsonify({'type': 'document_response', 'response': result})
    except Exception as e:
        app.logger.error(f"Error processing document query: {e}")
        return jsonify({'error': 'Failed to process document query.'}), 500

@app.route('/synthesize', methods=['POST'])
def synthesize_speech():
    data = request.get_json()
    input_text = data.get('input')
    voice = data.get('voice', 'onyx')
    tts_model = data.get('model', 'tts-1-hd')  # Avoid shadowing `model`

    if not input_text:
        return jsonify({'error': 'Input text is missing'}), 400

    try:
        audio_path = lenox.synthesize_text(tts_model, input_text, voice)
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
        query = data.get('query', '').lower()

        if not query:
            app.logger.debug("No query provided in the request.")
            return jsonify({'error': 'Empty query.'}), 400

        result = lenox.convchain(query, session['session_id'])
        app.logger.debug(f"Processed query with convchain, result: {result}")
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Failed to process request.'}), 500

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    feedback_data = request.get_json()
    if 'query' not in feedback_data or 'feedback' not in feedback_data:
        return jsonify({'error': 'Missing necessary feedback data.'}), 400

    query = feedback_data['query']
    feedback = feedback_data['feedback']

    try:
        lenox.teachable_agent.teach_from_feedback(query, feedback)
        return jsonify({'message': 'Feedback processed successfully, and learning was updated.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    try:
        data = request.get_json()
        visualization_result = lenox.handle_visualization_query(data['query'], [], session.get('session_id', 'default_session'))
        return jsonify(visualization_result)
    except Exception as e:
        app.logger.error(f"Failed to create visualization: {str(e)}")
        return jsonify({'error': 'Failed to process visualization.'}), 500

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(lenox.get_sample_data())

@socketio.on('connect')
def on_connect():
    emit('status', {'data': 'Connected to real-time updates'})

@socketio.on('send_feedback')
def on_feedback(data):
    response = lenox.process_feedback(data['feedback'], session['session_id'])
    emit('feedback_response', {'message': 'Feedback processed', 'data': response})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=bool(os.getenv('FLASK_DEBUG')))