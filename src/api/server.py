from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
import json
import uuid
import time
import datetime
import threading
import logging
import sys
import os
import traceback

# Add parent directory to path so we can import from other packages
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from src.config.config import *
from src.models.ai_agents import simulate_student_turn, simulate_educator_turn, get_mini_ai_feedback, together

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

# Define allowed origins with the complete URL patterns
ALLOWED_ORIGINS = [
    "https://mentalcopilot.netlify.app",
    "https://mentalcopilot.netlify.app/",
    "http://localhost:5173", 
    "https://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3000/"
]

# Don't use the flask-cors extension configuration since we're handling CORS manually
# This prevents potential conflicts with our custom CORS implementation

# Handle CORS errors
@app.errorhandler(Exception)
def handle_error(e):
    """Global error handler that ensures CORS headers are added even for errors."""
    logger.error(f"Error: {str(e)}")
    logger.error(traceback.format_exc())
    
    # Prepare error response
    response = jsonify({
        'status': 'error',
        'message': str(e),
        'error_type': type(e).__name__
    })
    
    # Add CORS headers
    origin = request.headers.get('Origin', '')
    
    # Log the origin for debugging
    logger.debug(f'Request origin in error handler: {origin}')
    
    # Check if the origin is in allowed origins
    if any(origin.startswith(allowed) for allowed in ALLOWED_ORIGINS):
        # Set the proper CORS headers
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-Custom-Header'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'  # Cache preflight requests for 1 hour
    
    return response, 500

# Store active conversations
active_conversations = {}

class Conversation:
    def __init__(self, conversation_id):
        self.conversation_id = conversation_id
        self.history = []
        self.events = []
        self.running = True
        self.lock = threading.Lock()
        self.resolution_detected = False
        self.created_at = datetime.datetime.utcnow()
        logger.info(f"Conversation created: {conversation_id}")
    
    def add_event(self, event):
        """Add an event to the conversation."""
        with self.lock:
            # Add event ID if not present
            if 'id' not in event:
                event['id'] = str(uuid.uuid4())
            
            # Add timestamp if not present
            if 'timestamp' not in event:
                event['timestamp'] = datetime.datetime.utcnow().isoformat()
            
            # Add index if not present
            if 'index' not in event:
                event['index'] = len(self.events)
            
            # Ensure event type is one of: typing, message, feedback
            if event.get('type') not in ['typing', 'message', 'feedback']:
                event['type'] = 'message'
            
            # For feedback events, ensure analysis and suggestions are present
            if event.get('type') == 'feedback':
                if 'analysis' not in event:
                    event['analysis'] = event.get('feedback', {}).get('analysis', '')
                if 'suggestions' not in event:
                    event['suggestions'] = event.get('feedback', {}).get('suggestions', [])
            
            # For message events, ensure sender is present
            if event.get('type') == 'message':
                if 'sender' not in event:
                    event['sender'] = event.get('speaker', 'student')
            
            self.events.append(event)
            
            # If it's a message, add to conversation history
            if event.get('type') == 'message':
                self.history.append({
                    'speaker': event.get('speaker'),
                    'text': event.get('text'),
                    'id': event['id'],
                    'timestamp': event['timestamp']
                })
                logger.info(f"Message added - {event.get('speaker')}: {event.get('text')[:50]}...")
    
    def run_conversation(self, turns=5):
        """Run the conversation simulation."""
        thread = threading.Thread(target=self._generate_conversation, args=(turns,))
        thread.daemon = True
        thread.start()
        logger.info(f"Conversation thread started for {self.conversation_id} with {turns} turns")
    
    def _generate_conversation(self, turns):
        """Generate the conversation between AI agents."""
        try:
            # Start with student turn
            for i in range(turns):
                if not self.running or self.resolution_detected:
                    logger.info(f"Conversation {self.conversation_id} ending early at turn {i}")
                    break
                    
                # Student's turn
                self._process_student_turn()
                
                # Break if conversation ended
                if not self.running or self.resolution_detected:
                    break
                    
                # Educator's turn
                self._process_educator_turn()
            
            logger.info(f"Conversation {self.conversation_id} generation completed")
        except Exception as e:
            logger.error(f"Error in conversation generation: {e}", exc_info=True)
    
    def _process_student_turn(self):
        """Process a turn from the student AI."""
        try:
            logger.info(f"Starting student turn for conversation {self.conversation_id}")
            
            # Send typing indicator
            timestamp = datetime.datetime.utcnow().isoformat()
            typing_event = {
                "id": str(uuid.uuid4()),
                "type": "typing",
                "index": len(self.events),
                "sender": "student",
                "timestamp": timestamp
            }
            self.add_event(typing_event)
            
            # Add a small delay (simulating typing)
            time.sleep(TYPING_DELAY_STUDENT)
            
            # Generate student message
            student_message = simulate_student_turn(self.history)
            timestamp = datetime.datetime.utcnow().isoformat()
            message_event = {
                "id": str(uuid.uuid4()),
                "type": "message",
                "index": len(self.events),
                "content": student_message,
                "sender": "student",
                "timestamp": timestamp
            }
            self.add_event(message_event)
            logger.info(f"Student message generated: {student_message[:50]}...")
            
            # Generate Mini AI feedback
            feedback = get_mini_ai_feedback(self.history)
            timestamp = datetime.datetime.utcnow().isoformat()
            feedback_event = {
                "id": str(uuid.uuid4()),
                "type": "feedback",
                "index": len(self.events),
                "content": feedback.get('analysis', ''),
                "analysis": feedback.get('analysis', ''),
                "suggestions": feedback.get('suggestions', []),
                "timestamp": timestamp
            }
            self.add_event(feedback_event)
            logger.info(f"Feedback generated: {feedback.get('analysis', '')[:50]}...")
            
            # Check for end conditions
            if self._check_end_condition(student_message):
                logger.info(f"Resolution detected in student message - ending conversation")
                self.resolution_detected = True
                
        except Exception as e:
            logger.error(f"Error in student turn: {e}", exc_info=True)
    
    def _process_educator_turn(self):
        """Process a turn from the educator AI."""
        try:
            logger.info(f"Starting educator turn for conversation {self.conversation_id}")
            
            # Get the latest feedback
            latest_feedback = None
            for event in reversed(self.events):
                if event.get('type') == 'feedback':
                    latest_feedback = event.get('feedback')
                    break
            
            # Send typing indicator
            timestamp = datetime.datetime.utcnow().isoformat()
            typing_event = {
                "id": str(uuid.uuid4()),
                "type": "typing",
                "index": len(self.events),
                "sender": "educator",
                "timestamp": timestamp
            }
            self.add_event(typing_event)
            
            # Add a small delay (simulating typing)
            time.sleep(TYPING_DELAY_EDUCATOR)
            
            # Generate educator message
            educator_message = simulate_educator_turn(self.history, latest_feedback)
            timestamp = datetime.datetime.utcnow().isoformat()
            message_event = {
                "id": str(uuid.uuid4()),
                "type": "message",
                "index": len(self.events),
                "content": educator_message,
                "sender": "educator",
                "timestamp": timestamp
            }
            self.add_event(message_event)
            logger.info(f"Educator message generated: {educator_message[:50]}...")
            
        except Exception as e:
            logger.error(f"Error in educator turn: {e}", exc_info=True)
    
    def _check_end_condition(self, message):
        """Check if the message indicates the conversation should end."""
        end_phrases = [
            "i feel better", 
            "thanks for talking", 
            "that helps a lot",
            "i should go now",
            "thank you for your help",
            "feel a bit better now",
            "i'll try what you suggested",
            "that makes sense",
            "i appreciate your help",
            "that's helpful"
        ]
        
        message_lower = message.lower()
        for phrase in end_phrases:
            if phrase in message_lower:
                return True
        
        return False
    
    def get_events_since(self, index):
        """Get events since a specific index."""
        with self.lock:
            if index < len(self.events):
                return self.events[index:]
            return []

    def get_conversation_transcript(self):
        """Get a formatted transcript of the conversation."""
        messages = [event for event in self.events if event.get("type") == "message"]
        transcript = []
        
        for msg in messages:
            speaker = msg.get("sender", "student").capitalize()
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            transcript.append(f"{speaker} ({timestamp}): {content}")
        
        return "\n\n".join(transcript)

    def get_metadata(self):
        """Get metadata about the conversation."""
        return {
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "message_count": len([e for e in self.events if e.get("type") == "message"]),
            "student_messages": len([e for e in self.events if e.get("type") == "message" and e.get("speaker") == "student"]),
            "educator_messages": len([e for e in self.events if e.get("type") == "message" and e.get("speaker") == "educator"]),
            "status": "resolved" if self.resolution_detected else "active" if self.running else "ended",
            "last_activity": self.events[-1]["timestamp"] if self.events else self.created_at.isoformat(),
            "duration": (datetime.datetime.utcnow() - self.created_at).total_seconds(),
            "has_feedback": any(e.get("type") == "feedback" for e in self.events),
            "participants": {
                "student": STUDENT_NAME,
                "educator": EDUCATOR_NAME
            }
        }

@app.route('/api/conversations', methods=['POST'])
def start_conversation():
    """Start a new conversation."""
    try:
        conversation_id = str(uuid.uuid4())
        data = request.json or {}
        turns = data.get('turns', 5)
        
        # Create new conversation
        conversation = Conversation(conversation_id)
        active_conversations[conversation_id] = conversation
        
        # Start generating the conversation
        conversation.run_conversation(turns=turns)
        
        logger.info(f"New conversation started: {conversation_id}")
        
        return jsonify({
            'status': 'success',
            'conversation_id': conversation_id,
            'message': 'Conversation started successfully'
        }), 201
    except Exception as e:
        logger.error(f"Error starting conversation: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>/events', methods=['GET'])
def get_conversation_events(conversation_id):
    """Get events from a conversation using long polling."""
    try:
        if conversation_id not in active_conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        conversation = active_conversations[conversation_id]
        
        # Get the last event index the client has seen
        last_index = int(request.args.get('last_index', 0))
        
        # Use long polling to wait for new events
        def generate():
            wait_time = 0
            while wait_time < LONG_POLLING_TIMEOUT:  # Wait for configured timeout
                events = conversation.get_events_since(last_index)
                if events:
                    logger.debug(f"Returning {len(events)} new events for conversation {conversation_id}")
                    return json.dumps({
                        'status': 'success',
                        'events': events,
                        'last_index': last_index + len(events)
                    })
                
                time.sleep(1)
                wait_time += 1
            
            # If no new events after timeout, return empty list
            logger.debug(f"No new events for conversation {conversation_id} after {wait_time}s")
            return json.dumps({
                'status': 'success',
                'events': [],
                'last_index': last_index
            })
        
        return Response(generate(), mimetype='application/json')
    except Exception as e:
        logger.error(f"Error getting conversation events: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_full_conversation(conversation_id):
    """Get the full conversation."""
    try:
        if conversation_id not in active_conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        conversation = active_conversations[conversation_id]
        
        return jsonify({
            'status': 'success',
            'conversation_id': conversation_id,
            'events': conversation.events,
            'transcript': conversation.get_conversation_transcript(),
            'metadata': conversation.get_metadata()
        }), 200
    except Exception as e:
        logger.error(f"Error getting full conversation: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>/transcript', methods=['GET'])
def get_conversation_transcript(conversation_id):
    """Get just the transcript of the conversation."""
    try:
        if conversation_id not in active_conversations:
            logger.warning(f"Conversation not found: {conversation_id}")
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        conversation = active_conversations[conversation_id]
        
        return jsonify({
            'status': 'success',
            'conversation_id': conversation_id,
            'transcript': conversation.get_conversation_transcript()
        }), 200
    except Exception as e:
        logger.error(f"Error getting conversation transcript: {e}", exc_info=True)
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
            logger.warning(f"Conversation not found: {conversation_id}")
            return jsonify({
                'status': 'error',
                'message': 'Conversation not found'
            }), 404
        
        conversation = active_conversations[conversation_id]
        conversation.running = False
        
        # Wait a moment for any processing to finish
        time.sleep(1)
        
        # Get the transcript before removing the conversation
        transcript = conversation.get_conversation_transcript()
        metadata = conversation.get_metadata()
        
        # Remove from active conversations
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
    
    # Log the origin for debugging
    logger.debug(f'Request origin: {origin}')
    
    # Check if the origin is in allowed origins using startswith for more flexible matching
    if any(origin.startswith(allowed) for allowed in ALLOWED_ORIGINS):
        # Set the proper CORS headers
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-Custom-Header'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'  # Cache preflight requests for 1 hour
    
    return response

# Handle all OPTIONS requests (preflight requests)
@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_route(path=''):
    # For OPTIONS requests, just return headers (created by add_cors_headers)
    return '', 200

@app.route('/health', methods=['GET'])
def health_check():
    """Check the health of the server and API connections."""
    try:
        # Check if Together client is initialized
        if together is None:
            return jsonify({
                'status': 'degraded',
                'api_status': 'disconnected',
                'error': 'Together client not initialized',
                'active_conversations': len(active_conversations),
                'timestamp': datetime.datetime.utcnow().isoformat()
            }), 503
            
        # Check if API key is set
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
