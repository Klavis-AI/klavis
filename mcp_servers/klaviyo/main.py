# klaviyo_mcp_server.py
import os
import time
import requests
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# -------------------------
# Environment & MCP Setup
# -------------------------
load_dotenv()
KLAVIYO_API_KEY = os.getenv("KLAVIYO_API_KEY")
if not KLAVIYO_API_KEY:
    raise ValueError("Please set KLAVIYO_API_KEY in your .env file")

mcp = FastMCP("KlaviyoMCPServer", dependencies=["requests", "dotenv"])

HEADERS = {
    "Authorization": f"Klaviyo-API-Key {KLAVIYO_API_KEY}",
    "accept": "application/vnd.api+json",
    "revision": "2025-07-15",
}

BASE_URL = "https://a.klaviyo.com/api"

# -------------------------
# Utilities: requests, retries, pagination
# -------------------------
def _request(method: str, path: str, **kwargs) -> Dict[str, Any]:
    """
    Wrapper around requests to apply headers, retries, exponential backoff,
    and consistent error structure.
    """
    url = f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = kwargs.pop("headers", {})
    merged_headers = {**HEADERS, **headers}

    retries = kwargs.pop("retries", 3)
    backoff = kwargs.pop("backoff", 0.5)

    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(method, url, headers=merged_headers, timeout=15, **kwargs)
            # raise on 4xx/5xx to be handled uniformly
            resp.raise_for_status()
            # some endpoints return empty responses for deletes
            if resp.text:
                return resp.json()
            return {}
        except requests.RequestException as e:
            if attempt == retries:
                raise
            time.sleep(backoff * (2 ** (attempt - 1)))

def _paginate_get(path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Fetch all pages for endpoints that support pagination (cursor or page-based).
    Returns a concatenated list of resource objects (where applicable).
    """
    params = params or {}
    results: List[Dict[str, Any]] = []
    # Many Klaviyo endpoints use page[cursor] or standard JSON:API links
    response = _request("GET", path, params=params)

    # If top-level data array exists, concatenate it and follow 'links.next' if present.
    if isinstance(response, dict) and "data" in response:
        data = response.get("data", [])
        results.extend(data)
        # follow JSON:API links if present
        links = response.get("links", {}) or {}
        next_url = links.get("next")
        while next_url:
            # next_url is a fully qualified url; call it directly
            resp = requests.get(next_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            page = resp.json()
            results.extend(page.get("data", []))
            links = page.get("links", {}) or {}
            next_url = links.get("next")
    else:
        # Fallback: if response is already a list
        if isinstance(response, list):
            results.extend(response)
        else:
            # single object
            results.append(response)
    return results

# -------------------------
# Atomic Tools (Profiles)
# -------------------------
@mcp.tool()
def get_profile(email: str) -> dict:
    """Retrieve profile(s) by email. Uses Profiles 'get' with filter."""
    params = {"filter": f"equals(email,'{email}')"}
    return _request("GET", "/profiles", params=params)


@mcp.tool()
def create_or_update_profile_single(profile: Dict[str, Any]) -> dict:
    """
    Create a single profile (server-side).
    Use Profiles API create endpoint for single profile upsert if needed.
    """
    return _request("POST", "/profiles", json={"data": {"type": "profile", "attributes": profile}})

# -------------------------
# Atomic Tools (Lists & Segments)
# -------------------------
@mcp.tool()
def get_lists() -> dict:
    """Get all lists (paginated)."""
    return {"lists": _paginate_get("/lists")}

@mcp.tool()
def get_list(list_id: str) -> dict:
    return _request("GET", f"/lists/{list_id}")

@mcp.tool()
def create_list(list_name: str) -> dict:
    payload = {"data": {"type": "list", "attributes": {"name": list_name}}}
    return _request("POST", "/lists", json=payload)

@mcp.tool()
def get_profiles_for_list(list_id: str) -> dict:
    """Get profiles for a given list (paginated)."""
    return {"profiles": _paginate_get(f"/lists/{list_id}/relationships/profiles")}

# -------------------------
# Atomic Tools (Metrics & Custom Metrics)
# -------------------------
@mcp.tool()
def get_metrics() -> dict:
    """List metrics available in account."""
    return _request("GET", "/metrics")

@mcp.tool()
def get_custom_metrics() -> dict:
    return _request("GET", "/custom-metrics")

# -------------------------
# Atomic Tools (Campaigns)
# -------------------------
@mcp.tool()
def get_campaigns(channel: str) -> dict:
    """
    Retrieve campaigns from Klaviyo filtered by channel.

    You must provide one of these channels:
    - 'email' → For email campaigns
    - 'sms' → For SMS campaigns
    - 'mobile_push' → For mobile push campaigns

    Example natural language triggers:
    - "Show me all email campaigns"
    - "List SMS campaigns"
    - "Get mobile push campaigns from Klaviyo"
    """
    valid_channels = ["email", "sms", "mobile_push"]
    if channel not in valid_channels:
        raise ValueError(f"Invalid channel '{channel}'. Must be one of {valid_channels}")

    params = {"filter": f"equals(messages.channel,'{channel}')"}
    return {"campaigns": _paginate_get("/campaigns", params=params)}

@mcp.tool()
def create_campaign(campaign_data: Dict[str, Any]) -> dict:
    """
    Create a new campaign in Klaviyo.

    Args:
        campaign_data: A dictionary following Klaviyo's campaign creation schema.
                       See: https://developers.klaviyo.com/en/reference/create_campaign

    Example:
        create_campaign({
            "name": "My new campaign",
            "audiences": {
                "included": ["Y6nRLr"],
                "excluded": ["UTd5ui"]
            },
            "send_strategy": {
                "method": "static",
                "datetime": "2022-11-08T00:00:00+00:00",
                "options": {
                    "send_past_recipients_immediately": False
                }
            },
            "send_options": {
                "use_smart_sending": True
            },
            "tracking_options": {
                "add_tracking_params": True,
                "custom_tracking_params": [
                    {"type": "dynamic", "value": "campaign_id", "name": "utm_medium"},
                    {"type": "static", "value": "string", "name": "utm_medium"}
                ],
                "is_tracking_clicks": True,
                "is_tracking_opens": True
            },
            "campaign-messages": {
                "data": [
                    {
                        "type": "campaign-message",
                        "attributes": {
                            "definition": {
                                "channel": "email",
                                "label": "My message name",
                                "content": {
                                    "subject": "Buy our product!",
                                    "preview_text": "My preview text",
                                    "from_email": "store@my-company.com",
                                    "from_label": "My Company",
                                    "reply_to_email": "reply-to@my-company.com",
                                    "cc_email": "cc@my-company.com",
                                    "bcc_email": "bcc@my-company.com"
                                }
                            }
                        },
                        "relationships": {
                            "image": {
                                "data": {"type": "image", "id": "string"}
                            }
                        }
                    }
                ]
            }
        })
    """
    payload = {"data": {"type": "campaign", "attributes": campaign_data}}
    return _request("POST", "/campaigns", json=payload)
@mcp.tool()
def get_campaign(campaign_id: str) -> dict:
    """
    Retrieve a specific campaign by ID from Klaviyo.

    Args:
        campaign_id: The ID of the campaign to retrieve.

    Returns:
        The campaign data as a dictionary.
    """
    return _request("GET", f"/campaigns/{campaign_id}")



# -------------------------
# Atomic Tools (Templates)
# -------------------------
@mcp.tool()
def get_templates() -> dict:
    return {"templates": _paginate_get("/templates")}


@mcp.tool()
def render_template(template_id: str, render_data: Dict[str, Any]) -> dict:
    """Render a template server-side with given data."""
    return _request("POST", f"/template-render", json=render_data)




# -------------------------
# Atomic Tools (Flows)
# -------------------------
@mcp.tool()
def get_flows() -> dict:
    return {"flows": _paginate_get("/flows")}

# -------------------------
# Atomic Tools (Accounts)
# -------------------------
@mcp.tool()
def get_account_details() -> dict:
    return _request("GET", "/accounts")

@mcp.tool()
def list_accounts() -> dict:
    return _request("GET", "/accounts")



# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    mcp.run()
    print("✅ Klaviyo MCP Server is running...")
