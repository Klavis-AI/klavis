# NotionOAuthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.notion_o_auth_error_response import NotionOAuthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of NotionOAuthErrorResponse from a JSON string
notion_o_auth_error_response_instance = NotionOAuthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(NotionOAuthErrorResponse.to_json())

# convert the object into a dict
notion_o_auth_error_response_dict = notion_o_auth_error_response_instance.to_dict()
# create an instance of NotionOAuthErrorResponse from a dict
notion_o_auth_error_response_from_dict = NotionOAuthErrorResponse.from_dict(notion_o_auth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


