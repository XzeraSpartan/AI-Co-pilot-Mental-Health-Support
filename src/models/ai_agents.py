import os
import random
import together
import sys
import logging

# Add parent directory to path so we can import from src.config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import *

# Set up logging
logger = logging.getLogger(__name__)

# Set the Together API key from configuration
together.api_key = TOGETHER_API_KEY

# Define character names
STUDENT_NAME = STUDENT_NAME_CONFIG
EDUCATOR_NAME = EDUCATOR_NAME_CONFIG

# Placeholder function to quickly test without API call
def use_placeholder_responses():
    """Check if we should use placeholder responses instead of API calls"""
    # Use the configuration setting
    return USE_PLACEHOLDERS

def format_conversation_for_prompt(conversation_history):
    """Format the conversation history for the LLM prompt"""
    formatted_text = ""
    for message in conversation_history:
        prefix = f"{STUDENT_NAME}: " if message["speaker"] == "student" else f"{EDUCATOR_NAME}: "
        formatted_text += prefix + message["text"] + "\n\n"
    return formatted_text

def simulate_student_turn(conversation_history):
    """Generate a student response using Together AI."""
    if use_placeholder_responses():
        # Use placeholders for testing
        placeholders = [
            f"Hi {EDUCATOR_NAME}. I've been feeling really overwhelmed with school lately. I don't know who else to talk to.",
            "It's just... I have three big exams next week, and I'm also trying to keep up with the debate team. I barely slept last night.",
            "My parents expect me to get all A's this semester. They don't understand how much pressure I'm under. Sometimes I feel like I can't breathe.",
            "I'm worried I'll let everyone down. My friends, my parents, my teachers... I'm trying my best but it doesn't feel like enough.",
            "I never thought about it that way. Maybe I am being too hard on myself."
        ]
        turn_number = len([m for m in conversation_history if m["speaker"] == "student"])
        if turn_number < len(placeholders):
            return placeholders[turn_number]
        return f"Thank you for listening, {EDUCATOR_NAME}. I feel a bit better now. I'll try what you suggested."
        
    # Real API call - THIS PART IS JUST FOR REFERENCE AND WILL NOT BE USED IN DEMO MODE
    formatted_conv = format_conversation_for_prompt(conversation_history)
    
    student_prompt = f"""You are simulating {STUDENT_NAME}, a high school student seeking mental health support from {EDUCATOR_NAME}, a school counselor.
    
Your character:
- You are a 16-year-old student dealing with stress, anxiety, and academic pressure
- You are articulate but sometimes struggle to express your feelings
- You speak like a teenager, using natural conversational language
- You respond directly to questions from {EDUCATOR_NAME}
- You are genuinely seeking help and willing to try suggestions

Important: If {EDUCATOR_NAME} gives advice that seems helpful, show signs of feeling better. The conversation should progress toward resolution.

Always respond as {STUDENT_NAME}, without any meta-commentary. Respond in 1-3 sentences, as a teenager would speak.

Conversation history:
{formatted_conv}

{STUDENT_NAME}: """
    
    try:
        logger.debug(f"Calling Together API for student response")
        response = together.Complete.create(
            prompt=student_prompt,
            model=STUDENT_MODEL,
            max_tokens=150,
            temperature=0.7,
            top_p=0.8,
            top_k=50
        )
        
        # Extract just the student's response
        return response["output"]["choices"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Error calling Together AI: {e}", exc_info=True)
        return "I'm sorry, I'm having trouble expressing myself right now."

def simulate_educator_turn(conversation_history, feedback=None):
    """Generate an educator response using Together AI, incorporating feedback if available."""
    if use_placeholder_responses():
        # Use placeholders for testing
        educator_responses = [
            f"Hello {STUDENT_NAME}. I'm glad you came to talk with me today. Can you tell me more about what's been making you feel overwhelmed?",
            "That's a lot to handle at once. Three exams plus debate team would be challenging for anyone. How have you been trying to manage your time so far?",
            "It sounds like you're feeling a lot of pressure from your parents' expectations. Have you tried talking to them about how you feel?",
            f"It's really common to feel that way, {STUDENT_NAME}. But remember that doing your best is all anyone can ask of you. What would make you feel successful right now?",
            "You know, recognizing when we're being too hard on ourselves is an important first step. What's one small thing you could do tonight to give yourself a break?",
            f"I'm happy to hear that perspective shift, {STUDENT_NAME}. You're making great progress just by recognizing these patterns. Would it help to create a plan for tackling these exams one at a time?",
            f"I'm here for you, {STUDENT_NAME}. Would you like us to work on some concrete strategies for managing your workload and talking to your parents?",
            "You're handling this very maturely. Let's work together on breaking down these big challenges into smaller, more manageable steps. How does that sound?",
            f"I'm really proud of how you're approaching this, {STUDENT_NAME}. Remember you can always come back if you need more support or just want to talk.",
            f"That's great to hear, {STUDENT_NAME}. Remember that my door is always open if you need to talk again."
        ]
        
        turn_number = len([m for m in conversation_history if m["speaker"] == "educator"])
        if turn_number < len(educator_responses):
            return educator_responses[turn_number]
        return f"I'm glad we had this conversation today, {STUDENT_NAME}. Remember, you can always come talk to me whenever you need support."
    
    # Real API call - THIS PART IS JUST FOR REFERENCE AND WILL NOT BE USED IN DEMO MODE
    formatted_conv = format_conversation_for_prompt(conversation_history)
    
    # Add a system prompt for the educator
    educator_prompt = f"""You are simulating {EDUCATOR_NAME}, an experienced and empathetic school counselor providing mental health support to {STUDENT_NAME}, a student.

Your character:
- You are warm, supportive, and skilled at helping students with mental health challenges
- You use evidence-based techniques like active listening, validation, and solution-focused approaches
- You ask thoughtful questions to understand root issues
- You provide practical strategies tailored to {STUDENT_NAME}'s specific struggles
- Your goal is to help resolve {STUDENT_NAME}'s issues by the end of the conversation

Conversation approach:
1. Listen and validate {STUDENT_NAME}'s feelings
2. Ask clarifying questions to understand the situation
3. Offer specific, actionable advice
4. Check in about how {STUDENT_NAME} is feeling about the suggestions
5. Work toward a resolution that leaves {STUDENT_NAME} feeling better

"""

    # Incorporate Mini AI feedback if available
    if feedback:
        educator_prompt += f"""
For this response, focus on these insights:
Analysis: {feedback.get('analysis', '')}
Suggested approaches: {', '.join(feedback.get('suggestions', []))}
"""

    educator_prompt += f"""
Conversation history:
{formatted_conv}

{EDUCATOR_NAME}: """
    
    try:
        logger.debug(f"Calling Together API for educator response")
        response = together.Complete.create(
            prompt=educator_prompt,
            model=EDUCATOR_MODEL,
            max_tokens=200,
            temperature=0.7,
            top_p=0.8,
            top_k=50
        )
        
        # Extract just the educator's response
        return response["output"]["choices"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Error calling Together AI: {e}", exc_info=True)
        return "I'm listening. Can you tell me more about how you're feeling?"

def get_mini_ai_feedback(conversation_history):
    """Generate feedback using Together AI."""
    # Find the last student message
    last_student_message = next((m["text"] for m in reversed(conversation_history) if m["speaker"] == "student"), None)
    
    if not last_student_message:
        return {
            "analysis": "Not enough context to provide analysis.",
            "suggestions": ["Ask open-ended questions to understand the student's situation."]
        }
    
    if use_placeholder_responses():
        # Use placeholders for testing
        analyses = [
            "The student is expressing feelings of being overwhelmed with academic and extracurricular responsibilities.",
            "The student is experiencing anxiety related to parental expectations and pressure to perform.",
            "The student is showing signs of burnout and stress from trying to meet everyone's expectations.",
            "The student appears to be experiencing self-doubt and fear of disappointing others.",
            "The student is starting to show openness to reframing their perspective on the situation."
        ]
        
        suggestions_list = [
            ["Use reflective listening to validate their feelings", "Explore specific stressors in more detail", "Normalize their experience"],
            ["Help identify thought patterns contributing to anxiety", "Teach simple breathing techniques", "Discuss strategies for communicating with parents"],
            ["Acknowledge the difficulty of balancing multiple responsibilities", "Explore priority-setting", "Introduce stress management techniques"],
            ["Validate their feelings of inadequacy", "Challenge perfectionist thinking", "Explore strengths and achievements"],
            ["Reinforce the shift in perspective", "Develop an action plan", "Discuss ongoing support options"]
        ]
        
        turn_number = len([m for m in conversation_history if m["speaker"] == "student"]) - 1
        turn_number = max(0, min(turn_number, len(analyses) - 1))
        
        return {
            "analysis": analyses[turn_number],
            "suggestions": suggestions_list[turn_number]
        }
    
    # Get the full conversation history context
    conversation_context = "\n".join([f"{'Student' if m['speaker'] == 'student' else 'Educator'}: {m['text']}" for m in conversation_history])
    
    mini_ai_prompt = f"""You are a specialized AI assistant for mental health educators. Your job is to analyze student messages and provide real-time guidance to help the educator respond effectively.

Latest student message: "{last_student_message}"

Full conversation context:
{conversation_context}

Provide:
1) A brief analysis of what the student might be feeling and the underlying issues
2) 2-3 specific techniques or approaches the educator could use in their next response

Format your response with clearly labeled sections for "Analysis:" and "Suggestions:".
"""
    
    try:
        # Real API call
        logger.debug(f"Calling Together API for Mini AI feedback")
        response = together.Complete.create(
            prompt=mini_ai_prompt,
            model=MINI_AI_MODEL,
            max_tokens=250,
            temperature=0.7,
            top_p=0.9
        )
        
        # Parse the response for analysis/suggestions
        content = response["output"]["choices"][0]["text"].strip()
        
        # Better parsing to extract analysis and suggestions sections
        analysis = ""
        suggestions = []
        
        if "Analysis:" in content:
            parts = content.split("Analysis:")
            if len(parts) > 1:
                analysis_section = parts[1].split("Suggestions:")[0].strip()
                analysis = analysis_section
        
        if "Suggestions:" in content:
            suggestions_section = content.split("Suggestions:")[1].strip()
            suggestion_lines = [line.strip('-• ') for line in suggestions_section.split('\n') if line.strip()]
            suggestions = [s for s in suggestion_lines if s]
        
        # Fallback if parsing fails
        if not analysis:
            analysis = content.split('\n')[0] if '\n' in content else content
        
        if not suggestions:
            suggestions = ["Validate the student's feelings", "Ask about specific stressors", "Offer coping strategies"]
        
        return {
            "analysis": analysis,
            "suggestions": suggestions[:3]
        }
    except Exception as e:
        logger.error(f"Error calling Together AI: {e}", exc_info=True)
        return {
            "analysis": "Unable to analyze the message due to API error.",
            "suggestions": ["Listen actively", "Ask clarifying questions", "Offer reassurance"]
        } 