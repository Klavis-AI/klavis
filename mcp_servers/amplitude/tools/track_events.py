# stdlib-only Amplitude HTTP V2 event ingestion
import json
import urllib.request
from typing import Any, Dict, Optional
from . import get_api_key, get_api_secret

AMPLITUDE_API_ENDPOINT = "https://api2.amplitude.com/2/httpapi"

def _ms(ts: Optional[int | float]) -> Optional[int]:
    if ts is None:
        return None
    # if seconds, convert to ms
    return int(ts * 1000) if float(ts) < 10_000_000_000 else int(ts)

def track_event(
    event_type: str,
    user_id: Optional[str] = None,
    device_id: Optional[str] = None,
    event_properties: Optional[Any] = None,
    time: Optional[int | float] = None,
) -> Dict[str, Any]:
    """
    Send one event to Amplitude HTTP V2.
    Requires event_type and at least one of user_id or device_id.
    """
    api_key = get_api_key()
    if not api_key:
        return {"status_code": 0, "error": "AMPLITUDE_API_KEY missing"}

    if not event_type:
        return {"status_code": 0, "error": "event_type is required"}
    if not user_id and not device_id:
        return {"status_code": 0, "error": "Provide user_id or device_id (>=5 chars)"}
    if user_id and len(str(user_id)) < 5:
        return {"status_code": 0, "error": "user_id must be >= 5 chars"}
    if device_id and len(str(device_id)) < 5:
        return {"status_code": 0, "error": "device_id must be >= 5 chars"}

    # event_properties might arrive as a JSON string; parse defensively
    if isinstance(event_properties, str):
        try:
            event_properties = json.loads(event_properties)
        except Exception:
            event_properties = {"_raw": event_properties}

    evt: Dict[str, Any] = {
        "event_type": event_type,
        "event_properties": event_properties or {},
    }
    if user_id:
        evt["user_id"] = str(user_id)
    if device_id:
        evt["device_id"] = str(device_id)

    ts = _ms(time)
    if ts is not None:
        evt["time"] = ts

    payload = {"api_key": api_key, "events": [evt]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        AMPLITUDE_API_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8") or "{}"
            return {"status_code": resp.getcode(), "response": json.loads(body)}
    except urllib.error.HTTPError as e:
        return {"status_code": e.code, "error": e.read().decode("utf-8")[:1000]}
    except Exception as e:
        return {"status_code": 0, "error": str(e)}