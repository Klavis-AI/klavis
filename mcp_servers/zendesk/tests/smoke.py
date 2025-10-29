import os
from tools.create_ticket import create_ticket
from tools.get_ticket_status import get_ticket_status
from tools.list_recent_tickets import list_recent_tickets
from tools.add_comment_to_ticket import add_comment_to_ticket

def must(k):
    v = os.getenv(k)
    if not v:
        raise SystemExit(f"Missing env var: {k}")
    return v

def main():
    # Ensure creds exist
    must("ZENDESK_EMAIL"); must("ZENDESK_API_TOKEN"); must("ZENDESK_SUBDOMAIN")

    print("== Smoke: create_ticket ==")
    res = create_ticket(
        subject="Smoke test via Docker",
        description="Created by tests/smoke.py",
        requester_email="cursorsl@gmail.com",
        requester_name="Smoke Tester"
    )
    print(res)
    ticket_id = res.get("ticket_id")
    assert ticket_id, "No ticket_id returned!"

    print("== Smoke: get_ticket_status ==")
    print(get_ticket_status(ticket_id))

    print("== Smoke: add_comment_to_ticket ==")
    print(add_comment_to_ticket(ticket_id, "Automated test comment"))

    print("== Smoke: list_recent_tickets ==")
    print(list_recent_tickets(limit=3))

    print("✅ Smoke test completed")

if __name__ == "__main__":
    main()
