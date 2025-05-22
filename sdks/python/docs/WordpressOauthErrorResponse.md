# WordpressOauthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.wordpress_oauth_error_response import WordpressOauthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of WordpressOauthErrorResponse from a JSON string
wordpress_oauth_error_response_instance = WordpressOauthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(WordpressOauthErrorResponse.to_json())

# convert the object into a dict
wordpress_oauth_error_response_dict = wordpress_oauth_error_response_instance.to_dict()
# create an instance of WordpressOauthErrorResponse from a dict
wordpress_oauth_error_response_from_dict = WordpressOauthErrorResponse.from_dict(wordpress_oauth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


