# WordPressOAuthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.word_press_o_auth_success_response import WordPressOAuthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of WordPressOAuthSuccessResponse from a JSON string
word_press_o_auth_success_response_instance = WordPressOAuthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(WordPressOAuthSuccessResponse.to_json())

# convert the object into a dict
word_press_o_auth_success_response_dict = word_press_o_auth_success_response_instance.to_dict()
# create an instance of WordPressOAuthSuccessResponse from a dict
word_press_o_auth_success_response_from_dict = WordPressOAuthSuccessResponse.from_dict(word_press_o_auth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


