# SetAuthTokenRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**instance_id** | **str** | The unique identifier for the connection instance | 
**auth_token** | **str** | The authentication token to save | 

## Example

```python
from klavis.models.set_auth_token_request import SetAuthTokenRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SetAuthTokenRequest from a JSON string
set_auth_token_request_instance = SetAuthTokenRequest.from_json(json)
# print the JSON string representation of the object
print(SetAuthTokenRequest.to_json())

# convert the object into a dict
set_auth_token_request_dict = set_auth_token_request_instance.to_dict()
# create an instance of SetAuthTokenRequest from a dict
set_auth_token_request_from_dict = SetAuthTokenRequest.from_dict(set_auth_token_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


