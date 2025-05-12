# JiraOauthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.jira_oauth_success_response import JiraOauthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of JiraOauthSuccessResponse from a JSON string
jira_oauth_success_response_instance = JiraOauthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(JiraOauthSuccessResponse.to_json())

# convert the object into a dict
jira_oauth_success_response_dict = jira_oauth_success_response_instance.to_dict()
# create an instance of JiraOauthSuccessResponse from a dict
jira_oauth_success_response_from_dict = JiraOauthSuccessResponse.from_dict(jira_oauth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


