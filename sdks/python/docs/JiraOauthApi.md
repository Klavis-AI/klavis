# klavis.JiraOauthApi

All URIs are relative to *https://api.klavis.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**authorize_jira**](JiraOauthApi.md#authorize_jira) | **GET** /oauth/jira/authorize | Authorize Jira
[**jira_o_auth_callback**](JiraOauthApi.md#jira_o_auth_callback) | **GET** /oauth/jira/callback | Jira Callback
[**refresh_jira_token_oauth_jira_refresh_token_post**](JiraOauthApi.md#refresh_jira_token_oauth_jira_refresh_token_post) | **POST** /oauth/jira/refresh_token | Refresh Jira Token


# **authorize_jira**
> object authorize_jira(instance_id, client_id=client_id, scope=scope, redirect_url=redirect_url)

Authorize Jira

Start Jira OAuth flow

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
    api_instance = klavis.JiraOauthApi(api_client)
    instance_id = 'instance_id_example' # str | Unique identifier for the client instance requesting authorization
    client_id = 'client_id_example' # str | Client ID for white labeling, if not provided will use default credentials (optional)
    scope = 'scope_example' # str | Optional OAuth scopes to request (comma-separated string) (optional)
    redirect_url = 'redirect_url_example' # str | Optional URL to redirect to after authorization completes (optional)

    try:
        # Authorize Jira
        api_response = api_instance.authorize_jira(instance_id, client_id=client_id, scope=scope, redirect_url=redirect_url)
        print("The response of JiraOauthApi->authorize_jira:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling JiraOauthApi->authorize_jira: %s\n" % e)
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

# **jira_o_auth_callback**
> JiraOauthSuccessResponse jira_o_auth_callback(code=code, state=state, error=error, error_description=error_description)

Jira Callback

Handles the callback from Jira OAuth authorization.

### Example


```python
import klavis
from klavis.models.jira_oauth_success_response import JiraOauthSuccessResponse
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
    api_instance = klavis.JiraOauthApi(api_client)
    code = 'code_example' # str | Authorization code returned by Jira (optional)
    state = 'state_example' # str | State parameter containing encoded authorization data (optional)
    error = 'error_example' # str | Error code returned by Jira, if any (optional)
    error_description = 'error_description_example' # str | Detailed error description from Jira, if any (optional)

    try:
        # Jira Callback
        api_response = api_instance.jira_o_auth_callback(code=code, state=state, error=error, error_description=error_description)
        print("The response of JiraOauthApi->jira_o_auth_callback:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling JiraOauthApi->jira_o_auth_callback: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **code** | **str**| Authorization code returned by Jira | [optional] 
 **state** | **str**| State parameter containing encoded authorization data | [optional] 
 **error** | **str**| Error code returned by Jira, if any | [optional] 
 **error_description** | **str**| Detailed error description from Jira, if any | [optional] 

### Return type

[**JiraOauthSuccessResponse**](JiraOauthSuccessResponse.md)

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

# **refresh_jira_token_oauth_jira_refresh_token_post**
> JiraOauthSuccessResponse refresh_jira_token_oauth_jira_refresh_token_post(instance_id)

Refresh Jira Token

Refresh an expired Jira access token using the stored refresh token

Parameters:
- instance_id: Identifier for the instance requesting token refresh

Returns:
- Success response if token was refreshed successfully, error response otherwise

### Example


```python
import klavis
from klavis.models.jira_oauth_success_response import JiraOauthSuccessResponse
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
    api_instance = klavis.JiraOauthApi(api_client)
    instance_id = 'instance_id_example' # str | Unique identifier for the client instance requesting token refresh

    try:
        # Refresh Jira Token
        api_response = api_instance.refresh_jira_token_oauth_jira_refresh_token_post(instance_id)
        print("The response of JiraOauthApi->refresh_jira_token_oauth_jira_refresh_token_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling JiraOauthApi->refresh_jira_token_oauth_jira_refresh_token_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **instance_id** | **str**| Unique identifier for the client instance requesting token refresh | 

### Return type

[**JiraOauthSuccessResponse**](JiraOauthSuccessResponse.md)

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

