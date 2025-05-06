#!/usr/bin/env python
"""
Simple HTTP Server for CORS Testing
"""
import http.server
import socketserver
import webbrowser
import threading
import time
import os

# Default port for the server
PORT = 5175

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to avoid issues when loading resources
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def open_browser():
    # Wait a moment for the server to start
    time.sleep(1)
    url = f'http://localhost:{PORT}/simple_cors_test.html'
    print(f"Opening browser to: {url}")
    webbrowser.open(url)

if __name__ == '__main__':
    print(f"Starting simple HTTP server on port {PORT}...")
    print(f"Press Ctrl+C to stop the server")
    
    # Create a server
    with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        
        # Start browser in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the server
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.") 