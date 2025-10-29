# mcp_servers/amplitude/tools/list_event_categories.py
import json
import base64
import urllib.request
from . import get_api_key, get_api_secret

CATEGORY_ENDPOINT = "https://amplitude.com/api/2/taxonomy/category"

def list_event_categories() -> list | dict:
    """
    List Amplitude taxonomy categories (plan/permission gated).

    Returns:
      - On success: list of category objects (from "data")
      - On error: dict with error message
    """
    api_key = get_api_key()
    api_secret = get_api_secret()
    if not api_key or not api_secret:
        return {
            "error": "taxonomy_unavailable_or_forbidden",
            "detail": "Missing AMPLITUDE_API_KEY and/or AMPLITUDE_API_SECRET"
        }

    creds = f"{api_key}:{api_secret}".encode("utf-8")
    auth_header = "Basic " + base64.b64encode(creds).decode("utf-8")

    req = urllib.request.Request(
        CATEGORY_ENDPOINT,
        headers={"Authorization": auth_header},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8") or "{}"
            data = json.loads(body)
            return data.get("data", data)
    except urllib.error.HTTPError as e:
        return {"status_code": e.code, "error": e.read().decode("utf-8")[:1000]}
    except Exception as e:
        return {"status_code": 0, "error": str(e)}