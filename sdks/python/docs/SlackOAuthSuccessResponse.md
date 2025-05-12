# SlackOAuthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.slack_o_auth_success_response import SlackOAuthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SlackOAuthSuccessResponse from a JSON string
slack_o_auth_success_response_instance = SlackOAuthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(SlackOAuthSuccessResponse.to_json())

# convert the object into a dict
slack_o_auth_success_response_dict = slack_o_auth_success_response_instance.to_dict()
# create an instance of SlackOAuthSuccessResponse from a dict
slack_o_auth_success_response_from_dict = SlackOAuthSuccessResponse.from_dict(slack_o_auth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


