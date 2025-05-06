import time
import threading
import datetime
import json
import random
from models import Session
from extensions import db
from ai_agents import simulate_student_turn, simulate_educator_turn, get_mini_ai_feedback

class SimulationEngine:
    def __init__(self, session_id, socketio, app):
        self.session_id = session_id
        self.socketio = socketio
        self.app = app
        self.running = False
        self.conversation_history = []
        self.lock = threading.Lock()
        self.current_feedback = None
        self.client_connected = False  # New flag to track connection
    
    def run(self):
        with self.app.app_context():
            self._run_simulation()
    
    def _run_simulation(self):
        self.running = True
        
        # Wait for client to connect (up to 10 seconds)
        print(f"Waiting for client to join session: {self.session_id}")
        wait_time = 0
        while not self.client_connected and wait_time < 10:
            time.sleep(1)
            wait_time += 1
            
        if wait_time >= 10:
            print("No client connected after waiting. Continuing anyway...")
        else:
            print("Client connected! Starting conversation.")
            
        # Start with student message
        self._process_student_turn()
        
        # Continue the conversation until stopped
        turn_count = 1
        max_turns = 10  # Limit for demo purposes
        
        while self.running and turn_count < max_turns:
            # Educator's turn
            self._process_educator_turn()
            
            # Check if simulation should continue
            if not self.running:
                break
                
            # Student's turn
            self._process_student_turn()
            
            turn_count += 1
        
        # End the simulation if it hasn't been stopped already
        self._end_simulation()
    
    def _process_student_turn(self):
        """Process a turn from the student AI."""
        try:
            print("Starting student turn")
            # Simulate typing indicator
            self._send_typing_indicator("student")
            
            # Generate student response
            print("Calling student AI")
            student_message = simulate_student_turn(self.conversation_history)
            print(f"Student message received: {student_message[:30]}...")
            
            # Add delay to simulate thinking/typing
            time.sleep(random.uniform(2, 4))
            
            # Send and save the message
            timestamp = datetime.datetime.utcnow().isoformat()
            message_data = {
                "session_id": self.session_id,
                "type": "message",
                "speaker": "student",
                "text": student_message,
                "timestamp": timestamp
            }
            
            # Add to conversation history
            with self.lock:
                self.conversation_history.append({"speaker": "student", "text": student_message})
            
            # Save to database
            self._save_message_to_db(message_data)
            
            # Send via WebSocket
            self.socketio.emit('session_update', message_data, room=self.session_id)
            
            # Get feedback from Mini AI
            self._get_and_send_feedback()
            
            # Check for end conditions in student message
            if self._check_end_condition(student_message):
                self.running = False
        except Exception as e:
            print(f"ERROR in student turn: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _process_educator_turn(self):
        """Process a turn from the educator AI."""
        try:
            print("Starting educator turn")
            # Simulate typing indicator
            self._send_typing_indicator("educator")
            
            # Generate educator response using feedback
            print("Calling educator AI")
            educator_message = simulate_educator_turn(
                self.conversation_history, 
                self.current_feedback
            )
            print(f"Educator message received: {educator_message[:30]}...")
            
            # Add delay to simulate thinking/typing
            time.sleep(random.uniform(3, 5))
            
            # Send and save the message
            timestamp = datetime.datetime.utcnow().isoformat()
            message_data = {
                "session_id": self.session_id,
                "type": "message",
                "speaker": "educator",
                "text": educator_message,
                "timestamp": timestamp
            }
            
            # Add to conversation history
            with self.lock:
                self.conversation_history.append({"speaker": "educator", "text": educator_message})
            
            # Save to database
            self._save_message_to_db(message_data)
            
            # Send via WebSocket
            self.socketio.emit('session_update', message_data, room=self.session_id)
        except Exception as e:
            print(f"ERROR in educator turn: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_and_send_feedback(self):
        """Get feedback from Mini AI and send it to the frontend."""
        # Get feedback based on the latest conversation
        feedback = get_mini_ai_feedback(self.conversation_history)
        self.current_feedback = feedback
        
        # Prepare feedback data
        timestamp = datetime.datetime.utcnow().isoformat()
        feedback_data = {
            "session_id": self.session_id,
            "type": "feedback",
            "feedback": feedback,
            "timestamp": timestamp
        }
        
        # Send feedback via WebSocket
        self.socketio.emit('session_update', feedback_data, room=self.session_id)
    
    def _send_typing_indicator(self, speaker):
        """Send typing indicator via WebSocket."""
        typing_data = {
            "session_id": self.session_id,
            "type": "typing",
            "speaker": speaker
        }
        print(f"Emitting typing indicator: {typing_data}")
        self.socketio.emit('session_update', typing_data, room=self.session_id)
    
    def _save_message_to_db(self, message_data):
        """Save a message to the database transcript."""
        with db.session.begin():
            session = Session.query.filter_by(session_id=self.session_id).first()
            if session:
                # Create a copy of the transcript to modify
                transcript = session.transcript.copy() if session.transcript else []
                
                # Add the new message
                transcript_entry = {
                    "speaker": message_data["speaker"],
                    "type": "message",
                    "text": message_data["text"],
                    "timestamp": message_data["timestamp"]
                }
                transcript.append(transcript_entry)
                
                # Update the session
                session.transcript = transcript
                db.session.commit()
    
    def _check_end_condition(self, message):
        """Check if the message indicates the conversation should end."""
        end_phrases = [
            "i feel better", 
            "thanks for talking", 
            "that helps a lot",
            "i should go now",
            "thank you for your help"
        ]
        
        message_lower = message.lower()
        for phrase in end_phrases:
            if phrase in message_lower:
                return True
        
        return False
    
    def _end_simulation(self):
        """End the simulation and update the database."""
        if not self.running:
            return
            
        self.running = False
        
        with db.session.begin():
            session = Session.query.filter_by(session_id=self.session_id).first()
            if session and session.status != 'ended':
                session.status = 'ended'
                session.end_time = datetime.datetime.utcnow()
                db.session.commit()
    
    def stop(self):
        """Stop the simulation."""
        self.running = False
    
    def client_joined(self):
        """Called when a client joins the session."""
        print(f"Client joined session: {self.session_id}")
        self.client_connected = True
        # You could send a notification if needed 