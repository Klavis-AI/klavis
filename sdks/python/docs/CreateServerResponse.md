# CreateServerResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**server_url** | **str** | The full URL for connecting to the MCP server via Server-Sent Events (SSE), including the instance ID. | 
**instance_id** | **str** | The unique identifier for this specific server connection instance. | 

## Example

```python
from klavis.models.create_server_response import CreateServerResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CreateServerResponse from a JSON string
create_server_response_instance = CreateServerResponse.from_json(json)
# print the JSON string representation of the object
print(CreateServerResponse.to_json())

# convert the object into a dict
create_server_response_dict = create_server_response_instance.to_dict()
# create an instance of CreateServerResponse from a dict
create_server_response_from_dict = CreateServerResponse.from_dict(create_server_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


