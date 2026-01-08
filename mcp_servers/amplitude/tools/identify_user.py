# stdlib-only Amplitude Identify API (form-encoded)
import json
import os
import urllib.parse
import urllib.request
from typing import Dict, Optional
from . import get_api_key, get_api_secret

IDENTIFY_URL = os.environ.get("AMPLITUDE_IDENTIFY_URL", "https://api2.amplitude.com/identify")

def identify_user(
    user_id: Optional[str] = None,
    device_id: Optional[str] = None,
    user_properties: Optional[Dict] = None,
    operations: Optional[Dict] = None,
) -> Dict:
    """
    Identify a user and set user properties.
    If `operations` is provided, it is used as-is (e.g. {"$set": {...}}).
    Otherwise, `user_properties` are wrapped under {"$set": ...}.
    """
    api_key = get_api_key()
    if not api_key:
        return {"status_code": 0, "error": "AMPLITUDE_API_KEY missing"}

    if not user_id and not device_id:
        return {"status_code": 0, "error": "Provide user_id or device_id (>=5 chars)"}
    if user_id and len(str(user_id)) < 5:
        return {"status_code": 0, "error": "user_id must be >= 5 chars"}
    if device_id and len(str(device_id)) < 5:
        return {"status_code": 0, "error": "device_id must be >= 5 chars"}

    ident: Dict = {}
    if user_id:
        ident["user_id"] = user_id
    if device_id:
        ident["device_id"] = device_id

    if operations is not None:
        ident["user_properties"] = operations
    elif user_properties is not None:
        ident["user_properties"] = {"$set": user_properties}
    else:
        ident["user_properties"] = {}

    form = urllib.parse.urlencode({
        "api_key": api_key,
        "identification": json.dumps([ident]),
    }).encode("utf-8")

    req = urllib.request.Request(
        IDENTIFY_URL,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return {"status_code": resp.getcode(), "response": body}
    except urllib.error.HTTPError as e:
        return {"status_code": e.code, "error": e.read().decode("utf-8")[:1000]}
    except Exception as e:
        return {"status_code": 0, "error": str(e)}