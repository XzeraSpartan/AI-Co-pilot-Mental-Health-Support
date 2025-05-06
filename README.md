# AI Co-Pilot Mental Health Support

A backend system that simulates live conversations between students and educators with real-time AI-generated feedback for mental health support scenarios.

## Project Overview

This project implements a backend service that:

1. Simulates conversations between a student seeking mental health support and an educator providing guidance
2. Provides real-time feedback to educators with suggestions to improve their responses
3. Makes all conversation data available through a RESTful API for frontend integration
4. Records and provides complete conversation transcripts

The system functions as an educational tool to demonstrate how AI can support mental health conversations in educational settings.

## Project Structure

```
.
├── docs/                  # Documentation files
├── src/                   # Source code
│   ├── api/               # API server and endpoints
│   ├── config/            # Configuration files
│   ├── models/            # AI models and data structures
│   ├── tests/             # Test scripts and utilities
│   └── utils/             # Utility functions
├── debug_tools/           # Debugging and development tools
├── logs/                  # Log files
├── main.py                # Main entry point script
└── requirements.txt       # Python dependencies
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-copilot-mental-health.git
cd ai-copilot-mental-health

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

The easiest way to run the server is using the main script:

```bash
# Run both the backend server and CORS proxy
python main.py

# Run only the backend server
python main.py --server

# Run only the CORS proxy
python main.py --proxy

# Run with custom ports
python main.py --server-port 5060 --proxy-port 5070
```

## API Documentation

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/api/conversations` | POST | Start a new conversation |
| `/api/conversations` | GET | List all active conversations |
| `/api/conversations/{id}` | GET | Get full conversation details |
| `/api/conversations/{id}` | DELETE | End a conversation |
| `/api/conversations/{id}/events` | GET | Get conversation events (long polling) |
| `/api/conversations/{id}/transcript` | GET | Get conversation transcript |

For frontend integration, please use the proxy URL (`http://127.0.0.1:5070`) to avoid CORS issues.

## Development

### Debug Tools

- `debug_tools/cors_proxy.py`: CORS proxy for frontend development
- `debug_tools/connection_tester.py`: Test connectivity to the backend
- `debug_tools/simple_cors_test.html`: Simple HTML test page for CORS issues

### Testing

```bash
# Run tests
python -m src.tests.test_backend
```

## Configuration

- Set `USE_PLACEHOLDERS=true` to use predefined responses without calling the AI API
- Set `TOGETHER_API_KEY` with your API key to enable real AI-generated responses
- Set `CORS_ALLOW_ORIGINS` to specify allowed origins for CORS (comma-separated, default: '*')
- Modify AI models and prompts in `src/models/ai_agents.py`

## License

[MIT License](LICENSE) 