# CallToolResult

The server's response to a tool call.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**content** | **List[object]** | The content of the tool call | 
**is_error** | **bool** | Whether the tool call was successful | [optional] [default to False]

## Example

```python
from klavis.models.call_tool_result import CallToolResult

# TODO update the JSON string below
json = "{}"
# create an instance of CallToolResult from a JSON string
call_tool_result_instance = CallToolResult.from_json(json)
# print the JSON string representation of the object
print(CallToolResult.to_json())

# convert the object into a dict
call_tool_result_dict = call_tool_result_instance.to_dict()
# create an instance of CallToolResult from a dict
call_tool_result_from_dict = CallToolResult.from_dict(call_tool_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


