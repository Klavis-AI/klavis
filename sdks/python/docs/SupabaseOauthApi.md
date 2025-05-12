# klavis.SupabaseOauthApi

All URIs are relative to *https://api.klavis.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**authorize_supabase**](SupabaseOauthApi.md#authorize_supabase) | **GET** /oauth/supabase/authorize | Authorize Supabase
[**refresh_supabase_token_oauth_supabase_refresh_token_post**](SupabaseOauthApi.md#refresh_supabase_token_oauth_supabase_refresh_token_post) | **POST** /oauth/supabase/refresh_token | Refresh Supabase Token
[**supabase_o_auth_callback**](SupabaseOauthApi.md#supabase_o_auth_callback) | **GET** /oauth/supabase/callback | Supabase Callback


# **authorize_supabase**
> object authorize_supabase(instance_id, client_id=client_id, redirect_url=redirect_url)

Authorize Supabase

Start Supabase OAuth flow

Parameters:
- instance_id: Identifier for the instance requesting authorization
- client_id: Optional client ID for white labeling
- redirect_url: Optional URL to redirect to after authorization completes

### Example


```python
import klavis
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)


# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.SupabaseOauthApi(api_client)
    instance_id = 'instance_id_example' # str | Unique identifier for the client instance requesting authorization
    client_id = 'client_id_example' # str | Client ID for white labeling, if not provided will use default credentials (optional)
    redirect_url = 'redirect_url_example' # str | Optional URL to redirect to after authorization completes (optional)

    try:
        # Authorize Supabase
        api_response = api_instance.authorize_supabase(instance_id, client_id=client_id, redirect_url=redirect_url)
        print("The response of SupabaseOauthApi->authorize_supabase:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SupabaseOauthApi->authorize_supabase: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **instance_id** | **str**| Unique identifier for the client instance requesting authorization | 
 **client_id** | **str**| Client ID for white labeling, if not provided will use default credentials | [optional] 
 **redirect_url** | **str**| Optional URL to redirect to after authorization completes | [optional] 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **refresh_supabase_token_oauth_supabase_refresh_token_post**
> SupabaseOAuthSuccessResponse refresh_supabase_token_oauth_supabase_refresh_token_post(instance_id)

Refresh Supabase Token

Refresh an expired Supabase access token using the stored refresh token

Parameters:
- instance_id: Identifier for the instance requesting token refresh

Returns:
- Success response if token was refreshed successfully, error response otherwise

### Example


```python
import klavis
from klavis.models.supabase_o_auth_success_response import SupabaseOAuthSuccessResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)


# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.SupabaseOauthApi(api_client)
    instance_id = 'instance_id_example' # str | Unique identifier for the client instance requesting token refresh

    try:
        # Refresh Supabase Token
        api_response = api_instance.refresh_supabase_token_oauth_supabase_refresh_token_post(instance_id)
        print("The response of SupabaseOauthApi->refresh_supabase_token_oauth_supabase_refresh_token_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SupabaseOauthApi->refresh_supabase_token_oauth_supabase_refresh_token_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **instance_id** | **str**| Unique identifier for the client instance requesting token refresh | 

### Return type

[**SupabaseOAuthSuccessResponse**](SupabaseOAuthSuccessResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**400** | Bad Request |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **supabase_o_auth_callback**
> SupabaseOAuthSuccessResponse supabase_o_auth_callback(code=code, state=state, error=error, error_description=error_description)

Supabase Callback

Handles the callback from Supabase OAuth authorization.

### Example


```python
import klavis
from klavis.models.supabase_o_auth_success_response import SupabaseOAuthSuccessResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)


# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.SupabaseOauthApi(api_client)
    code = 'code_example' # str | Authorization code returned by Supabase (optional)
    state = 'state_example' # str | State parameter containing encoded authorization data (optional)
    error = 'error_example' # str | Error code returned by Supabase, if any (optional)
    error_description = 'error_description_example' # str | Detailed error description from Supabase, if any (optional)

    try:
        # Supabase Callback
        api_response = api_instance.supabase_o_auth_callback(code=code, state=state, error=error, error_description=error_description)
        print("The response of SupabaseOauthApi->supabase_o_auth_callback:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SupabaseOauthApi->supabase_o_auth_callback: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **code** | **str**| Authorization code returned by Supabase | [optional] 
 **state** | **str**| State parameter containing encoded authorization data | [optional] 
 **error** | **str**| Error code returned by Supabase, if any | [optional] 
 **error_description** | **str**| Detailed error description from Supabase, if any | [optional] 

### Return type

[**SupabaseOAuthSuccessResponse**](SupabaseOAuthSuccessResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**400** | Bad Request |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

