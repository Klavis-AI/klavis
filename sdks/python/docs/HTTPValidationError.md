# HTTPValidationError


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**detail** | [**List[ValidationError]**](ValidationError.md) |  | [optional] 

## Example

```python
from klavis.models.http_validation_error import HTTPValidationError

# TODO update the JSON string below
json = "{}"
# create an instance of HTTPValidationError from a JSON string
http_validation_error_instance = HTTPValidationError.from_json(json)
# print the JSON string representation of the object
print(HTTPValidationError.to_json())

# convert the object into a dict
http_validation_error_dict = http_validation_error_instance.to_dict()
# create an instance of HTTPValidationError from a dict
http_validation_error_from_dict = HTTPValidationError.from_dict(http_validation_error_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


