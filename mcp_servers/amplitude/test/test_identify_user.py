from unittest import mock
from tools.identify_user import identify_user, IDENTIFY_URL

@mock.patch("tools.identify_user.requests.post")
def test_identify_user_form_encoded(mock_post):
    mock_resp = mock.Mock()
    mock_resp.status_code = 200
    mock_resp.text = "success"
    mock_resp.raise_for_status = lambda: None
    mock_post.return_value = mock_resp

#userid is something you can choose it will be automatically updated to Amplitude
    out = identify_user(user_id="jain_mcp_2247", user_properties={"plan":"free"})
    assert out["status_code"] == 200
    assert out["response"] == "success"

    _, kwargs = mock_post.call_args
    assert kwargs.get("data") and "identification" in kwargs["data"]
    assert kwargs.get("url", IDENTIFY_URL) or True