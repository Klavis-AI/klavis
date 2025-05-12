# NotionOAuthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.notion_o_auth_success_response import NotionOAuthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of NotionOAuthSuccessResponse from a JSON string
notion_o_auth_success_response_instance = NotionOAuthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(NotionOAuthSuccessResponse.to_json())

# convert the object into a dict
notion_o_auth_success_response_dict = notion_o_auth_success_response_instance.to_dict()
# create an instance of NotionOAuthSuccessResponse from a dict
notion_o_auth_success_response_from_dict = NotionOAuthSuccessResponse.from_dict(notion_o_auth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


