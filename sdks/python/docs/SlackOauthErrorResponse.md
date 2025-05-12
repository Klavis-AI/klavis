# SlackOauthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.slack_oauth_error_response import SlackOauthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SlackOauthErrorResponse from a JSON string
slack_oauth_error_response_instance = SlackOauthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(SlackOauthErrorResponse.to_json())

# convert the object into a dict
slack_oauth_error_response_dict = slack_oauth_error_response_instance.to_dict()
# create an instance of SlackOauthErrorResponse from a dict
slack_oauth_error_response_from_dict = SlackOauthErrorResponse.from_dict(slack_oauth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


