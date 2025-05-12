# SupabaseOAuthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.supabase_o_auth_error_response import SupabaseOAuthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SupabaseOAuthErrorResponse from a JSON string
supabase_o_auth_error_response_instance = SupabaseOAuthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(SupabaseOAuthErrorResponse.to_json())

# convert the object into a dict
supabase_o_auth_error_response_dict = supabase_o_auth_error_response_instance.to_dict()
# create an instance of SupabaseOAuthErrorResponse from a dict
supabase_o_auth_error_response_from_dict = SupabaseOAuthErrorResponse.from_dict(supabase_o_auth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


