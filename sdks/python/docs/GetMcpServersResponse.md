# GetMcpServersResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**servers** | [**List[McpServer]**](McpServer.md) |  | 

## Example

```python
from klavis.models.get_mcp_servers_response import GetMcpServersResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetMcpServersResponse from a JSON string
get_mcp_servers_response_instance = GetMcpServersResponse.from_json(json)
# print the JSON string representation of the object
print(GetMcpServersResponse.to_json())

# convert the object into a dict
get_mcp_servers_response_dict = get_mcp_servers_response_instance.to_dict()
# create an instance of GetMcpServersResponse from a dict
get_mcp_servers_response_from_dict = GetMcpServersResponse.from_dict(get_mcp_servers_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


