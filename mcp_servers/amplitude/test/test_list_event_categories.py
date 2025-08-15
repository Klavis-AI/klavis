from unittest import mock
from tools.list_event_categories import list_event_categories, CATEGORY_ENDPOINT

@mock.patch("tools.list_event_categories.requests.get")
def test_list_event_categories(mock_get):
    # Arrange
    mock_resp = mock.Mock()
    mock_resp.json.return_value = {"data": [{"id": 123, "name": "TestCat"}]}
    mock_resp.raise_for_status = lambda: None
    mock_get.return_value = mock_resp

    # Act
    result = list_event_categories()

    # Assert
    mock_get.assert_called_once_with(CATEGORY_ENDPOINT, auth=mock.ANY)
    assert result == [{"id": 123, "name": "TestCat"}]