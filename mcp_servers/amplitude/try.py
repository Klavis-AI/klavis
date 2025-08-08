import os, requests
url = "https://api2.amplitude.com/identify"
data = {
  "api_key": os.environ["AMPLITUDE_API_KEY"],
  # NOTE: identification must be a JSON string, not a dict
  "identification": '[{"user_id":"jain_mcp_2247","user_properties":{"plan":"free","source":"mcp"}}]'
}
r = requests.post(url, data=data)  # form-encoded
print(r.status_code, r.text)