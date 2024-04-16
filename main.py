from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler  # Ensure this is correctly imported
from dotenv import load_dotenv
from documents import DocumentHandler
from utils import Lenox
from prompts import PromptEngine
from tool_imports import import_tools

# Load environment variables
load_dotenv()
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_secret_key')
socketio = SocketIO(app)

# Configure structured logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

# Initialize components
document_handler = DocumentHandler(document_folder="documents", data_folder="data")
tools = import_tools()
prompt_engine = PromptEngine(context_length=5, max_tokens=2048, tools=tools, model_name="gpt-3.5-turbo")
lenox = Lenox(tools=tools, document_handler=document_handler, prompt_engine=prompt_engine)

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

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Empty query.'}), 400
    return jsonify(lenox.convchain(query, session['session_id']))

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    feedback_data = request.get_json()
    if 'feedback' not in feedback_data:
        return jsonify({'error': 'Missing feedback data.'}), 400
    lenox.process_feedback(feedback_data['feedback'], session['session_id'])
    return jsonify({'message': 'Thank you for your feedback!'})

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
