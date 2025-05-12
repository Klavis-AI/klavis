# SlackOauthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.slack_oauth_success_response import SlackOauthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SlackOauthSuccessResponse from a JSON string
slack_oauth_success_response_instance = SlackOauthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(SlackOauthSuccessResponse.to_json())

# convert the object into a dict
slack_oauth_success_response_dict = slack_oauth_success_response_instance.to_dict()
# create an instance of SlackOauthSuccessResponse from a dict
slack_oauth_success_response_from_dict = SlackOauthSuccessResponse.from_dict(slack_oauth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


