import os
import random
import sys
import logging
import time
from typing import List, Dict, Optional
from together import Together

# Add parent directory to path so we can import from src.config
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from src.config.config import *

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Together client
try:
    together = Together()
    together.api_key = TOGETHER_API_KEY
    logger.info("Together client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Together client: {e}")
    together = None

def format_conversation_history(history: List[Dict[str, str]]) -> str:
    """Format the conversation history into a string."""
    if not history:
        return "No previous conversation."
    
    formatted = []
    for msg in history:
        speaker = msg.get("speaker", "unknown").title()
        text = msg.get("text", "")
        formatted.append(f"{speaker}: {text}")
    
    return "\n".join(formatted)

def format_feedback(feedback: Dict) -> str:
    """Format the feedback dictionary into a string."""
    if not feedback:
        return "No feedback available."
    
    return feedback.get("analysis", "No analysis available.")

def simulate_student_turn(conversation_history: List[Dict[str, str]]) -> str:
    """Simulate the student's turn in the conversation."""
    # Format conversation history
    history_text = format_conversation_history(conversation_history)
    
    # Generate prompt
    prompt = STUDENT_PROMPT_TEMPLATE.format(
        student_name=STUDENT_NAME,
        educator_name=EDUCATOR_NAME,
        conversation_history=history_text
    )
    
    # Get response from model
    response = together.chat.completions.create(
        model=STUDENT_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content.strip()

def simulate_educator_turn(conversation_history: List[Dict[str, str]], feedback: Optional[Dict] = None) -> str:
    """Simulate the educator's turn in the conversation."""
    # Format conversation history
    history_text = format_conversation_history(conversation_history)
    
    # Format feedback
    feedback_text = format_feedback(feedback) if feedback else "No previous feedback available."
    
    # Generate prompt
    prompt = EDUCATOR_PROMPT_TEMPLATE.format(
        educator_name=EDUCATOR_NAME,
        student_name=STUDENT_NAME,
        conversation_history=history_text,
        feedback=feedback_text
    )
    
    # Get response from model
    response = together.chat.completions.create(
        model=EDUCATOR_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.7,
        top_k=50,
        top_p=0.7,
        repetition_penalty=1.1
    )
    
    return response.choices[0].message.content.strip()

def get_mini_ai_feedback(conversation_history: List[Dict[str, str]]) -> Dict:
    """Get feedback from the mini AI about the conversation."""
    # Format conversation history
    history_text = format_conversation_history(conversation_history)
    
    # Generate prompt
    prompt = FEEDBACK_PROMPT_TEMPLATE.format(conversation=history_text)
    
    # Get response from model
    response = together.chat.completions.create(
        model=FEEDBACK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.7,
        top_k=50,
        top_p=0.7,
        repetition_penalty=1.1
    )
    
    analysis = response.choices[0].message.content.strip()
    
    return {
        "analysis": analysis,
        "timestamp": time.time()
    } 
