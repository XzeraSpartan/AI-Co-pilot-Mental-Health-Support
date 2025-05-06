#!/usr/bin/env python
"""
Backend Connection Tester

This script checks various connectivity aspects to the backend server to help
diagnose "Failed to fetch" errors in the browser.
"""

import requests
import socket
import subprocess
import sys
import platform
import json
from urllib.parse import urlparse
import time

# Configuration
BACKEND_URL = "http://127.0.0.1:5060"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"
API_ENDPOINT = f"{BACKEND_URL}/api/conversations"

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)

def check_socket_connection(host, port):
    """Test basic TCP socket connection to the host:port."""
    print_header("SOCKET CONNECTION TEST")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"✅ Socket connection to {host}:{port} succeeded")
            return True
        else:
            print(f"❌ Socket connection to {host}:{port} failed (Error: {result})")
            return False
    except Exception as e:
        print(f"❌ Socket connection error: {e}")
        return False
    finally:
        sock.close()

def run_ping_test(host):
    """Test network reachability using ping."""
    print_header("PING TEST")
    ping_param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        subprocess.check_output(["ping", ping_param, "3", host], 
                               stderr=subprocess.STDOUT, 
                               universal_newlines=True)
        print(f"✅ Ping to {host} succeeded")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ping to {host} failed with return code {e.returncode}")
        print(e.output)
        return False
    except Exception as e:
        print(f"❌ Ping test error: {e}")
        return False

def test_http_requests():
    """Test HTTP requests to the backend."""
    print_header("HTTP REQUESTS TEST")
    
    # Test health endpoint with requests
    try:
        print(f"Testing GET {HEALTH_ENDPOINT}")
        start_time = time.time()
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        elapsed = time.time() - start_time
        
        print(f"✅ HTTP GET succeeded in {elapsed:.2f}s (Status code: {response.status_code})")
        print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        
        # Check for CORS headers
        if 'Access-Control-Allow-Origin' in response.headers:
            print("✅ CORS headers found in response")
        else:
            print("⚠️ CORS headers missing from response")
            
    except requests.exceptions.ConnectionError:
        print("❌ HTTP GET failed: Connection error")
        return False
    except requests.exceptions.Timeout:
        print("❌ HTTP GET failed: Timeout")
        return False
    except Exception as e:
        print(f"❌ HTTP GET failed: {e}")
        return False
    
    # Test POST to API endpoint
    try:
        print(f"\nTesting POST {API_ENDPOINT}")
        start_time = time.time()
        response = requests.post(
            API_ENDPOINT, 
            json={"turns": 1}, 
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        elapsed = time.time() - start_time
        
        print(f"✅ HTTP POST succeeded in {elapsed:.2f}s (Status code: {response.status_code})")
        print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        
    except requests.exceptions.ConnectionError:
        print("❌ HTTP POST failed: Connection error")
        return False
    except requests.exceptions.Timeout:
        print("❌ HTTP POST failed: Timeout")
        return False
    except Exception as e:
        print(f"❌ HTTP POST failed: {e}")
        return False
        
    return True

def test_options_request():
    """Test OPTIONS request for CORS preflight."""
    print_header("CORS PREFLIGHT TEST")
    
    try:
        print(f"Testing OPTIONS {API_ENDPOINT}")
        response = requests.options(
            API_ENDPOINT,
            headers={
                "Origin": "http://localhost:5175",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=5
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        
        # Check for CORS headers
        required_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
        
        missing_headers = [h for h in required_headers if h not in response.headers]
        
        if not missing_headers:
            print("✅ All required CORS headers found in OPTIONS response")
        else:
            print(f"⚠️ Missing required CORS headers: {', '.join(missing_headers)}")
            
        return True
    except Exception as e:
        print(f"❌ OPTIONS request failed: {e}")
        return False

def print_recommendations(all_tests_passed):
    """Print recommendations based on test results."""
    print_header("DIAGNOSIS & RECOMMENDATIONS")
    
    if all_tests_passed:
        print("✅ All connection tests passed successfully.")
        print("\nSince server-side tests are successful but browser requests fail:")
        print("1. Browser security settings may be blocking the requests")
        print("2. There might be a browser extension interfering with requests")
        print("3. The browser might not be handling CORS properly")
        
        print("\nTry these solutions:")
        print("- Try a different browser (Firefox, Chrome, Safari)")
        print("- Temporarily disable browser extensions")
        print("- Try running the frontend and backend on the same origin/port")
        print("- Check browser console for more specific error messages")
    else:
        print("❌ Some connection tests failed.")
        print("\nPossible issues:")
        print("1. The backend server may not be running")
        print("2. There might be a firewall blocking connections")
        print("3. The backend might be listening on a different port/interface")
        
        print("\nTry these solutions:")
        print("- Make sure the backend server is running")
        print("- Check if the server is listening on the correct port (5060)")
        print("- Verify there's no firewall blocking connections to port 5060")
        print("- Try changing the server to listen on 0.0.0.0 instead of 127.0.0.1")

if __name__ == "__main__":
    print("Backend Connection Tester")
    print(f"Testing connectivity to {BACKEND_URL}")
    
    # Parse URL to get host and port
    parsed_url = urlparse(BACKEND_URL)
    host = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    
    # Run the tests
    socket_test = check_socket_connection(host, port)
    ping_test = True  # Skip ping for localhost 
    if host != "127.0.0.1" and host != "localhost":
        ping_test = run_ping_test(host)
    http_test = test_http_requests()
    options_test = test_options_request()
    
    all_tests_passed = socket_test and ping_test and http_test and options_test
    print_recommendations(all_tests_passed) 