import os, json, time, requests

API_KEY = os.environ["AMPLITUDE_API_KEY"]
API_SECRET = os.environ.get("AMPLITUDE_API_SECRET", "")
USER_ID = os.environ.get("USER_ID", "jain_mcp_2247")

# 1) HTTP V2 event
v2_url = "https://api2.amplitude.com/2/httpapi"  # EU: https://api.eu.amplitude.com/2/httpapi
payload = {
    "api_key": API_KEY,
    "events": [{
        "event_type": "mcp_smoke_test",
        "user_id": USER_ID,
        "time": int(time.time() * 1000),
        "event_properties": {"source": "mcp", "purpose": "smoke_test"}
    }]
}
r = requests.post(v2_url, json=payload)
print("HTTP V2 status:", r.status_code)
print("HTTP V2 body:", r.text)

# 2) Profile API (optional; requires Activation plan, US-only)
if API_SECRET:
    prof_url = "https://profile-api.amplitude.com/v1/userprofile"
    headers = {"Authorization": f"Api-Key {API_SECRET}"}
    params = {"user_id": USER_ID, "get_amp_props": "true"}
    rp = requests.get(prof_url, headers=headers, params=params)
    print("Profile status:", rp.status_code)
    print("Profile body:", rp.text)