import requests

try:
    print("Sending request...")
    response = requests.post("http://localhost:5050/sessions/start_simulation", json={}, timeout=5)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
except Exception as e:
    print(f"Error: {e}") 