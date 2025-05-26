# WordpressOauthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.wordpress_oauth_success_response import WordpressOauthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of WordpressOauthSuccessResponse from a JSON string
wordpress_oauth_success_response_instance = WordpressOauthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(WordpressOauthSuccessResponse.to_json())

# convert the object into a dict
wordpress_oauth_success_response_dict = wordpress_oauth_success_response_instance.to_dict()
# create an instance of WordpressOauthSuccessResponse from a dict
wordpress_oauth_success_response_from_dict = WordpressOauthSuccessResponse.from_dict(wordpress_oauth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


