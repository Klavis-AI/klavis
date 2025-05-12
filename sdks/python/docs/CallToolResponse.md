# CallToolResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** | Whether the API call was successful | 
**result** | [**CallToolResult**](CallToolResult.md) |  | [optional] 
**error** | **str** |  | [optional] 

## Example

```python
from klavis.models.call_tool_response import CallToolResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CallToolResponse from a JSON string
call_tool_response_instance = CallToolResponse.from_json(json)
# print the JSON string representation of the object
print(CallToolResponse.to_json())

# convert the object into a dict
call_tool_response_dict = call_tool_response_instance.to_dict()
# create an instance of CallToolResponse from a dict
call_tool_response_from_dict = CallToolResponse.from_dict(call_tool_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


