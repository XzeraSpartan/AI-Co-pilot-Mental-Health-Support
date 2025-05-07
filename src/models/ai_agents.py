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

def get_mini_ai_feedback(conversation_history: List[Dict[str, str]]) -> Dict:
    """Get feedback and suggestions from the mini AI about the conversation."""
    # Format conversation history
    history_text = format_conversation_history(conversation_history)
    
    # Generate prompt
    prompt = """Analyze the following conversation between a student and counselor.
Focus on:
1. Student's emotional state and key concerns
2. Potential risk factors
3. Suggested next questions for the counselor

Provide:
1. A brief analysis of the student's current state
2. Three specific, open-ended questions the counselor could ask next
3. Any warning signs or concerns to address

Conversation:
{conversation}

Analysis:"""
    
    # Get response from model
    response = together.chat.completions.create(
        model=FEEDBACK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
        top_k=50,
        top_p=0.7,
        repetition_penalty=1.1
    )
    
    analysis = response.choices[0].message.content.strip()
    
    # Parse the response to extract questions
    questions = []
    lines = analysis.split('\n')
    for line in lines:
        if line.strip().startswith(('1.', '2.', '3.')):
            questions.append(line.strip()[2:].strip())
    
    return {
        "analysis": analysis,
        "suggested_questions": questions[:3],  # Ensure we only return 3 questions
        "timestamp": time.time()
    } 
