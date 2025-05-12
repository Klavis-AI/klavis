# SlackOAuthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.slack_o_auth_error_response import SlackOAuthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SlackOAuthErrorResponse from a JSON string
slack_o_auth_error_response_instance = SlackOAuthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(SlackOAuthErrorResponse.to_json())

# convert the object into a dict
slack_o_auth_error_response_dict = slack_o_auth_error_response_instance.to_dict()
# create an instance of SlackOAuthErrorResponse from a dict
slack_o_auth_error_response_from_dict = SlackOAuthErrorResponse.from_dict(slack_o_auth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


