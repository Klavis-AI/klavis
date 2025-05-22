# klavis.WordpressOauthApi

All URIs are relative to *https://api.klavis.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**authorize_wordpress**](WordpressOauthApi.md#authorize_wordpress) | **GET** /oauth/wordpress/authorize | Authorize Wordpress
[**wordpress_o_auth_callback**](WordpressOauthApi.md#wordpress_o_auth_callback) | **GET** /oauth/wordpress/callback | Wordpress Callback


# **authorize_wordpress**
> object authorize_wordpress(instance_id, client_id=client_id, scope=scope, redirect_url=redirect_url)

Authorize Wordpress

Start WordPress OAuth flow

Parameters:
- instance_id: Identifier for the instance requesting authorization
- client_id: Optional client ID for white labeling
- scope: Optional scopes to request (comma-separated)
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
    api_instance = klavis.WordpressOauthApi(api_client)
    instance_id = 'instance_id_example' # str | Unique identifier for the client instance requesting authorization
    client_id = 'client_id_example' # str | Client ID for white labeling, if not provided will use default credentials (optional)
    scope = 'scope_example' # str | Optional OAuth scopes to request (comma-separated string) (optional)
    redirect_url = 'redirect_url_example' # str | Optional URL to redirect to after authorization completes (optional)

    try:
        # Authorize Wordpress
        api_response = api_instance.authorize_wordpress(instance_id, client_id=client_id, scope=scope, redirect_url=redirect_url)
        print("The response of WordpressOauthApi->authorize_wordpress:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling WordpressOauthApi->authorize_wordpress: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **instance_id** | **str**| Unique identifier for the client instance requesting authorization | 
 **client_id** | **str**| Client ID for white labeling, if not provided will use default credentials | [optional] 
 **scope** | **str**| Optional OAuth scopes to request (comma-separated string) | [optional] 
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

# **wordpress_o_auth_callback**
> WordpressOauthSuccessResponse wordpress_o_auth_callback(code=code, state=state, error=error, error_description=error_description)

Wordpress Callback

Handles the callback from WordPress OAuth authorization.

### Example


```python
import klavis
from klavis.models.wordpress_oauth_success_response import WordpressOauthSuccessResponse
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
    api_instance = klavis.WordpressOauthApi(api_client)
    code = 'code_example' # str | Authorization code returned by WordPress (optional)
    state = 'state_example' # str | State parameter containing encoded authorization data (optional)
    error = 'error_example' # str | Error code returned by WordPress, if any (optional)
    error_description = 'error_description_example' # str | Detailed error description from WordPress, if any (optional)

    try:
        # Wordpress Callback
        api_response = api_instance.wordpress_o_auth_callback(code=code, state=state, error=error, error_description=error_description)
        print("The response of WordpressOauthApi->wordpress_o_auth_callback:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling WordpressOauthApi->wordpress_o_auth_callback: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **code** | **str**| Authorization code returned by WordPress | [optional] 
 **state** | **str**| State parameter containing encoded authorization data | [optional] 
 **error** | **str**| Error code returned by WordPress, if any | [optional] 
 **error_description** | **str**| Detailed error description from WordPress, if any | [optional] 

### Return type

[**WordpressOauthSuccessResponse**](WordpressOauthSuccessResponse.md)

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

