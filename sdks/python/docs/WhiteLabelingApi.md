# klavis.WhiteLabelingApi

All URIs are relative to *https://api.klavis.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_white_labeling**](WhiteLabelingApi.md#create_white_labeling) | **POST** /white-labeling/create | Create
[**get_white_labeling_by_client_id**](WhiteLabelingApi.md#get_white_labeling_by_client_id) | **GET** /white-labeling/get/{client_id} | Get


# **create_white_labeling**
> WhiteLabelingResponse create_white_labeling(create_white_labeling_request)

Create

Saves OAuth white labeling information, or updates existing information if the `client_id` matches.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.create_white_labeling_request import CreateWhiteLabelingRequest
from klavis.models.white_labeling_response import WhiteLabelingResponse
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
    api_instance = klavis.WhiteLabelingApi(api_client)
    create_white_labeling_request = klavis.CreateWhiteLabelingRequest() # CreateWhiteLabelingRequest | 

    try:
        # Create
        api_response = api_instance.create_white_labeling(create_white_labeling_request)
        print("The response of WhiteLabelingApi->create_white_labeling:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling WhiteLabelingApi->create_white_labeling: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_white_labeling_request** | [**CreateWhiteLabelingRequest**](CreateWhiteLabelingRequest.md)|  | 

### Return type

[**WhiteLabelingResponse**](WhiteLabelingResponse.md)

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

# **get_white_labeling_by_client_id**
> WhiteLabelingResponse get_white_labeling_by_client_id(client_id)

Get

Retrieves white labeling information for a specific OAuth client ID.

### Example

* Bearer Authentication (HTTPBearer):

```python
import klavis
from klavis.models.white_labeling_response import WhiteLabelingResponse
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
    api_instance = klavis.WhiteLabelingApi(api_client)
    client_id = 'client_id_example' # str | 

    try:
        # Get
        api_response = api_instance.get_white_labeling_by_client_id(client_id)
        print("The response of WhiteLabelingApi->get_white_labeling_by_client_id:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling WhiteLabelingApi->get_white_labeling_by_client_id: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **client_id** | **str**|  | 

### Return type

[**WhiteLabelingResponse**](WhiteLabelingResponse.md)

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

