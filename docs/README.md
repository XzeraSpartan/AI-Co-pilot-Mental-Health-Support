# AI Co-Pilot for Mental Health Support

A backend system that simulates live conversations between students and educators with real-time AI-generated feedback for mental health support scenarios.

## Project Overview

This project implements a backend service that:

1. Simulates conversations between a student seeking mental health support and an educator providing guidance
2. Provides real-time feedback to educators with suggestions to improve their responses
3. Makes all conversation data available through a RESTful API for frontend integration
4. Records and provides complete conversation transcripts

The system functions as an educational tool to demonstrate how AI can support mental health conversations in educational settings.

## Key Components

### 1. AI Agents
- **Student AI**: Simulates a student seeking mental health support
- **Educator AI**: Simulates an educator providing guidance and support 
- **Mini AI**: Provides real-time feedback and suggestions to the educator

### 2. Backend Server
- **Flask API**: Provides RESTful endpoints for managing and monitoring conversations
- **WebSocket Support**: Enables real-time updates via long-polling
- **Conversation Management**: Handles conversation state, persistence, and transcript generation

## API Documentation

### Endpoints

#### Start a Conversation
```
POST /api/conversations
```
Creates a new simulated conversation.

**Request Body:**
```json
{
  "turns": 10  // Optional, default is 5
}
```

**Response:**
```json
{
  "status": "success",
  "conversation_id": "uuid-string",
  "message": "Conversation started successfully"
}
```

#### Get Conversation Events
```
GET /api/conversations/{conversation_id}/events?last_index={index}
```
Long-polling endpoint to receive new events.

**Response:**
```json
{
  "status": "success",
  "events": [
    {
      "conversation_id": "uuid-string",
      "type": "typing",
      "speaker": "student",
      "name": "Alex",
      "timestamp": "2023-05-05T12:34:56.789"
    },
    {
      "conversation_id": "uuid-string",
      "type": "message",
      "speaker": "student",
      "name": "Alex",
      "text": "Hi Ms. Morgan...",
      "timestamp": "2023-05-05T12:34:59.123"
    },
    {
      "conversation_id": "uuid-string",
      "type": "feedback",
      "feedback": {
        "analysis": "The student is expressing...",
        "suggestions": ["Validate their feelings", "..."]
      },
      "timestamp": "2023-05-05T12:35:00.456"
    }
  ],
  "last_index": 3
}
```

#### Get Full Conversation
```
GET /api/conversations/{conversation_id}
```
Retrieve the complete conversation with all events and transcript.

#### Get Conversation Transcript
```
GET /api/conversations/{conversation_id}/transcript
```
Get just the formatted transcript of the conversation.

#### List All Conversations
```
GET /api/conversations
```
Get a list of all active conversations with metadata.

#### End Conversation
```
DELETE /api/conversations/{conversation_id}
```
End the conversation and clean up server resources.

#### Health Check
```
GET /health
```
Simple health check endpoint.

## Installation

### Prerequisites
- Python 3.9+ 
- pip

### Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-copilot-mental-health.git
cd ai-copilot-mental-health
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set API key for Together AI (optional for real AI responses):
```bash
export TOGETHER_API_KEY=your_api_key_here
```

## Running the Backend

Start the backend server:
```bash
python simplified_server.py
```

The server will start on http://127.0.0.1:5060 by default.

## Testing

Run the test client to simulate interaction with the backend:
```bash
python test_client.py
```

Or use the convenience script that sets up the environment and runs both server and client:
```bash
./run_test.sh
```

## Configuration

- Set `USE_PLACEHOLDERS=true` to use predefined responses without calling the AI API
- Set `TOGETHER_API_KEY` with your API key to enable real AI-generated responses
- Set `CORS_ALLOW_ORIGINS` to specify allowed origins for CORS (comma-separated, default: '*')
- Modify AI models and prompts in `ai_agents.py`
- Change server port in `simplified_server.py`

## Real-World Implementation

For production use, consider:
1. Adding user authentication and session management
2. Using a proper database for conversation persistence
3. Implementing rate limiting and API security measures
4. Deploying with a production WSGI server like Gunicorn
5. Adding automated tests for API endpoints

## License

[MIT License](LICENSE)

## Credits

- Together AI for providing the API for language models
- Character names and conversation scenarios are fictional 