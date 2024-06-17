from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from documents import DocumentHandler, allowed_file
from lenox import Lenox
from prompts import PromptEngine, PromptEngineConfig
from werkzeug.utils import secure_filename
from tool_imports import import_tools
import whisper
from dashboards.dashboard import create_dashboard



# Load environment variables
load_dotenv()
app = Flask(__name__)
whisper_model = whisper.load_model("base")
openai_api_key = os.getenv('OPENAI_API_KEY')
tavily_api_key = os.getenv('TAVILY_API_KEY')

# Ensure tavily_api_key is not None
if tavily_api_key is None:
    raise ValueError("TAVILY_API_KEY environment variable is not set")

CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_secret_key')
app.config['UPLOAD_FOLDER'] = '/Users/lenox27/LENOX/documents'
socketio = SocketIO(app)

# Pass the `app` object to `create_dashboard` to integrate Dash
app = create_dashboard(app)

handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

# Import tools before they are used
tools = import_tools()
tools = {"tool_{}".format(i): tool for i, tool in enumerate(tools)}

# Create instances of your components
document_handler = DocumentHandler(document_folder="documents", data_folder="data")
prompt_engine_config = PromptEngineConfig(context_length=10, max_tokens=4096)
prompt_engine = PromptEngine(config=prompt_engine_config, tools=tools, api_key=tavily_api_key)

# Initialize Lenox with all necessary components
lenox = Lenox(
    tools=tools,
    document_handler=document_handler,
    prompt_engine=prompt_engine,
    tavily_search=prompt_engine.tavily_tool,
    openai_api_key=openai_api_key,
    tavily_api_key=tavily_api_key  # Ensure the tavily_api_key is passed here
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.get_json()
        query = data.get('query', '').lower()

        if not query:
            app.logger.debug("No query provided in the request.")
            return jsonify({'error': 'Empty query.'}), 400

        result = lenox.handle_query(query, session['session_id'])
        app.logger.debug(f"Processed query with handle_query, result: {result}")
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Failed to process request.'}), 500

@app.route('/dashboard')
def dashboard_page():
    return redirect('/dashboard/')

@app.before_request
def log_request():
    app.logger.debug(f'Incoming request: {request.method} {request.path}')
    session.setdefault('session_id', os.urandom(24).hex())

@app.after_request
def log_response(response):
    app.logger.debug(f'Outgoing response: {response.status_code}')
    return response

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename or "")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Save the file to the upload folder
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
    tts_model = data.get('model', 'tts-1-hd')

    if not input_text:
        return jsonify({'error': 'Input text is missing'}), 400

    try:
        audio_path = lenox.synthesize_text(tts_model, input_text, voice)
        if audio_path:
            directory = os.path.dirname(audio_path)
            filename = os.path.basename(audio_path)
            return send_from_directory(directory=directory, filename=filename, as_attachment=True)
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    feedback_data = request.get_json()
    if 'query' not in feedback_data or 'feedback' not in feedback_data:
        return jsonify({'error': 'Missing necessary feedback data.'}), 400

    query = feedback_data['query']
    feedback = feedback_data['feedback']

    try:
        app.logger.info(f"Received feedback for query: {query}")
        app.logger.info(f"Feedback content: {feedback}")
        return jsonify({'message': 'Feedback processed successfully, and learning was updated.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_visualization', methods=['POST'])
def create_visualization():
    try:
        data = request.get_json()
        visualization_result = lenox.create_visualization(data['query'])
        return jsonify(visualization_result)
    except AttributeError as e:
        app.logger.error(f"Failed to create visualization: {str(e)}")
        return jsonify({'error': 'Failed to process visualization. Method not found.'}), 500
    except Exception as e:
        app.logger.error(f"Failed to create visualization: {str(e)}")
        return jsonify({'error': 'Failed to process visualization.'}), 500

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify({})

@socketio.on('connect')
def on_connect():
    emit('status', {'data': 'Connected to real-time updates'})

@socketio.on('send_feedback')
def on_feedback(data):
    response = {}  # Replace with actual processing logic if needed
    emit('feedback_response', {'message': 'Feedback processed', 'data': response})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=bool(os.getenv('FLASK_DEBUG')))