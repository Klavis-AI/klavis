# GetToolsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tools** | [**List[ServerTool]**](ServerTool.md) | List of available tools with their descriptions | [optional] 

## Example

```python
from klavis.models.get_tools_response import GetToolsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetToolsResponse from a JSON string
get_tools_response_instance = GetToolsResponse.from_json(json)
# print the JSON string representation of the object
print(GetToolsResponse.to_json())

# convert the object into a dict
get_tools_response_dict = get_tools_response_instance.to_dict()
# create an instance of GetToolsResponse from a dict
get_tools_response_from_dict = GetToolsResponse.from_dict(get_tools_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


