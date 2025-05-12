# SupabaseOAuthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.supabase_o_auth_success_response import SupabaseOAuthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SupabaseOAuthSuccessResponse from a JSON string
supabase_o_auth_success_response_instance = SupabaseOAuthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(SupabaseOAuthSuccessResponse.to_json())

# convert the object into a dict
supabase_o_auth_success_response_dict = supabase_o_auth_success_response_instance.to_dict()
# create an instance of SupabaseOAuthSuccessResponse from a dict
supabase_o_auth_success_response_from_dict = SupabaseOAuthSuccessResponse.from_dict(supabase_o_auth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


