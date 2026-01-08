# mcp_servers/amplitude/tools/get_user_profile.py
import json
import urllib.parse
import urllib.request
from . import get_api_secret

USER_PROFILE_ENDPOINT = "https://profile-api.amplitude.com/v1/userprofile"

def get_user_profile(
    user_id: str,
    get_amp_props: bool = False,
    get_cohort_ids: bool = False,
    get_recs: bool = False,
    get_computations: bool = False,
) -> dict:
    api_secret = get_api_secret()
    if not api_secret:
        return {"error": "profile_api_unavailable_or_unauthorized", "detail": "AMPLITUDE_API_SECRET not set"}

    params = urllib.parse.urlencode({
        "user_id": user_id,
        "get_amp_props": str(get_amp_props).lower(),
        "get_cohort_ids": str(get_cohort_ids).lower(),
        "get_recs": str(get_recs).lower(),
        "get_computations": str(get_computations).lower(),
    })
    req = urllib.request.Request(
        f"{USER_PROFILE_ENDPOINT}?{params}",
        headers={"Authorization": f"Api-Key {api_secret}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return {"status_code": resp.getcode(), "response": json.loads(body)}
    except urllib.error.HTTPError as e:
        return {"status_code": e.code, "error": e.read().decode("utf-8")[:1000]}
    except Exception as e:
        return {"status_code": 0, "error": str(e)}