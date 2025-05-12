# JiraOAuthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.jira_o_auth_success_response import JiraOAuthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of JiraOAuthSuccessResponse from a JSON string
jira_o_auth_success_response_instance = JiraOAuthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(JiraOAuthSuccessResponse.to_json())

# convert the object into a dict
jira_o_auth_success_response_dict = jira_o_auth_success_response_instance.to_dict()
# create an instance of JiraOAuthSuccessResponse from a dict
jira_o_auth_success_response_from_dict = JiraOAuthSuccessResponse.from_dict(jira_o_auth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


