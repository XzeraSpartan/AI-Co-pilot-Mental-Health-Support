#!/usr/bin/env python
"""
CORS Checker for AI Co-Pilot Frontend

This script helps debug CORS issues by:
1. Starting a test server on port 5173 (typical Vite port)
2. Making requests to your backend and showing detailed error information
3. Suggesting fixes based on observed behavior
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time

# HTML template for the CORS test page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Frontend CORS Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        .output {
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            min-height: 100px;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        button {
            margin: 10px 5px 10px 0;
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .error {
            color: #D8000C;
            background-color: #FFBABA;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .success {
            color: #4F8A10;
            background-color: #DFF2BF;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        #portInput {
            padding: 8px;
            width: 80px;
        }
    </style>
</head>
<body>
    <h1>AI Co-Pilot Frontend CORS Tester</h1>
    <p>This tool helps diagnose CORS issues between your frontend and backend. It simulates requests from port 5173 (Vite's default) to your backend server.</p>
    
    <div>
        <label for="portInput">Backend Port:</label>
        <input type="number" id="portInput" value="5060">
        <button id="updatePort">Update Port</button>
    </div>
    
    <div>
        <button id="healthCheck">Test Health Check</button>
        <button id="startConversation">Start Conversation</button>
        <button id="fetchEvents">Fetch Events</button>
        <button id="corsTest">Test CORS Headers</button>
    </div>
    
    <div class="output" id="output">Results will appear here...</div>
    <div id="corsAnalysis"></div>

    <script>
        let API_URL = 'http://127.0.0.1:5060';
        let conversationId = null;
        const output = document.getElementById('output');
        const corsAnalysis = document.getElementById('corsAnalysis');
        
        // Update port
        document.getElementById('updatePort').addEventListener('click', () => {
            const port = document.getElementById('portInput').value;
            API_URL = `http://127.0.0.1:${port}`;
            output.textContent = `API URL updated to: ${API_URL}`;
        });

        // Test health check endpoint
        document.getElementById('healthCheck').addEventListener('click', async () => {
            corsAnalysis.innerHTML = '';
            try {
                output.textContent = 'Testing health check endpoint...\n';
                const response = await fetch(`${API_URL}/health`);
                const data = await response.json();
                output.textContent += `Status: ${response.status}\n`;
                output.textContent += `Headers: ${JSON.stringify(Object.fromEntries([...response.headers]), null, 2)}\n`;
                output.textContent += `Data: ${JSON.stringify(data, null, 2)}`;
                
                // Check for CORS headers
                analyzeHeaders(response.headers);
            } catch (error) {
                output.textContent += `Error: ${error.message}\n`;
                console.error(error);
                analyzeError(error);
            }
        });

        // Test start conversation endpoint
        document.getElementById('startConversation').addEventListener('click', async () => {
            corsAnalysis.innerHTML = '';
            try {
                output.textContent = 'Starting conversation...\n';
                const response = await fetch(`${API_URL}/api/conversations`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ turns: 3 })
                });
                const data = await response.json();
                conversationId = data.conversation_id;
                output.textContent += `Status: ${response.status}\n`;
                output.textContent += `Headers: ${JSON.stringify(Object.fromEntries([...response.headers]), null, 2)}\n`;
                output.textContent += `Data: ${JSON.stringify(data, null, 2)}`;
                
                // Check for CORS headers
                analyzeHeaders(response.headers);
            } catch (error) {
                output.textContent += `Error: ${error.message}\n`;
                console.error(error);
                analyzeError(error);
            }
        });

        // Test fetch events endpoint
        document.getElementById('fetchEvents').addEventListener('click', async () => {
            corsAnalysis.innerHTML = '';
            if (!conversationId) {
                output.textContent = 'Please start a conversation first!';
                return;
            }
            
            try {
                output.textContent = 'Fetching events...\n';
                const response = await fetch(`${API_URL}/api/conversations/${conversationId}/events?last_index=0`);
                const data = await response.json();
                output.textContent += `Status: ${response.status}\n`;
                output.textContent += `Headers: ${JSON.stringify(Object.fromEntries([...response.headers]), null, 2)}\n`;
                output.textContent += `Data: ${JSON.stringify(data, null, 2)}`;
                
                // Check for CORS headers
                analyzeHeaders(response.headers);
            } catch (error) {
                output.textContent += `Error: ${error.message}\n`;
                console.error(error);
                analyzeError(error);
            }
        });

        // Test CORS headers specifically
        document.getElementById('corsTest').addEventListener('click', async () => {
            corsAnalysis.innerHTML = '';
            try {
                output.textContent = 'Testing CORS with preflight request...\n';
                
                // Make preflight request with OPTIONS
                const fetchOptions = {
                    method: 'OPTIONS',
                    headers: {
                        'Origin': window.location.origin,
                        'Access-Control-Request-Method': 'POST',
                        'Access-Control-Request-Headers': 'Content-Type, X-Custom-Header'
                    }
                };
                
                // Log the preflight request
                output.textContent += `Preflight Options Request to: ${API_URL}/api/conversations\n`;
                output.textContent += `Headers: ${JSON.stringify(fetchOptions.headers, null, 2)}\n\n`;
                
                // Manually send preflight
                try {
                    const response = await fetch(`${API_URL}/api/conversations`, fetchOptions);
                    output.textContent += `Preflight Response Status: ${response.status}\n`;
                    output.textContent += `Preflight Headers: ${JSON.stringify(Object.fromEntries([...response.headers]), null, 2)}\n\n`;
                } catch (error) {
                    output.textContent += `Preflight Error: ${error.message}\n\n`;
                }
                
                // Now try the actual request
                output.textContent += `Now trying actual POST request...\n`;
                const actualResponse = await fetch(`${API_URL}/api/conversations`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Custom-Header': 'test-value'
                    },
                    body: JSON.stringify({ turns: 1 })
                });
                
                const data = await actualResponse.json();
                output.textContent += `Actual Response Status: ${actualResponse.status}\n`;
                output.textContent += `Actual Headers: ${JSON.stringify(Object.fromEntries([...actualResponse.headers]), null, 2)}\n`;
                output.textContent += `Data: ${JSON.stringify(data, null, 2)}`;
                
                // Check for CORS headers
                analyzeHeaders(actualResponse.headers);
            } catch (error) {
                output.textContent += `Error: ${error.message}\n`;
                console.error(error);
                analyzeError(error);
            }
        });
        
        // Helper function to analyze headers
        function analyzeHeaders(headers) {
            const corsIssues = [];
            const corsSuccess = [];
            
            // Check Access-Control-Allow-Origin
            const allowOrigin = headers.get('Access-Control-Allow-Origin');
            if (allowOrigin) {
                if (allowOrigin === '*' || allowOrigin === window.location.origin) {
                    corsSuccess.push(`✅ Access-Control-Allow-Origin header set correctly to "${allowOrigin}"`);
                } else {
                    corsIssues.push(`⚠️ Access-Control-Allow-Origin is set to "${allowOrigin}" but should be "${window.location.origin}" or "*"`);
                }
            } else {
                corsIssues.push('❌ Missing Access-Control-Allow-Origin header');
            }
            
            // Check for other important CORS headers
            if (headers.get('Access-Control-Allow-Methods')) {
                corsSuccess.push(`✅ Access-Control-Allow-Methods header is present`);
            } else {
                corsIssues.push('⚠️ Missing Access-Control-Allow-Methods header');
            }
            
            if (headers.get('Access-Control-Allow-Headers')) {
                corsSuccess.push(`✅ Access-Control-Allow-Headers header is present`);
            } else {
                corsIssues.push('⚠️ Missing Access-Control-Allow-Headers header');
            }
            
            // Display the analysis
            let analysisHTML = '';
            if (corsIssues.length > 0) {
                analysisHTML += '<div class="error"><h3>CORS Issues Found:</h3><ul>';
                corsIssues.forEach(issue => {
                    analysisHTML += `<li>${issue}</li>`;
                });
                analysisHTML += '</ul></div>';
            }
            
            if (corsSuccess.length > 0) {
                analysisHTML += '<div class="success"><h3>CORS Success:</h3><ul>';
                corsSuccess.forEach(success => {
                    analysisHTML += `<li>${success}</li>`;
                });
                analysisHTML += '</ul></div>';
            }
            
            corsAnalysis.innerHTML = analysisHTML;
        }
        
        // Helper function to analyze errors
        function analyzeError(error) {
            let analysisHTML = '<div class="error"><h3>Error Analysis:</h3>';
            
            if (error.message.includes('Failed to fetch')) {
                analysisHTML += '<p>The "Failed to fetch" error usually indicates one of the following issues:</p><ul>';
                analysisHTML += '<li>The backend server is not running or not accessible at the specified URL</li>';
                analysisHTML += '<li>A CORS policy is blocking the request (most likely)</li>';
                analysisHTML += '<li>Network connectivity issues between client and server</li>';
                analysisHTML += '</ul>';
                
                analysisHTML += '<p><strong>Recommended actions:</strong></p><ul>';
                analysisHTML += `<li>Verify the backend is running at ${API_URL}</li>`;
                analysisHTML += '<li>Check that your backend has the following CORS headers:</li>';
                analysisHTML += '<ul>';
                analysisHTML += `<li>Access-Control-Allow-Origin: "${window.location.origin}" or "*"</li>`;
                analysisHTML += '<li>Access-Control-Allow-Methods: "GET, POST, DELETE, OPTIONS"</li>';
                analysisHTML += '<li>Access-Control-Allow-Headers: "Content-Type, Authorization, X-Custom-Header"</li>';
                analysisHTML += '</ul>';
                analysisHTML += '<li>Try using curl to test if the server is responding correctly</li>';
                analysisHTML += '</ul>';
            } else {
                analysisHTML += `<p>${error.message}</p>`;
            }
            
            analysisHTML += '</div>';
            corsAnalysis.innerHTML = analysisHTML;
        }
    </script>
</body>
</html>
"""

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        else:
            super().do_GET()

def start_server(port=5173):
    handler = CORSRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🚀 Server running at http://localhost:{port}")
            print("🔎 Use this to test CORS issues from a frontend perspective")
            print("ℹ️  Press CTRL+C to stop the server")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"⚠️  Port {port} is already in use.")
            print("ℹ️  This might mean your Vite server is already running, which is good!")
            print(f"🌐 You can navigate to http://localhost:{port}/check_frontend_cors.html if you've placed this file there")
            print("or try a different port with: python check_frontend_cors.py <port>")
            return False
        else:
            raise
    return True

def open_browser(port=5173):
    # Wait a moment for the server to start
    time.sleep(1)
    webbrowser.open(f'http://localhost:{port}')

if __name__ == "__main__":
    port = 5173
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port. Using default port 5173.")
    
    print("=" * 60)
    print("🔄 CORS Checker for AI Co-Pilot Frontend")
    print("=" * 60)
    print("This tool will help diagnose CORS issues between your frontend and backend")
    
    browser_thread = threading.Thread(target=open_browser, args=(port,))
    browser_thread.daemon = True
    browser_thread.start()
    
    if start_server(port):
        pass  # Server running until Ctrl+C 