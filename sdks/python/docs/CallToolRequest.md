# CallToolRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**server_url** | **str** | The full URL for connecting to the MCP server via Server-Sent Events (SSE) | 
**tool_name** | **str** | The name of the tool to call | 
**tool_args** | **Dict[str, object]** | The input parameters for the tool | [optional] 

## Example

```python
from klavis.models.call_tool_request import CallToolRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CallToolRequest from a JSON string
call_tool_request_instance = CallToolRequest.from_json(json)
# print the JSON string representation of the object
print(CallToolRequest.to_json())

# convert the object into a dict
call_tool_request_dict = call_tool_request_instance.to_dict()
# create an instance of CallToolRequest from a dict
call_tool_request_from_dict = CallToolRequest.from_dict(call_tool_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


