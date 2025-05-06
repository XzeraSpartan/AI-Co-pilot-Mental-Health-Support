#!/usr/bin/env python
"""
AI Co-Pilot Mental Health Support - Main Entry Script

This script provides a unified entry point to run either the backend server,
the CORS proxy, or both together.
"""

import argparse
import subprocess
import sys
import os
import logging
import time
import signal
import atexit

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/main.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_SERVER_PORT = 5060
DEFAULT_PROXY_PORT = 5070
SERVER_SCRIPT = "src/api/server.py"
PROXY_SCRIPT = "debug_tools/cors_proxy.py"

# Process tracking
processes = []

def signal_handler(sig, frame):
    """Handle termination signals to clean up processes."""
    logger.info("Shutting down all processes...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            process.terminate()
    sys.exit(0)

def cleanup_processes():
    """Ensure all processes are terminated on exit."""
    for process in processes:
        if process.poll() is None:  # If process is still running
            process.terminate()

def run_server(port=DEFAULT_SERVER_PORT):
    """Run the backend server."""
    logger.info(f"Starting backend server on port {port}...")
    
    # Ensure the server script exists
    if not os.path.exists(SERVER_SCRIPT):
        logger.error(f"Server script not found at {SERVER_SCRIPT}")
        logger.info("Falling back to simplified_server.py in root directory")
        server_script = "simplified_server.py"
        if not os.path.exists(server_script):
            logger.error("Could not find any server script to run.")
            return None
    else:
        server_script = SERVER_SCRIPT
    
    try:
        process = subprocess.Popen(
            [sys.executable, server_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env={**os.environ, "SERVER_PORT": str(port)}
        )
        processes.append(process)
        logger.info(f"Backend server process started with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Failed to start backend server: {e}")
        return None

def run_proxy(port=DEFAULT_PROXY_PORT, backend_port=DEFAULT_SERVER_PORT):
    """Run the CORS proxy."""
    logger.info(f"Starting CORS proxy on port {port} pointing to backend on port {backend_port}...")
    
    # Ensure the proxy script exists
    if not os.path.exists(PROXY_SCRIPT):
        logger.error(f"Proxy script not found at {PROXY_SCRIPT}")
        logger.info("Falling back to cors_proxy.py in root directory")
        proxy_script = "cors_proxy.py"
        if not os.path.exists(proxy_script):
            logger.error("Could not find any proxy script to run.")
            return None
    else:
        proxy_script = PROXY_SCRIPT
    
    try:
        # Create a temporary script that sets the environment variables
        with open("temp_proxy_config.py", "w") as f:
            f.write(f"""
import os
os.environ['PROXY_PORT'] = '{port}'
os.environ['BACKEND_URL'] = 'http://127.0.0.1:{backend_port}'
            
# Now run the actual proxy script
with open("{proxy_script}") as proxy_file:
    exec(proxy_file.read())
""")
        
        process = subprocess.Popen(
            [sys.executable, "temp_proxy_config.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        processes.append(process)
        logger.info(f"CORS proxy process started with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Failed to start CORS proxy: {e}")
        return None
    finally:
        # Clean up the temporary script after a delay
        def cleanup_temp():
            time.sleep(2)  # Wait for the script to be loaded
            if os.path.exists("temp_proxy_config.py"):
                os.remove("temp_proxy_config.py")
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup_temp)
        cleanup_thread.daemon = True
        cleanup_thread.start()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Co-Pilot Mental Health Support Runner")
    parser.add_argument("--server", action="store_true", help="Run the backend server")
    parser.add_argument("--proxy", action="store_true", help="Run the CORS proxy")
    parser.add_argument("--server-port", type=int, default=DEFAULT_SERVER_PORT, help="Port for the backend server")
    parser.add_argument("--proxy-port", type=int, default=DEFAULT_PROXY_PORT, help="Port for the CORS proxy")
    
    args = parser.parse_args()
    
    # If no specific flags, run both server and proxy
    if not args.server and not args.proxy:
        args.server = True
        args.proxy = True
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_processes)
    
    # Start requested processes
    server_process = None
    proxy_process = None
    
    if args.server:
        server_process = run_server(port=args.server_port)
        
    if args.proxy:
        # Wait a moment for the server to start if both are being started
        if args.server and server_process:
            logger.info("Waiting for backend server to initialize...")
            time.sleep(2)
        
        proxy_process = run_proxy(port=args.proxy_port, backend_port=args.server_port)
    
    if not server_process and not proxy_process:
        logger.error("No processes were started successfully.")
        return
    
    logger.info("All processes started. Press Ctrl+C to stop.")
    
    # Main loop to keep the script running and monitor processes
    try:
        while True:
            if args.server and server_process and server_process.poll() is not None:
                logger.error("Backend server process stopped unexpectedly.")
                returncode = server_process.poll()
                output, _ = server_process.communicate()
                logger.error(f"Server output: {output}")
                logger.error(f"Return code: {returncode}")
                break
                
            if args.proxy and proxy_process and proxy_process.poll() is not None:
                logger.error("CORS proxy process stopped unexpectedly.")
                returncode = proxy_process.poll()
                output, _ = proxy_process.communicate()
                logger.error(f"Proxy output: {output}")
                logger.error(f"Return code: {returncode}")
                break
                
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt. Shutting down...")
    finally:
        # Clean up happens via the atexit handler
        pass

if __name__ == "__main__":
    main() 