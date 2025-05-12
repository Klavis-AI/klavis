# GitHubOAuthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.git_hub_o_auth_error_response import GitHubOAuthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GitHubOAuthErrorResponse from a JSON string
git_hub_o_auth_error_response_instance = GitHubOAuthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(GitHubOAuthErrorResponse.to_json())

# convert the object into a dict
git_hub_o_auth_error_response_dict = git_hub_o_auth_error_response_instance.to_dict()
# create an instance of GitHubOAuthErrorResponse from a dict
git_hub_o_auth_error_response_from_dict = GitHubOAuthErrorResponse.from_dict(git_hub_o_auth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


