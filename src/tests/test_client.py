import requests
import time
import json
import sys
import os
from datetime import datetime
import config

# Configure logging
import logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Server configuration
BASE_URL = f"http://{config.SERVER_HOST}:{config.SERVER_PORT}/api"

def start_conversation(turns=5):
    """Start a new conversation on the server"""
    logger.info("Starting a new conversation...")
    response = requests.post(f"{BASE_URL}/conversations", json={"turns": turns})
    if response.status_code == 201:
        data = response.json()
        conversation_id = data.get("conversation_id")
        logger.info(f"Conversation started with ID: {conversation_id}")
        return conversation_id
    else:
        logger.error(f"Failed to start conversation: {response.text}")
        return None

def poll_conversation_events(conversation_id, last_index=0):
    """Get new events from the conversation using long polling"""
    try:
        response = requests.get(
            f"{BASE_URL}/conversations/{conversation_id}/events",
            params={"last_index": last_index}
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting events: {response.text}")
            return {"status": "error", "events": [], "last_index": last_index}
    except Exception as e:
        logger.error(f"Exception in polling: {e}")
        return {"status": "error", "events": [], "last_index": last_index}

def end_conversation(conversation_id):
    """End the conversation"""
    logger.info(f"Ending conversation {conversation_id}...")
    response = requests.delete(f"{BASE_URL}/conversations/{conversation_id}")
    if response.status_code == 200:
        data = response.json()
        logger.info("Conversation ended successfully")
        # Print the final transcript if available
        if "transcript" in data:
            logger.info("\n===== FINAL CONVERSATION TRANSCRIPT =====")
            logger.info(data["transcript"])
            logger.info("===== END OF FINAL TRANSCRIPT =====\n")
        return True
    else:
        logger.error(f"Failed to end conversation: {response.text}")
        return False

def get_full_conversation(conversation_id):
    """Get the complete conversation after it's done"""
    logger.info(f"Getting full conversation {conversation_id}...")
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}")
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to get conversation: {response.text}")
        return None

def get_transcript(conversation_id):
    """Get just the transcript of the conversation"""
    logger.info(f"Getting transcript for conversation {conversation_id}...")
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/transcript")
    if response.status_code == 200:
        return response.json().get("transcript", "No transcript available")
    else:
        logger.error(f"Failed to get transcript: {response.text}")
        return "Failed to retrieve transcript"

def print_conversation_transcript(events):
    """Print a nicely formatted transcript of the conversation"""
    logger.info("\n===== CONVERSATION TRANSCRIPT =====")
    # Filter and sort message events
    messages = [event for event in events if event.get("type") == "message"]
    messages.sort(key=lambda x: x.get("timestamp", ""))
    
    for msg in messages:
        speaker = msg.get("name", msg.get("speaker", "unknown").upper())
        text = msg.get("text", "")
        timestamp = msg.get("timestamp", "")
        logger.info(f"[{speaker}]: {text}")
    
    logger.info("===== END OF TRANSCRIPT =====\n")

def print_feedback_analysis(events):
    """Print the feedback provided during the conversation"""
    logger.info("\n===== MINI AI FEEDBACK ANALYSIS =====")
    # Filter and sort feedback events
    feedback_events = [event for event in events if event.get("type") == "feedback"]
    feedback_events.sort(key=lambda x: x.get("timestamp", ""))
    
    for idx, event in enumerate(feedback_events):
        feedback = event.get("feedback", {})
        timestamp = event.get("timestamp", "")
        logger.info(f"Feedback #{idx+1}:")
        logger.info(f"Analysis: {feedback.get('analysis', 'N/A')}")
        logger.info(f"Suggestions: {', '.join(feedback.get('suggestions', ['N/A']))}")
        logger.info("---")
    
    logger.info("===== END OF FEEDBACK ANALYSIS =====\n")

def main():
    logger.info("Starting test client for AI Co-Pilot Mental Health Support")
    
    # Start a conversation
    turns = int(os.environ.get('TEST_TURNS', 10))
    conversation_id = start_conversation(turns=turns)
    if not conversation_id:
        return
    
    # Poll for events until the conversation is complete
    last_index = 0
    active = True
    consecutive_empty_polls = 0
    max_empty_polls = int(os.environ.get('MAX_EMPTY_POLLS', 10))
    
    logger.info("Waiting for conversation events...")
    while active:
        data = poll_conversation_events(conversation_id, last_index)
        events = data.get("events", [])
        last_index = data.get("last_index", last_index)
        
        if events:
            consecutive_empty_polls = 0
            for event in events:
                event_type = event.get("type", "unknown")
                if event_type == "message":
                    speaker = event.get("name", event.get("speaker", "unknown").upper())
                    text = event.get("text", "")
                    logger.info(f"New message from {speaker}: {text}")
                elif event_type == "typing":
                    speaker = event.get("name", event.get("speaker", "unknown").upper())
                    logger.info(f"{speaker} is typing...")
                elif event_type == "feedback":
                    feedback = event.get("feedback", {})
                    logger.info(f"New feedback: {feedback.get('analysis', '')}")
                    logger.info(f"Suggestions: {', '.join(feedback.get('suggestions', ['N/A']))}")
        else:
            consecutive_empty_polls += 1
            logger.info(f"No new events... ({consecutive_empty_polls}/{max_empty_polls})")
            
        # End condition: if we get 10 consecutive empty polls, assume conversation is over
        if consecutive_empty_polls >= max_empty_polls:
            logger.info("No activity for a while, assuming conversation is complete")
            active = False
        
        time.sleep(1)
    
    # Get the transcript
    logger.info("\n===== FINAL TRANSCRIPT FROM SERVER =====")
    transcript = get_transcript(conversation_id)
    logger.info(transcript)
    logger.info("===== END OF FINAL TRANSCRIPT =====\n")
    
    # Get the complete conversation
    conversation_data = get_full_conversation(conversation_id)
    if conversation_data:
        # Print the feedback analysis
        print_feedback_analysis(conversation_data.get("events", []))
        
        # Print metadata if available
        if "metadata" in conversation_data:
            metadata = conversation_data["metadata"]
            logger.info("\n===== CONVERSATION METADATA =====")
            for key, value in metadata.items():
                logger.info(f"{key}: {value}")
            logger.info("===== END OF METADATA =====\n")
    
    # End the conversation
    end_conversation(conversation_id)
    logger.info("Test client finished")

if __name__ == "__main__":
    main() 