# WordPressOAuthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.word_press_o_auth_error_response import WordPressOAuthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of WordPressOAuthErrorResponse from a JSON string
word_press_o_auth_error_response_instance = WordPressOAuthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(WordPressOAuthErrorResponse.to_json())

# convert the object into a dict
word_press_o_auth_error_response_dict = word_press_o_auth_error_response_instance.to_dict()
# create an instance of WordPressOAuthErrorResponse from a dict
word_press_o_auth_error_response_from_dict = WordPressOAuthErrorResponse.from_dict(word_press_o_auth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


