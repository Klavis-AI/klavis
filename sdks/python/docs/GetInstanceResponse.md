# GetInstanceResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**instance_id** | **str** |  | [optional] 
**is_authenticated** | **bool** | Indicates whether the instance is authenticated successfully. | [optional] [default to False]
**server_name** | **str** | The name of the MCP server associated with the instance. | [optional] [default to '']
**platform** | **str** | The platform associated with the instance (e.g., &#39;Den&#39;, &#39;CamelAI&#39;). | [optional] [default to '']
**external_user_id** | **str** | The user&#39;s identifier on the external platform. | [optional] [default to '']

## Example

```python
from klavis.models.get_instance_response import GetInstanceResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetInstanceResponse from a JSON string
get_instance_response_instance = GetInstanceResponse.from_json(json)
# print the JSON string representation of the object
print(GetInstanceResponse.to_json())

# convert the object into a dict
get_instance_response_dict = get_instance_response_instance.to_dict()
# create an instance of GetInstanceResponse from a dict
get_instance_response_from_dict = GetInstanceResponse.from_dict(get_instance_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


