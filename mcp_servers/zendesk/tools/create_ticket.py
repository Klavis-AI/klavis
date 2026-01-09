# import httpx
from .common import get_zendesk_env, base_url, auth, client, safe_text

def create_ticket(subject: str, description: str, requester_email: str, requester_name: str | None = None) -> dict:
    """
    Stateless ticket creation. No globals; reads env per call; short-lived HTTP client.
    Returns a minimal, stable shape for MCP consumers.
    """
    email, token, subdomain = get_zendesk_env()
    url = f"{base_url(subdomain)}/api/v2/tickets.json"
    name = requester_name or requester_email.split("@")[0]

    payload = {
        "ticket": {
            "subject": subject,
            "comment": {"body": description},
            "requester": {"name": name, "email": requester_email},
        }
    }

    with client() as c:
        resp = c.post(url, json=payload, auth=auth(email, token))
        if resp.status_code != 201:
            raise RuntimeError(f"Zendesk create failed ({resp.status_code}): {safe_text(resp)}")
        t = resp.json().get("ticket", {})
        return {
            "ticket_id": t.get("id"),
            "status": t.get("status", "new"),
            "subject": t.get("subject", subject),
            "message": "Ticket successfully created."
        }
