#!/bin/bash

# This script removes files that have been relocated to the src/ and debug_tools/ directories
# as part of the project reorganization

echo "Removing redundant files from the root directory..."

# Files relocated to src/api/
rm -f simplified_server.py
rm -f app.py
rm -f extensions.py

# Files relocated to src/models/
rm -f ai_agents.py
rm -f simulation_engine.py
rm -f models.py

# Files relocated to src/config/
rm -f config.py

# Files relocated to src/tests/
rm -f test_client.py
rm -f test_backend.py
rm -f run_test.sh
rm -f simple_test.py

# Files relocated to debug_tools/
rm -f cors_proxy.py
rm -f connection_tester.py
rm -f simple_test_server.py
rm -f check_frontend_cors.py
rm -f simple_cors_test.html
rm -f cors_test.html

# Log files (now centralized in logs/)
rm -f backend.log

# Clean up Python cache directories
echo "Removing Python cache directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove empty tools directory
if [ -d "tools" ] && [ ! "$(ls -A tools)" ]; then
    echo "Removing empty tools directory..."
    rmdir tools
fi

echo "Cleanup complete!" 