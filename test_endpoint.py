import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Your endpoint URL
ENDPOINT = "http://localhost:5000/quiz"

# Test with demo quiz
payload = {
    "email": os.environ.get('MY_EMAIL'),
    "secret": os.environ.get('MY_SECRET'),
    "url": "https://tds-llm-analysis.s-anand.net/demo"
}

print("Testing endpoint...")
print(f"Sending request to: {ENDPOINT}")
print(f"Payload: {payload}")

try:
    response = requests.post(ENDPOINT, json=payload, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
