from unittest import mock
from tools.get_user_profile import get_user_profile, USER_PROFILE_ENDPOINT

@mock.patch("tools.get_user_profile.requests.get")
def test_get_user_profile(mock_get):
    # Arrange
    fake_json = {"userData": {"user_id": "user1", "amp_props": {}}}
    mock_resp = mock.Mock()
    mock_resp.json.return_value = fake_json
    mock_resp.raise_for_status = lambda: None
    mock_get.return_value = mock_resp

    # Act
    result = get_user_profile("user1", get_amp_props=True)

    # Assert
    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    assert called_url == USER_PROFILE_ENDPOINT
    assert result == fake_json