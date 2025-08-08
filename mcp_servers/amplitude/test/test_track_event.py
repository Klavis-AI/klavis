import mock
import pytest
from tools.track_events import track_event, AMPLITUDE_API_ENDPOINT

@mock.patch("tools.track_events.requests")
def test_track_event(mock_requests):
    mock_resp = mock.Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"events_ingested": 1}
    mock_resp.raise_for_status = lambda: None
    mock_requests.post.return_value = mock_resp

    result = track_event("test_event", "user123", {"key": "value"}, 1620000000000)
    assert result["status_code"] == 200
    assert result["response"] == {"events_ingested": 1}
    mock_requests.post.assert_called_with(AMPLITUDE_API_ENDPOINT, json=mock.ANY)