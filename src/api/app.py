from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from extensions import db
import uuid
import time
import threading
import json
import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///mental_health.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
socketio = SocketIO(app, cors_allowed_origins="*")
db.init_app(app)

# Import models after db.init_app(app)
from models import Session

# Import SimulationEngine after app and db are set up
from simulation_engine import SimulationEngine

# Store active simulation engines
active_simulations = {}

@app.route('/sessions/start_simulation', methods=['POST'])
def start_simulation():
    """Start a new simulated session between AI agents."""
    data = request.json or {}
    student_id = data.get('student_id', str(uuid.uuid4()))
    educator_id = data.get('educator_id', str(uuid.uuid4()))
    
    # Create a new session in the database
    session = Session(
        session_id=str(uuid.uuid4()),
        student_id=student_id,
        educator_id=educator_id,
        start_time=datetime.datetime.utcnow(),
        transcript=[],
        status='simulating'
    )
    db.session.add(session)
    db.session.commit()
    
    # Create and start the simulation engine
    simulation = SimulationEngine(session.session_id, socketio, app)
    active_simulations[session.session_id] = simulation
    
    # Start the simulation in a separate thread
    simulation_thread = threading.Thread(target=simulation.run)
    simulation_thread.daemon = True
    simulation_thread.start()
    
    return jsonify({
        'status': 'success',
        'session_id': session.session_id,
        'message': 'Simulation started successfully'
    }), 201

@app.route('/sessions/end_simulation', methods=['POST'])
def end_simulation():
    """End an ongoing simulated session."""
    data = request.json or {}
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'status': 'error', 'message': 'Session ID is required'}), 400
    
    # Get the session from the database
    session = Session.query.filter_by(session_id=session_id).first()
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    # Stop the simulation engine if it's active
    if session_id in active_simulations:
        active_simulations[session_id].stop()
        del active_simulations[session_id]
    
    # Update the session in the database
    session.end_time = datetime.datetime.utcnow()
    session.status = 'ended'
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Simulation ended successfully'
    }), 200

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print('Client disconnected')

@socketio.on('join')
def on_join(data):
    """Join a specific session room."""
    session_id = data.get('session_id')
    if session_id:
        print(f"Client joined session: {session_id}")
        # Join the room with this session_id
        socketio.server.enter_room(request.sid, session_id)
        print(f"Active rooms: {socketio.server.manager.rooms}")
        
        # If a simulation is active for this session, let it know a client has connected
        if session_id in active_simulations:
            print(f"Setting client_connected=True for session {session_id}")
            active_simulations[session_id].client_connected = True
            
            # Send a welcome message to confirm connection
            welcome_data = {
                "session_id": session_id,
                "type": "system",
                "text": "Welcome to the session. Conversation will begin shortly.",
            }
            socketio.emit('session_update', welcome_data, room=session_id)

@socketio.on_error()        
def error_handler(e):
    print(f"Socket.IO error: {e}")
    
@socketio.on_error_default
def default_error_handler(e):
    print(f"Socket.IO default error: {e}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='127.0.0.1', port=5050) 