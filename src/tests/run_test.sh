#!/bin/bash

# Ensure virtual environment exists and is activated
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Set environment variable for Together API key
# Replace this with your actual API key or set it in your environment before running
if [ -z "$TOGETHER_API_KEY" ]; then
    echo "Warning: TOGETHER_API_KEY environment variable not set!"
    echo "Using placeholder responses instead..."
    export USE_PLACEHOLDERS=true
else
    export USE_PLACEHOLDERS=false
fi

# Start the server in the background
echo "Starting server..."
python simplified_server.py > server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Run the test client
echo "Running test client..."
python test_client.py

# After test is complete, shut down the server
echo "Test complete. Shutting down server..."
kill $SERVER_PID

# Display location of log files
echo ""
echo "Log files available at:"
echo "- Server log: server.log"
echo "- Client log: client_test.log"

# Deactivate virtual environment
deactivate 