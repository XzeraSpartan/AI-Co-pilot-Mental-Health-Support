import requests
import json
import websocket
import threading
import time
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://127.0.0.1:5050"
WS_URL = "ws://127.0.0.1:5050/socket.io/?EIO=4&transport=websocket"
session_id = None
ws = None
message_count = 0
received_messages = []
test_complete = threading.Event()

def on_ws_message(ws, message):
    """Handle incoming WebSocket messages."""
    global message_count, received_messages
    
    logger.info(f"Received WebSocket message: {message}")
    
    # Parse Socket.IO message format
    if message.startswith("0"):
        logger.info("Socket.IO handshake received")
    elif message.startswith("40"):
        logger.info("Socket.IO connection established")
        # Join the session room
        if session_id:
            # Format the join event more carefully
            join_message = json.dumps({"session_id": session_id})
            ws.send(f'42["join",{join_message}]')
            logger.info(f"Joined session room: {session_id}")
    elif message.startswith("42"):
        logger.info(f"Received Socket.IO event: {message}")
        try:
            # Extract the JSON payload
            json_str = message[2:]
            event_data = json.loads(json_str)
            
            if len(event_data) >= 2 and event_data[0] == "session_update":
                data = event_data[1]
                message_count += 1
                received_messages.append(data)
                
                # Log based on message type
                if data.get("type") == "typing":
                    logger.info(f"Typing indicator from {data.get('speaker')}")
                elif data.get("type") == "message":
                    logger.info(f"Message from {data.get('speaker')}: {data.get('text')}")
                elif data.get("type") == "feedback":
                    logger.info(f"Feedback received: {data.get('feedback')}")
                
                # If we've received enough messages, end the test
                if message_count >= 10:  # Adjust based on expected message count
                    logger.info("Received sufficient messages, ending test")
                    test_complete.set()
        except Exception as e:
            logger.error(f"Error parsing WebSocket message: {e}")
    elif message.startswith("2"):
        logger.info("Socket.IO ping/pong")
    else:
        logger.info(f"Unknown message format: {message}")

def on_ws_error(ws, error):
    """Handle WebSocket errors."""
    logger.error(f"WebSocket error: {error}")

def on_ws_close(ws, close_status_code, close_msg):
    """Handle WebSocket connection close."""
    logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")

def on_ws_open(ws):
    """Handle WebSocket connection open."""
    logger.info("WebSocket connection opened")
    
    # If we already have a session ID, join that session immediately
    if session_id:
        join_message = json.dumps({"session_id": session_id})
        ws.send(f'42["join",{join_message}]')
        logger.info(f"Joined session room: {session_id}")

def start_websocket():
    """Start WebSocket connection."""
    global ws
    
    # Create WebSocket connection
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_ws_open,
        on_message=on_ws_message,
        on_error=on_ws_error,
        on_close=on_ws_close
    )
    
    # Start WebSocket connection in a separate thread
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()
    
    logger.info("WebSocket thread started")
    return ws_thread

def start_simulation():
    """Start a new simulation session."""
    global session_id
    
    logger.info("Starting simulation session")
    
    try:
        logger.info("Sending POST request to start_simulation endpoint")
        response = requests.post(f"{BASE_URL}/sessions/start_simulation", json={}, timeout=10)
        logger.info(f"Received response with status code: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        session_id = data.get("session_id")
        
        logger.info(f"Simulation started with session ID: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        return None

def end_simulation(session_id):
    """End the simulation session."""
    if not session_id:
        logger.error("Cannot end simulation: No session ID")
        return False
    
    logger.info(f"Ending simulation session: {session_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/end_simulation", 
            json={"session_id": session_id}
        )
        response.raise_for_status()
        
        logger.info("Simulation ended successfully")
        return True
    except Exception as e:
        logger.error(f"Error ending simulation: {e}")
        return False

def analyze_results():
    """Analyze the test results."""
    logger.info("Analyzing test results")
    
    # Count message types
    typing_indicators = sum(1 for msg in received_messages if msg.get("type") == "typing")
    conversation_messages = sum(1 for msg in received_messages if msg.get("type") == "message")
    feedback_messages = sum(1 for msg in received_messages if msg.get("type") == "feedback")
    
    logger.info(f"Received {typing_indicators} typing indicators")
    logger.info(f"Received {conversation_messages} conversation messages")
    logger.info(f"Received {feedback_messages} feedback messages")
    
    # Check for student and educator messages
    student_messages = sum(1 for msg in received_messages 
                          if msg.get("type") == "message" and msg.get("speaker") == "student")
    educator_messages = sum(1 for msg in received_messages 
                           if msg.get("type") == "message" and msg.get("speaker") == "educator")
    
    logger.info(f"Received {student_messages} student messages")
    logger.info(f"Received {educator_messages} educator messages")
    
    # Verify the conversation flow
    if student_messages > 0 and educator_messages > 0 and feedback_messages > 0:
        logger.info("Test PASSED: Conversation flow is working correctly")
    else:
        logger.warning("Test WARNING: Conversation flow may not be complete")
    
    # Print the conversation
    logger.info("\n--- Conversation Transcript ---")
    for msg in received_messages:
        if msg.get("type") == "message":
            speaker = msg.get("speaker", "unknown").capitalize()
            text = msg.get("text", "")
            logger.info(f"{speaker}: {text}")
    logger.info("--- End of Transcript ---\n")

def run_test():
    """Run the complete backend test."""
    global session_id
    
    logger.info("Starting backend test")
    
    # First, start WebSocket connection
    ws_thread = start_websocket()
    
    # Wait for WebSocket to connect fully
    time.sleep(2)
    
    # Now start the simulation
    session_id = start_simulation()
    if not session_id:
        logger.error("Test FAILED: Could not start simulation")
        return
    
    # The session ID should be sent to the WebSocket now
    # Wait a moment for the join to be processed
    time.sleep(1)
    
    # Now wait for messages
    timeout = 120  # 2 minutes
    logger.info(f"Waiting for messages (timeout: {timeout} seconds)")
    test_complete.wait(timeout)
    
    # End simulation
    end_simulation(session_id)
    
    # Close WebSocket connection
    if ws:
        ws.close()
    
    # Analyze results
    analyze_results()
    
    logger.info("Backend test completed")

if __name__ == "__main__":
    # Enable debug logging for WebSocket
    websocket.enableTrace(True)
    
    # Run the test
    run_test() 