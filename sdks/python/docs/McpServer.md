# McpServer


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**name** | **str** |  | 
**description** | **str** |  | [optional] 
**tools** | [**List[ServerTool]**](ServerTool.md) |  | [optional] 

## Example

```python
from klavis.models.mcp_server import McpServer

# TODO update the JSON string below
json = "{}"
# create an instance of McpServer from a JSON string
mcp_server_instance = McpServer.from_json(json)
# print the JSON string representation of the object
print(McpServer.to_json())

# convert the object into a dict
mcp_server_dict = mcp_server_instance.to_dict()
# create an instance of McpServer from a dict
mcp_server_from_dict = McpServer.from_dict(mcp_server_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


