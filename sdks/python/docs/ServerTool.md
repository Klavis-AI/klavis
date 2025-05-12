# ServerTool


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**description** | **str** |  | 

## Example

```python
from klavis.models.server_tool import ServerTool

# TODO update the JSON string below
json = "{}"
# create an instance of ServerTool from a JSON string
server_tool_instance = ServerTool.from_json(json)
# print the JSON string representation of the object
print(ServerTool.to_json())

# convert the object into a dict
server_tool_dict = server_tool_instance.to_dict()
# create an instance of ServerTool from a dict
server_tool_from_dict = ServerTool.from_dict(server_tool_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


