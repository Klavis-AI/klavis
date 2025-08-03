# MCP Server for Twilio

This project is an MCP server for the Twilio API, allowing an AI agent to perform communication tasks.

## Setup

1.  **Environment Variables**: The server requires the following environment variables to be set. These can be found in your Twilio Console.
    *   `TWILIO_ACCOUNT_SID`: Your account identifier.
    *   `TWILIO_AUTH_TOKEN`: Your secret auth token.
    *   `TWILIO_PHONE_NUMBER`: Your default Twilio phone number for sending messages.

2.  **Installation & Running:**
    ```bash
    # Navigate to the server directory
    cd mcp_servers/twilio/twilio

    # Install dependencies
    pip install -r requirements.txt

    # Run the server
    python main.py
    ```
The server will run on `http://127.0.0.1:5000`.

## Available Tools

### 1. Send SMS
- **Route:** `/send_sms`
- **Method:** `POST`
- **Description:** Sends a new text-only message.
- **Body:** `{"to": "<phone_number>", "body": "<message_text>"}`

### 2. Send MMS
- **Route:** `/send_mms`
- **Method:** `POST`
- **Description:** Sends a new message containing media.
- **Body:** `{"to": "<phone_number>", "media_url": "<url_to_image>", "body": "<optional_text>"}`

### 3. List Messages
- **Route:** `/list_messages`
- **Method:** `GET`
- **Description:** Retrieves the 20 most recent messages.

### 4. Get Message Details
- **Route:** `/get_message_details`
- **Method:** `POST`
- **Description:** Fetches details for a single message.
- **Body:** `{"sid": "<message_sid>"}`

### 5. Redact Message
- **Route:** `/redact_message`
- **Method:** `POST`
- **Description:** Deletes the content of a message body, making it unreadable.
- **Body:** `{"sid": "<message_sid>"}`

### 6. List Phone Numbers
- **Route:** `/list_phone_numbers`
- **Method:** `GET`
- **Description:** Retrieves a list of all active Twilio phone numbers in the account and their capabilities.