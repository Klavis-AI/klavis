import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_logs_success():
    # Use _internal index because it always has data
    response = client.post(
        "/search_logs",
        json={
            "query": "search index=_internal | head 1",
            "earliest_time": "0",
            "latest_time": "now"
        }
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "results" in json_data
    assert isinstance(json_data["results"], list)

def test_get_events_success():
    response = client.get("/get_events?index=_internal&limit=1")
    assert response.status_code == 200
    json_data = response.json()
    assert "events" in json_data
    assert isinstance(json_data["events"], list)

def test_trigger_alert_not_found():
    response = client.post(
        "/trigger_alert",
        json={
            "alert_name": "DefinitelyNotARealAlert",
            "params": {}
        }
    )
    assert response.status_code in [404, 500]  # Depending on your error handling
    # Optionally check for error detail string in the response
    assert "error" in response.json() or "detail" in response.json()
