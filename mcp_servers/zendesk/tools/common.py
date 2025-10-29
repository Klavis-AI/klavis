import os
import httpx

def get_zendesk_env():
    email = os.getenv("ZENDESK_EMAIL")
    token = os.getenv("ZENDESK_API_TOKEN")
    subdomain = os.getenv("ZENDESK_SUBDOMAIN")
    if not all([email, token, subdomain]):
        raise RuntimeError("Missing Zendesk credentials in environment (ZENDESK_EMAIL, ZENDESK_API_TOKEN, ZENDESK_SUBDOMAIN)")
    return email, token, subdomain

def base_url(subdomain: str) -> str:
    return f"https://{subdomain}.zendesk.com"

def auth(email: str, token: str) -> httpx.BasicAuth:
    # Zendesk requires email + '/token' as username, API token as password
    return httpx.BasicAuth(f"{email}/token", token)

def client(timeout_sec: float = 15.0) -> httpx.Client:
    # Fresh client per request (stateless; no cross-request pooling)
    return httpx.Client(timeout=httpx.Timeout(timeout_sec), headers={"Content-Type": "application/json", "Accept": "application/json"})

def safe_text(resp: httpx.Response, maxlen: int = 2000) -> str:
    try:
        return resp.text[:maxlen]
    except Exception:
        return "<unreadable-response>"
