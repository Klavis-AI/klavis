# mcp_servers/twilio/twilio/main.py

from flask import Flask, request, jsonify
from utils import TwilioApiClient

# This is our main web application.
app = Flask(__name__)

# --- Client Initialization ---
# Create one shared client instance for the whole app.
# This is more efficient than creating a new one for every request.
try:
    twilio_client = TwilioApiClient()
    print("Twilio API Client initialized successfully.")
except ValueError as e:
    # If the client fails to init (e.g., missing env vars), log it and set to None.
    # The routes below will then fail gracefully.
    twilio_client = None
    print(f"CRITICAL: Could not initialize TwilioApiClient. {e}")


# --- Tool Handlers ---

@app.route('/send_sms', methods=['POST'])
def send_sms_handler():
    # This is our main guard clause. If the client didn't init, none of the tools will work.
    if not twilio_client: return jsonify({"error": "Server is not configured"}), 503
    
    # 1. Get the data from the incoming request.
    data = request.get_json()
    
    # 2. Do some basic validation to make sure we have what we need.
    if not data or 'to' not in data or 'body' not in data:
        return jsonify({"error": "Missing 'to' or 'body'"}), 400
    
    # 3. Call our client to do the real work and return the response.
    try:
        return jsonify(twilio_client.send_sms(data['to'], data['body'])), 200
    except ConnectionError as e:
        # 4. If our client had a problem talking to Twilio, catch it and report it.
        return jsonify({"error": str(e)}), 500

@app.route('/send_mms', methods=['POST'])
def send_mms_handler():
    if not twilio_client: return jsonify({"error": "Server is not configured"}), 503
    data = request.get_json()
    if not data or 'to' not in data or 'media_url' not in data:
        return jsonify({"error": "Missing 'to' or 'media_url'"}), 400
    try:
        # The body is optional for an MMS, so we use .get() with a default.
        body = data.get('body', '')
        return jsonify(twilio_client.send_mms(data['to'], data['media_url'], body)), 200
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list_messages', methods=['GET'])
def list_messages_handler():
    if not twilio_client: return jsonify({"error": "Server is not configured"}), 503
    try:
        return jsonify({"messages": twilio_client.list_messages()}), 200
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_message_details', methods=['POST'])
def get_message_details_handler():
    if not twilio_client: return jsonify({"error": "Server is not configured"}), 503
    data = request.get_json()
    if not data or 'sid' not in data:
        return jsonify({"error": "Missing 'sid'"}), 400
    try:
        return jsonify(twilio_client.get_message_details(data['sid'])), 200
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/redact_message', methods=['POST'])
def redact_message_handler():
    if not twilio_client: return jsonify({"error": "Server is not configured"}), 503
    data = request.get_json()
    if not data or 'sid' not in data:
        return jsonify({"error": "Missing 'sid'"}), 400
    try:
        return jsonify(twilio_client.redact_message(data['sid'])), 200
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list_phone_numbers', methods=['GET'])
def list_phone_numbers_handler():
    if not twilio_client: return jsonify({"error": "Server is not configured"}), 503
    try:
        return jsonify({"phone_numbers": twilio_client.list_phone_numbers()}), 200
    except ConnectionError as e:
        return jsonify({"error": str(e)}), 500

# This makes the script runnable with `python main.py`.
if __name__ == '__main__':
    app.run(port=5000, debug=True)