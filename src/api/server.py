from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import uuid
import time
import datetime
import logging
import sys
import os
import traceback

# Add parent directory to path so we can import from other packages
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from src.config.config import *
from src.models.ai_agents import simulate_student_turn, get_mini_ai_feedback, together

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Debug middleware to log all requests
@app.before_request
def log_request_info():
    """Log request details for debugging."""
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())
    logger.debug('Origin: %s', request.headers.get('Origin', 'No origin header'))

# Define allowed origins
ALLOWED_ORIGINS = [
    "https://mentalcopilot.netlify.app",
    "https://mentalcopilot.netlify.app/",
    "http://localhost:5173", 
    "https://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3000/",
    "https://zippy-kitsune-1bbced.netlify.app/",
    "https://zippy-kitsune-1bbced.netlify.app"
]

# Store active conversations
active_conversations = {}

class Conversation:
    def __init__(self, conversation_id):
        self.conversation_id = conversation_id
        self.history = []
        self.created_at = datetime.datetime.utcnow()
        logger.info(f"Conversation created: {conversation_id}")
    
    def add_message(self, speaker, text):
        """Add a message to the conversation history."""
        message = {
            'id': str(uuid.uuid4()),
            'speaker': speaker,
            'text': text,
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        self.history.append(message)
        logger.info(f"Message added - {speaker}: {text[:50]}...")
        return message
    
    def get_transcript(self):
        """Get the full conversation transcript."""
        return self.history
    
    def get_metadata(self):
        """Get conversation metadata."""
        return {
            'id': self.conversation_id,
            'created_at': self.created_at.isoformat(),
            'message_count': len(self.history),
            'last_message': self.history[-1] if self.history else None
        }

@app.route('/api/conversations', methods=['POST'])
def start_conversation():
    """Start a new conversation."""
    try:
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(conversation_id)
        active_conversations[conversation_id] = conversation
        
        # Generate initial student message
        student_message = simulate_student_turn([])
        conversation.add_message('student', student_message)
        
        # Get initial suggestions
        feedback = get_mini_ai_feedback(conversation.history)
        
        return jsonify({
            'status': 'success',
            'conversation_id': conversation_id,
            'transcript': conversation.get_transcript(),
            'suggestions': feedback
        }), 200
    except Exception as e:
        logger.error(f"Error starting conversation: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>/message', methods=['POST'])
def send_message(conversation_id):
    """Send a message from the educator and get student's response."""
    try:
        if conversation_id not in active_conversations:
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        # Get educator's message from request
        data = request.json
        if not data or 'message' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
        
        conversation = active_conversations[conversation_id]
        
        # Add educator's message
        conversation.add_message('educator', data['message'])
        
        # Generate student's response
        student_message = simulate_student_turn(conversation.history)
        conversation.add_message('student', student_message)
        
        # Get suggestions for next response
        feedback = get_mini_ai_feedback(conversation.history)
        
        return jsonify({
            'status': 'success',
            'conversation_id': conversation_id,
            'transcript': conversation.get_transcript(),
            'suggestions': feedback
        }), 200
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get the full conversation."""
    try:
        if conversation_id not in active_conversations:
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        conversation = active_conversations[conversation_id]
        
        return jsonify({
            'status': 'success',
            'conversation_id': conversation_id,
            'transcript': conversation.get_transcript(),
            'metadata': conversation.get_metadata()
        }), 200
    except Exception as e:
        logger.error(f"Error getting conversation: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    """List all active conversations."""
    try:
        conversations = []
        for conversation_id, conversation in active_conversations.items():
            conversations.append(conversation.get_metadata())
        
        return jsonify({
            'status': 'success',
            'conversations': conversations
        }), 200
    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def end_conversation(conversation_id):
    """End a conversation."""
    try:
        if conversation_id not in active_conversations:
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        conversation = active_conversations[conversation_id]
        transcript = conversation.get_transcript()
        metadata = conversation.get_metadata()
        
        del active_conversations[conversation_id]
        logger.info(f"Conversation ended: {conversation_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Conversation ended successfully',
            'transcript': transcript,
            'metadata': metadata
        }), 200
    except Exception as e:
        logger.error(f"Error ending conversation: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses."""
    origin = request.headers.get('Origin', '')
    
    if any(origin.startswith(allowed) for allowed in ALLOWED_ORIGINS):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-Custom-Header'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
    
    return response

# Handle OPTIONS requests
@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_route(path=''):
    return '', 200

@app.route('/health', methods=['GET'])
def health_check():
    """Check the health of the server and API connections."""
    try:
        if together is None:
            return jsonify({
                'status': 'degraded',
                'api_status': 'disconnected',
                'error': 'Together client not initialized',
                'active_conversations': len(active_conversations),
                'timestamp': datetime.datetime.utcnow().isoformat()
            }), 503
            
        if not together.api_key:
            return jsonify({
                'status': 'degraded',
                'api_status': 'disconnected',
                'error': 'Together API key not set',
                'active_conversations': len(active_conversations),
                'timestamp': datetime.datetime.utcnow().isoformat()
            }), 503
            
        return jsonify({
            'status': 'healthy',
            'api_status': 'connected',
            'active_conversations': len(active_conversations),
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'degraded',
            'api_status': 'disconnected',
            'error': str(e),
            'active_conversations': len(active_conversations),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 503

if __name__ == '__main__':
    logger.info("Starting AI Co-Pilot Mental Health Support backend server")
    
    # Check if SSL certificates exist and use them if they do
    cert_path = "/etc/letsencrypt/live/cpmhs.harshrajj.com/fullchain.pem"
    key_path = "/etc/letsencrypt/live/cpmhs.harshrajj.com/privkey.pem"
    
    ssl_context = None
    try:
        if os.path.exists(cert_path) and os.path.exists(key_path):
            logger.info(f"SSL certificates found, running with HTTPS on port {SERVER_PORT}")
            ssl_context = (cert_path, key_path)
        else:
            logger.warning(f"SSL certificates not found at {cert_path} and {key_path}")
            logger.warning("Running without SSL - CORS may not work in production!")
    except Exception as e:
        logger.error(f"Error checking SSL certificates: {e}")
        logger.warning("Running without SSL - CORS may not work in production!")
    
    # Run the app with or without SSL depending on certificate availability
    app.run(
        debug=DEBUG_MODE, 
        host='0.0.0.0', 
        port=SERVER_PORT,
        ssl_context=ssl_context
    )
