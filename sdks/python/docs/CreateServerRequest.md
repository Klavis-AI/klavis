# CreateServerRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**server_name** | [**ServerName**](ServerName.md) | The name of the target MCP server. | 
**user_id** | **str** | The identifier for the user requesting the server URL. | 
**platform_name** | **str** | The name of the platform associated with the user (e.g., &#39;Den&#39;, &#39;CamelAI&#39;). | 

## Example

```python
from klavis.models.create_server_request import CreateServerRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateServerRequest from a JSON string
create_server_request_instance = CreateServerRequest.from_json(json)
# print the JSON string representation of the object
print(CreateServerRequest.to_json())

# convert the object into a dict
create_server_request_dict = create_server_request_instance.to_dict()
# create an instance of CreateServerRequest from a dict
create_server_request_from_dict = CreateServerRequest.from_dict(create_server_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


