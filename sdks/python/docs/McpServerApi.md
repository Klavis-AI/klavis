# klavis.McpServerApi

All URIs are relative to *https://api.klavis.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**call_server_tool**](McpServerApi.md#call_server_tool) | **POST** /mcp-server/call-tool | Call Tool
[**create_server_instance**](McpServerApi.md#create_server_instance) | **POST** /mcp-server/instance/create | Create a Server Instance
[**delete_instance_auth**](McpServerApi.md#delete_instance_auth) | **DELETE** /mcp-server/instance/delete-auth/{instance_id} | Delete Auth data for a Server Instance
[**delete_server_instance**](McpServerApi.md#delete_server_instance) | **DELETE** /mcp-server/instance/delete/{instance_id} | Delete a Server Instance
[**get_all_mcp_servers**](McpServerApi.md#get_all_mcp_servers) | **GET** /mcp-server/servers | Get All Servers
[**get_server_instance**](McpServerApi.md#get_server_instance) | **GET** /mcp-server/instance/get/{instance_id} | Get Server Instance
[**get_server_tools**](McpServerApi.md#get_server_tools) | **GET** /mcp-server/tools/{server_name} | Get Tools
[**list_server_tools**](McpServerApi.md#list_server_tools) | **GET** /mcp-server/list-tools/{server_url} | List Tools
[**set_instance_auth_token**](McpServerApi.md#set_instance_auth_token) | **POST** /mcp-server/instance/set-auth-token | Set Auth Token


# **call_server_tool**
> CallToolResponse call_server_tool(call_tool_request)

Call Tool

Calls MCP server tool directly using the provided server URL.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.call_tool_request import CallToolRequest
from klavis.models.call_tool_response import CallToolResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)
    call_tool_request = klavis.CallToolRequest() # CallToolRequest | 

    try:
        # Call Tool
        api_response = api_instance.call_server_tool(call_tool_request)
        print("The response of McpServerApi->call_server_tool:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->call_server_tool: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **call_tool_request** | [**CallToolRequest**](CallToolRequest.md)|  | 

### Return type

[**CallToolResponse**](CallToolResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_server_instance**
> CreateServerResponse create_server_instance(create_server_request)

Create a Server Instance

Creates a Server-Sent Events (SSE) URL for a specified MCP server,
validating the request with an API key and user details.
Returns the existing server URL if it already exists for the user.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.create_server_request import CreateServerRequest
from klavis.models.create_server_response import CreateServerResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)
    create_server_request = klavis.CreateServerRequest() # CreateServerRequest | 

    try:
        # Create a Server Instance
        api_response = api_instance.create_server_instance(create_server_request)
        print("The response of McpServerApi->create_server_instance:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->create_server_instance: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_server_request** | [**CreateServerRequest**](CreateServerRequest.md)|  | 

### Return type

[**CreateServerResponse**](CreateServerResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_instance_auth**
> StatusResponse delete_instance_auth(instance_id)

Delete Auth data for a Server Instance

Deletes authentication metadata for a specific server connection instance.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.status_response import StatusResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)
    instance_id = 'instance_id_example' # str | The ID of the connection instance to delete auth for.

    try:
        # Delete Auth data for a Server Instance
        api_response = api_instance.delete_instance_auth(instance_id)
        print("The response of McpServerApi->delete_instance_auth:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->delete_instance_auth: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **instance_id** | **str**| The ID of the connection instance to delete auth for. | 

### Return type

[**StatusResponse**](StatusResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_server_instance**
> StatusResponse delete_server_instance(instance_id)

Delete a Server Instance

Completely removes a server connection instance using its unique ID,
deleting all associated data from the system.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.status_response import StatusResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)
    instance_id = 'instance_id_example' # str | The ID of the connection instance to delete.

    try:
        # Delete a Server Instance
        api_response = api_instance.delete_server_instance(instance_id)
        print("The response of McpServerApi->delete_server_instance:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->delete_server_instance: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **instance_id** | **str**| The ID of the connection instance to delete. | 

### Return type

[**StatusResponse**](StatusResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_mcp_servers**
> GetMcpServersResponse get_all_mcp_servers()

Get All Servers

Get all MCP servers with their basic information including id, name, description, and tools.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.get_mcp_servers_response import GetMcpServersResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)

    try:
        # Get All Servers
        api_response = api_instance.get_all_mcp_servers()
        print("The response of McpServerApi->get_all_mcp_servers:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->get_all_mcp_servers: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**GetMcpServersResponse**](GetMcpServersResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_server_instance**
> GetInstanceResponse get_server_instance(instance_id)

Get Server Instance

Checks the details of a specific server connection instance using its unique ID and API key,
returning server details like authentication status and associated server/platform info.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.get_instance_response import GetInstanceResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)
    instance_id = 'instance_id_example' # str | The ID of the connection instance whose status is being checked. This is returned by the Create API.

    try:
        # Get Server Instance
        api_response = api_instance.get_server_instance(instance_id)
        print("The response of McpServerApi->get_server_instance:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->get_server_instance: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **instance_id** | **str**| The ID of the connection instance whose status is being checked. This is returned by the Create API. | 

### Return type

[**GetInstanceResponse**](GetInstanceResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_server_tools**
> GetToolsResponse get_server_tools(server_name)

Get Tools

Get list of tool names for a specific MCP server.
Mainly used for querying metadata about the MCP server.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.get_tools_response import GetToolsResponse
from klavis.models.server_name import ServerName
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)
    server_name = klavis.ServerName() # ServerName | The name of the target MCP server.

    try:
        # Get Tools
        api_response = api_instance.get_server_tools(server_name)
        print("The response of McpServerApi->get_server_tools:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->get_server_tools: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **server_name** | [**ServerName**](.md)| The name of the target MCP server. | 

### Return type

[**GetToolsResponse**](GetToolsResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_server_tools**
> ListToolResponse list_server_tools(server_url)

List Tools

Lists all tools available for a specific remote MCP server by 
connecting to the server and calling the list_tools method.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.list_tool_response import ListToolResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)
    server_url = 'server_url_example' # str | The full URL for connecting to the MCP server via Server-Sent Events (SSE)

    try:
        # List Tools
        api_response = api_instance.list_server_tools(server_url)
        print("The response of McpServerApi->list_server_tools:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->list_server_tools: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **server_url** | **str**| The full URL for connecting to the MCP server via Server-Sent Events (SSE) | 

### Return type

[**ListToolResponse**](ListToolResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_instance_auth_token**
> StatusResponse set_instance_auth_token(set_auth_token_request)

Set Auth Token

Sets an authentication token for a specific instance.
This updates the auth_metadata for the specified instance.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.set_auth_token_request import SetAuthTokenRequest
from klavis.models.status_response import StatusResponse
from klavis.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.klavis.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = klavis.Configuration(
    host = "https://api.klavis.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = klavis.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with klavis.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = klavis.McpServerApi(api_client)
    set_auth_token_request = klavis.SetAuthTokenRequest() # SetAuthTokenRequest | 

    try:
        # Set Auth Token
        api_response = api_instance.set_instance_auth_token(set_auth_token_request)
        print("The response of McpServerApi->set_instance_auth_token:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling McpServerApi->set_instance_auth_token: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **set_auth_token_request** | [**SetAuthTokenRequest**](SetAuthTokenRequest.md)|  | 

### Return type

[**StatusResponse**](StatusResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

