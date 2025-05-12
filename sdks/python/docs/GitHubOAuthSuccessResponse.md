# GitHubOAuthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | 
**message** | **str** | Success message | 
**data** | **Dict[str, object]** |  | [optional] 

## Example

```python
from klavis.models.git_hub_o_auth_success_response import GitHubOAuthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GitHubOAuthSuccessResponse from a JSON string
git_hub_o_auth_success_response_instance = GitHubOAuthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(GitHubOAuthSuccessResponse.to_json())

# convert the object into a dict
git_hub_o_auth_success_response_dict = git_hub_o_auth_success_response_instance.to_dict()
# create an instance of GitHubOAuthSuccessResponse from a dict
git_hub_o_auth_success_response_from_dict = GitHubOAuthSuccessResponse.from_dict(git_hub_o_auth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


