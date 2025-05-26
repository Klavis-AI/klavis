# SupabaseOauthSuccessResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** | Status of the OAuth process | [optional] [default to 'success']
**message** | **str** | Success message | 

## Example

```python
from klavis.models.supabase_oauth_success_response import SupabaseOauthSuccessResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SupabaseOauthSuccessResponse from a JSON string
supabase_oauth_success_response_instance = SupabaseOauthSuccessResponse.from_json(json)
# print the JSON string representation of the object
print(SupabaseOauthSuccessResponse.to_json())

# convert the object into a dict
supabase_oauth_success_response_dict = supabase_oauth_success_response_instance.to_dict()
# create an instance of SupabaseOauthSuccessResponse from a dict
supabase_oauth_success_response_from_dict = SupabaseOauthSuccessResponse.from_dict(supabase_oauth_success_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


