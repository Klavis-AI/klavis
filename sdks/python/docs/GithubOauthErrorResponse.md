# GithubOauthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.github_oauth_error_response import GithubOauthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GithubOauthErrorResponse from a JSON string
github_oauth_error_response_instance = GithubOauthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(GithubOauthErrorResponse.to_json())

# convert the object into a dict
github_oauth_error_response_dict = github_oauth_error_response_instance.to_dict()
# create an instance of GithubOauthErrorResponse from a dict
github_oauth_error_response_from_dict = GithubOauthErrorResponse.from_dict(github_oauth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


