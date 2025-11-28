from flask import Flask, request, jsonify
import os
from quiz_solver import solve_quiz
import threading

app = Flask(__name__)

# Load from environment variables
MY_EMAIL = os.environ.get('MY_EMAIL', 'your-email@example.com')
MY_SECRET = os.environ.get('MY_SECRET', 'your-secret-string')

@app.route('/quiz', methods=['POST'])
def handle_quiz():
    try:
        data = request.get_json()
    except:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    email = data.get('email')
    secret = data.get('secret')
    url = data.get('url')
    
    # Verify secret
    if secret != MY_SECRET:
        return jsonify({'error': 'Invalid secret'}), 403
    
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
    
    # Start solving in background thread
    thread = threading.Thread(target=solve_quiz, args=(email, secret, url))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'processing', 'url': url}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
