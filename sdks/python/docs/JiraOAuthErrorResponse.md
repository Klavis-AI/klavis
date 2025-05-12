# JiraOAuthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.jira_o_auth_error_response import JiraOAuthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of JiraOAuthErrorResponse from a JSON string
jira_o_auth_error_response_instance = JiraOAuthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(JiraOAuthErrorResponse.to_json())

# convert the object into a dict
jira_o_auth_error_response_dict = jira_o_auth_error_response_instance.to_dict()
# create an instance of JiraOAuthErrorResponse from a dict
jira_o_auth_error_response_from_dict = JiraOAuthErrorResponse.from_dict(jira_o_auth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


