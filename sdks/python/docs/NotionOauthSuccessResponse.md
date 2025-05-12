# NotionOauthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.notion_oauth_success_response import NotionOauthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of NotionOauthSuccessResponse from a JSON string
notion_oauth_success_response_instance = NotionOauthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(NotionOauthSuccessResponse.to_json())

# convert the object into a dict
notion_oauth_success_response_dict = notion_oauth_success_response_instance.to_dict()
# create an instance of NotionOauthSuccessResponse from a dict
notion_oauth_success_response_from_dict = NotionOauthSuccessResponse.from_dict(notion_oauth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


