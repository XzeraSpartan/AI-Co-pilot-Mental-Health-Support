from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import uuid
import datetime
import logging
import sys
import os

# Add parent directory to path so we can import from other packages
sys.path.append(os.path.dirname(__file__))
from src.models.ai_agents import simulate_student_turn, get_mini_ai_feedback, together

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
    PORT = 5060
    HOST = 'localhost'
    logger.info(f"Starting local development server on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True) 