# mcp_servers/twilio/twilio/utils.py

import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class TwilioApiClient:
    """A simple client for handling all our Twilio API calls."""

    def __init__(self):
        """Load up our credentials from the environment."""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')

        # If any of these are missing, we can't do anything. Fail loudly.
        if not all([account_sid, auth_token, self.twilio_phone_number]):
            raise ValueError("Missing critical Twilio environment variables (ACCOUNT_SID, AUTH_TOKEN, or PHONE_NUMBER)")

        self.client = Client(account_sid, auth_token)

    def send_sms(self, to_number: str, body: str) -> dict:
        """Sends a standard SMS."""
        try:
            message = self.client.messages.create(
                to=to_number,
                from_=self.twilio_phone_number,
                body=body
            )
            # Just return the basics for confirmation.
            return {"status": "Message sent successfully", "message_sid": message.sid}
        except TwilioRestException as e:
            # Re-raise with a more generic error that our route handler can catch.
            raise ConnectionError(f"Twilio API Error: {e.msg}") from e

    def send_mms(self, to_number: str, media_url: str, body: str = "") -> dict:
        """Sends an MMS with a link to some media."""
        try:
            # Twilio's helper library expects media_url to be a list.
            message = self.client.messages.create(
                to=to_number,
                from_=self.twilio_phone_number,
                body=body,
                media_url=[media_url]
            )
            return {"status": "MMS sent successfully", "message_sid": message.sid}
        except TwilioRestException as e:
            raise ConnectionError(f"Twilio API Error: {e.msg}") from e

    def list_messages(self, limit: int = 20) -> list:
        """Gets a list of recent messages."""
        try:
            messages = self.client.messages.list(limit=limit)
            # Just pull out the useful bits into a clean list of dicts.
            return [{"sid": msg.sid, "from": msg.from_, "to": msg.to, "body": msg.body, "status": msg.status} for msg in messages]
        except TwilioRestException as e:
            raise ConnectionError(f"Twilio API Error: {e.msg}") from e

    def get_message_details(self, message_sid: str) -> dict:
        """Fetches the details for a single message."""
        try:
            msg = self.client.messages(message_sid).fetch()
            # Return a bit more detail than the list view.
            return {"sid": msg.sid, "from": msg.from_, "to": msg.to, "body": msg.body, "status": msg.status, "error_message": msg.error_message}
        except TwilioRestException as e:
            raise ConnectionError(f"Twilio API Error: {e.msg}") from e

    def redact_message(self, message_sid: str) -> dict:
        """
        This is Twilio's version of 'deleting' a message.
        It doesn't remove the record, just blanks out the body content.
        """
        try:
            message = self.client.messages(message_sid).update(body="")
            return {"status": "Message redacted successfully", "message_sid": message.sid}
        except TwilioRestException as e:
            raise ConnectionError(f"Twilio API Error: {e.msg}") from e
    
    def list_phone_numbers(self) -> list:
        """
        Lets the AI see what numbers are available in the account.
        This is good for checking capabilities (SMS, MMS, Voice).
        """
        try:
            numbers = self.client.incoming_phone_numbers.list(limit=20)
            return [{"phone_number": num.phone_number, "sid": num.sid, "capabilities": num.capabilities} for num in numbers]
        except TwilioRestException as e:
            raise ConnectionError(f"Twilio API Error: {e.msg}") from e