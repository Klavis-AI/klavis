import os
import requests
from typing import Dict

AMPLITUDE_API_ENDPOINT = "https://api2.amplitude.com/2/httpapi"
API_KEY = os.getenv("AMPLITUDE_API_KEY")

def track_event(event_type: str, user_id: str, event_properties: Dict = None, time: int = None) -> Dict:
    """
    Sends a single event to Amplitude via HTTP V2 API.

    Inputs:
      event_type: Name of the event (string).
      user_id: Unique identifier for the user (string).
      event_properties: Dictionary of event-specific properties.
      time: UNIX timestamp in milliseconds.

    Outputs:
      status_code: HTTP status code of the response.
      response: Parsed JSON response.
    """
    payload = {
        "api_key": API_KEY, 
        "events": [
            {
                "event_type": event_type,
                "user_id": user_id,
                "event_properties": event_properties or {},
                "time": time
            }
        ]
    }
    resp = requests.post(AMPLITUDE_API_ENDPOINT, json=payload)
    resp.raise_for_status()
    return {"status_code": resp.status_code, "response": resp.json()}