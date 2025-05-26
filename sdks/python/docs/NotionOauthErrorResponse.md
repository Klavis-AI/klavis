# NotionOauthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.notion_oauth_error_response import NotionOauthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of NotionOauthErrorResponse from a JSON string
notion_oauth_error_response_instance = NotionOauthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(NotionOauthErrorResponse.to_json())

# convert the object into a dict
notion_oauth_error_response_dict = notion_oauth_error_response_instance.to_dict()
# create an instance of NotionOauthErrorResponse from a dict
notion_oauth_error_response_from_dict = NotionOauthErrorResponse.from_dict(notion_oauth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


