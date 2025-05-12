# CreateWhiteLabelingRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**client_id** | **str** | OAuth client ID | 
**client_secret** | **str** | OAuth client secret | 
**server_name** | [**WhiteLabelServerName**](WhiteLabelServerName.md) | Optional. The name of the server | 
**redirect_url** | **str** |  | [optional] 
**scope** | **str** |  | [optional] 
**account_id** | **str** |  | [optional] 

## Example

```python
from klavis.models.create_white_labeling_request import CreateWhiteLabelingRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateWhiteLabelingRequest from a JSON string
create_white_labeling_request_instance = CreateWhiteLabelingRequest.from_json(json)
# print the JSON string representation of the object
print(CreateWhiteLabelingRequest.to_json())

# convert the object into a dict
create_white_labeling_request_dict = create_white_labeling_request_instance.to_dict()
# create an instance of CreateWhiteLabelingRequest from a dict
create_white_labeling_request_from_dict = CreateWhiteLabelingRequest.from_dict(create_white_labeling_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


