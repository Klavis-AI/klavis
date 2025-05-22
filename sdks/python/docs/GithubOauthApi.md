# klavis.GithubOauthApi

All URIs are relative to *https://api.klavis.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**authorize_github**](GithubOauthApi.md#authorize_github) | **GET** /oauth/github/authorize | Authorize Github
[**github_o_auth_callback**](GithubOauthApi.md#github_o_auth_callback) | **GET** /oauth/github/callback | Github Callback


# **authorize_github**
> object authorize_github(instance_id, client_id=client_id, scope=scope, redirect_url=redirect_url)

Authorize Github

Start GitHub OAuth flow

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
    api_instance = klavis.GithubOauthApi(api_client)
    instance_id = 'instance_id_example' # str | Unique identifier for the client instance requesting authorization
    client_id = 'client_id_example' # str | Client ID for white labeling, if not provided will use default credentials (optional)
    scope = 'scope_example' # str | Optional OAuth scopes to request (comma-separated string) (optional)
    redirect_url = 'redirect_url_example' # str | Optional URL to redirect to after authorization completes (optional)

    try:
        # Authorize Github
        api_response = api_instance.authorize_github(instance_id, client_id=client_id, scope=scope, redirect_url=redirect_url)
        print("The response of GithubOauthApi->authorize_github:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GithubOauthApi->authorize_github: %s\n" % e)
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

# **github_o_auth_callback**
> GithubOauthSuccessResponse github_o_auth_callback(code=code, state=state, error=error, error_description=error_description)

Github Callback

Handles the callback from GitHub OAuth authorization.

### Example


```python
import klavis
from klavis.models.github_oauth_success_response import GithubOauthSuccessResponse
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
    api_instance = klavis.GithubOauthApi(api_client)
    code = 'code_example' # str | Authorization code returned by GitHub (optional)
    state = 'state_example' # str | State parameter containing encoded authorization data (optional)
    error = 'error_example' # str | Error code returned by GitHub, if any (optional)
    error_description = 'error_description_example' # str | Detailed error description from GitHub, if any (optional)

    try:
        # Github Callback
        api_response = api_instance.github_o_auth_callback(code=code, state=state, error=error, error_description=error_description)
        print("The response of GithubOauthApi->github_o_auth_callback:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GithubOauthApi->github_o_auth_callback: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **code** | **str**| Authorization code returned by GitHub | [optional] 
 **state** | **str**| State parameter containing encoded authorization data | [optional] 
 **error** | **str**| Error code returned by GitHub, if any | [optional] 
 **error_description** | **str**| Detailed error description from GitHub, if any | [optional] 

### Return type

[**GithubOauthSuccessResponse**](GithubOauthSuccessResponse.md)

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

