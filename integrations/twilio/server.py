# Step 1: Import the tools we need
import os
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Step 2: Create the main application object
# This is the foundation of our server.
app = Flask(__name__)

# Step 3: Load our secret credentials from the environment
# This is the secure way to handle secrets, never write them directly in the code.
# We will set these in the terminal later.
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')

# Step 4: Create the Twilio client
# This object is our main tool for talking to Twilio's API.
client = Client(account_sid, auth_token)

# Step 5: Define the 'send_sms' tool
# The "@app.route" line creates a unique URL for our tool.
# We specify "methods=['POST']" because we expect to receive data.
@app.route('/tools/send_sms', methods=['POST'])
def send_sms():
    """
    This function is the core logic for our tool.
    It's designed to be used by an AI.
    """
    print("Tool 'send_sms' was called.")

    # Get the data the AI sent to us (to, body)
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request: No data provided"}), 400

    to_number = data.get('to')
    body = data.get('body')

    # Basic validation
    if not to_number or not body:
        return jsonify({"error": "Missing 'to' or 'body' in request"}), 400

    try:
        # This is where we use the Twilio client to send the message!
        message = client.messages.create(
            to=to_number,
            from_=twilio_phone_number,
            body=body
        )
        print(f"Successfully sent message. SID: {message.sid}")
        # Send back a success response with the message ID (SID)
        return jsonify({
            "status": "Message sent successfully",
            "message_sid": message.sid
        })

    except TwilioRestException as e:
        # If Twilio gives us an error (e.g., bad phone number), catch it.
        print(f"Error from Twilio: {e}")
        return jsonify({"error": f"Failed to send SMS: {e.msg}"}), 500

# Step 6: This part makes the server run when you execute the file.
# It will run on a local "port" (5000) and will be accessible only on your computer.
if __name__ == '__main__':
    app.run(port=5000, debug=True)