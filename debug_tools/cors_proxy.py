#!/usr/bin/env python
"""
CORS Proxy Server

This script creates a simple proxy server that forwards requests to the backend
while adding appropriate CORS headers. This effectively bypasses browser CORS
restrictions by having both frontend and "backend" on the same origin.
"""

from flask import Flask, request, Response, jsonify
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "http://127.0.0.1:5060"  # The actual backend server
PROXY_PORT = 5070  # Port for this proxy server

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    """Home page with instructions."""
    return """
    <html>
    <head>
        <title>CORS Proxy for AI Co-Pilot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            pre { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
            .note { background-color: #fff3cd; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>CORS Proxy for AI Co-Pilot</h1>
        <p>This server proxies requests to the backend server at <code>{backend_url}</code>, 
        adding appropriate CORS headers to bypass browser restrictions.</p>
        
        <div class="note">
            <p><strong>To use this proxy:</strong> Simply replace <code>{backend_url}</code> with <code>http://localhost:{proxy_port}</code> in your frontend code.</p>
        </div>
        
        <h2>Available Endpoints:</h2>
        <p>All endpoints from the original backend are available through this proxy.</p>
        <p>For example:</p>
        <ul>
            <li>Health Check: <a href="/health">/health</a></li>
            <li>Start Conversation: POST to <code>/api/conversations</code></li>
        </ul>
        
        <h2>For Frontend Developers:</h2>
        <pre>// Change your API URL to:
const API_URL = 'http://localhost:{proxy_port}';</pre>
    </body>
    </html>
    """.format(backend_url=BACKEND_URL, proxy_port=PROXY_PORT)

@app.route('/<path:path>', methods=['GET', 'POST', 'DELETE', 'PUT', 'OPTIONS'])
def proxy(path):
    """Proxy all requests to the backend server."""
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE, PUT, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, X-Custom-Header')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    # Forward the request to the backend
    url = f"{BACKEND_URL}/{path}"
    logger.info(f"Proxying {request.method} request to {url}")
    
    try:
        # Copy request headers
        headers = {key: value for (key, value) in request.headers if key != 'Host'}
        
        # Forward the request
        if request.method == 'GET':
            resp = requests.get(
                url, 
                headers=headers,
                params=request.args,
                cookies=request.cookies,
                timeout=30
            )
        elif request.method == 'POST':
            resp = requests.post(
                url, 
                headers=headers,
                data=request.get_data(),
                params=request.args,
                cookies=request.cookies,
                timeout=30
            )
        elif request.method == 'DELETE':
            resp = requests.delete(
                url, 
                headers=headers,
                cookies=request.cookies,
                timeout=30
            )
        else:
            resp = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.get_data(),
                params=request.args,
                cookies=request.cookies,
                timeout=30
            )
        
        # Create response
        response = Response(resp.content, resp.status_code)
        
        # Copy response headers
        for key, value in resp.headers.items():
            if key.lower() not in ('access-control-allow-origin', 'access-control-allow-methods', 
                                  'access-control-allow-headers', 'access-control-allow-credentials'):
                response.headers[key] = value
        
        # Add CORS headers
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE, PUT, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, X-Custom-Header')
        
        return response
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying request: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'proxy_error': True
        }), 500

if __name__ == '__main__':
    logger.info(f"Starting CORS proxy server on port {PROXY_PORT}")
    logger.info(f"Proxying requests to backend at {BACKEND_URL}")
    app.run(host='0.0.0.0', port=PROXY_PORT, debug=True) 