# JiraOauthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.jira_oauth_error_response import JiraOauthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of JiraOauthErrorResponse from a JSON string
jira_oauth_error_response_instance = JiraOauthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(JiraOauthErrorResponse.to_json())

# convert the object into a dict
jira_oauth_error_response_dict = jira_oauth_error_response_instance.to_dict()
# create an instance of JiraOauthErrorResponse from a dict
jira_oauth_error_response_from_dict = JiraOauthErrorResponse.from_dict(jira_oauth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


