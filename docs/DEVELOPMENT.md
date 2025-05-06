# Development Guide

This document provides guidance for developers working on the AI Co-Pilot Mental Health Support project.

## Project Structure

The project has been reorganized to follow a more maintainable structure:

```
.
├── docs/                  # Documentation files
├── src/                   # Source code
│   ├── api/               # API server and endpoints
│   │   ├── server.py      # Main backend server (from simplified_server.py)
│   │   ├── app.py         # Flask application setup
│   │   └── extensions.py  # Flask extensions
│   ├── config/            # Configuration files
│   │   └── config.py      # Environment and application config
│   ├── models/            # AI models and data structures
│   │   ├── ai_agents.py   # AI agent implementations
│   │   ├── data_models.py # Data models
│   │   └── simulation_engine.py # Conversation simulation engine
│   ├── tests/             # Test scripts and utilities
│   │   ├── test_client.py # Client for testing the API
│   │   └── test_backend.py # Backend tests
│   └── utils/             # Utility functions
├── debug_tools/           # Debugging and development tools
│   ├── cors_proxy.py      # CORS proxy for frontend development
│   ├── connection_tester.py # Test connectivity to backend
│   └── *.html             # HTML test files
├── logs/                  # Log files
├── main.py                # Main entry point script
└── requirements.txt       # Python dependencies
```

## Development Workflow

### Running the Server

The new project structure includes a central `main.py` script that handles starting both the backend server and the CORS proxy in a single command:

```bash
# Run both backend and proxy
python main.py

# Run only the backend server
python main.py --server

# Run only the CORS proxy
python main.py --proxy

# Run with custom ports
python main.py --server-port 5060 --proxy-port 5070
```

### Frontend Integration

For frontend developers, connect to the server through the CORS proxy:

```javascript
// Use this URL in your frontend code
const API_URL = 'http://127.0.0.1:5070';
```

The proxy eliminates CORS issues while forwarding requests to the actual backend server.

### Debugging

Debug tools are located in the `debug_tools/` directory:

1. `connection_tester.py` - Tests connectivity to the backend server
2. `check_frontend_cors.py` - Tests CORS issues from a frontend perspective
3. `simple_cors_test.html` - Simple HTML page to test API calls

Example usage:
```bash
# Test backend connectivity
python debug_tools/connection_tester.py

# Start a CORS test server
python debug_tools/check_frontend_cors.py
```

### Adding New Features

1. **Backend API Endpoints**:
   - Add new endpoints to `src/api/server.py`
   - Follow the existing patterns for error handling and response formatting

2. **AI Agent Behavior**:
   - Modify prompts and responses in `src/models/ai_agents.py`
   - Test changes using the test client: `python src/tests/test_client.py`

3. **Configuration**:
   - Add new configuration options to `src/config/config.py`
   - Access them in code through the config module

## Common Issues

### CORS Issues

If you're experiencing CORS issues when connecting from a frontend:

1. Ensure both the backend server and CORS proxy are running:
   ```bash
   python main.py
   ```

2. Check that your frontend is using the proxy URL:
   ```javascript
   const API_URL = 'http://127.0.0.1:5070';
   ```

3. If still having issues, try the connection tester:
   ```bash
   python debug_tools/connection_tester.py
   ```

### Webcontainer/Cloud IDE Issues

When developing in cloud environments (like Stackblitz, CodeSandbox, etc.):

1. The backend needs to be accessible over the internet
2. Use a service like ngrok to expose your local server:
   ```bash
   ngrok http 5070
   ```
3. Update your frontend code to use the ngrok URL

## Contributing

1. Create a feature branch from main
2. Make your changes
3. Run tests to ensure your changes don't break existing functionality
4. Submit a pull request with a clear description of your changes 