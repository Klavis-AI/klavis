# SupabaseOauthErrorResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** | Error message from the OAuth process | 

## Example

```python
from klavis.models.supabase_oauth_error_response import SupabaseOauthErrorResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SupabaseOauthErrorResponse from a JSON string
supabase_oauth_error_response_instance = SupabaseOauthErrorResponse.from_json(json)
# print the JSON string representation of the object
print(SupabaseOauthErrorResponse.to_json())

# convert the object into a dict
supabase_oauth_error_response_dict = supabase_oauth_error_response_instance.to_dict()
# create an instance of SupabaseOauthErrorResponse from a dict
supabase_oauth_error_response_from_dict = SupabaseOauthErrorResponse.from_dict(supabase_oauth_error_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


