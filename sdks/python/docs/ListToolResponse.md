# ListToolResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** | Whether the list tools request was successful | 
**tools** | **List[object]** | List of tools available for the MCP server | 

## Example

```python
from klavis.models.list_tool_response import ListToolResponse

# TODO update the JSON string below
json = "{}"
# create an instance of ListToolResponse from a JSON string
list_tool_response_instance = ListToolResponse.from_json(json)
# print the JSON string representation of the object
print(ListToolResponse.to_json())

# convert the object into a dict
list_tool_response_dict = list_tool_response_instance.to_dict()
# create an instance of ListToolResponse from a dict
list_tool_response_from_dict = ListToolResponse.from_dict(list_tool_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


