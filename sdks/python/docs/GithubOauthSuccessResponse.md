# GithubOauthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | 
**message** | **str** | Success message | 
**data** | **Dict[str, object]** |  | [optional] 

## Example

```python
from klavis.models.github_oauth_success_response import GithubOauthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GithubOauthSuccessResponse from a JSON string
github_oauth_success_response_instance = GithubOauthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(GithubOauthSuccessResponse.to_json())

# convert the object into a dict
github_oauth_success_response_dict = github_oauth_success_response_instance.to_dict()
# create an instance of GithubOauthSuccessResponse from a dict
github_oauth_success_response_from_dict = GithubOauthSuccessResponse.from_dict(github_oauth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


