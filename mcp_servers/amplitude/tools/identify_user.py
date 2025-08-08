import os, json
import requests
from typing import Dict, Optional

API_KEY = os.getenv("AMPLITUDE_API_KEY")
IDENTIFY_URL = os.getenv("AMPLITUDE_IDENTIFY_URL", "https://api2.amplitude.com/identify")


def identify_user(
    user_id: Optional[str] = None,
    device_id: Optional[str] = None,
    user_properties: Optional[Dict] = None,
    operations: Optional[Dict] = None,
) -> Dict:
    """
    Identify a user and set user properties.

    Inputs:
      user_id: str
      device_id: str
      user_properties: Plain properties to $set (e.g., {"plan":"free"}).
      operations: Advanced ops dict (e.g., {"$set": {...}, "$add": {...}}). If provided, overrides user_properties.

    Returns: {"status_code": int, "response": str}
    """
    if not API_KEY:
        raise RuntimeError("AMPLITUDE_API_KEY not set")

    # Build identification object
    ident: Dict = {}
    if user_id:
        ident["user_id"] = user_id
    if device_id:
        ident["device_id"] = device_id

    if not ident:
        raise ValueError("At least one of user_id or device_id must be provided")

    if operations is not None:
        ident["user_properties"] = operations
    elif user_properties is not None:
        ident["user_properties"] = {"$set": user_properties}
    else:
        ident["user_properties"] = {}

    # Identify API requires form-encoded body with identification as a JSON string
    data = {
        "api_key": API_KEY,
        "identification": json.dumps([ident])
    }
    resp = requests.post(IDENTIFY_URL, data=data)
    try:
        resp.raise_for_status()
        body = resp.text
    except Exception:
        body = resp.text
    return {"status_code": resp.status_code, "response": body}