# WhiteLabelingResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** | Whether the operation was successful | 
**data** | **Dict[str, object]** |  | [optional] 
**message** | **str** |  | [optional] 

## Example

```python
from klavis.models.white_labeling_response import WhiteLabelingResponse

# TODO update the JSON string below
json = "{}"
# create an instance of WhiteLabelingResponse from a JSON string
white_labeling_response_instance = WhiteLabelingResponse.from_json(json)
# print the JSON string representation of the object
print(WhiteLabelingResponse.to_json())

# convert the object into a dict
white_labeling_response_dict = white_labeling_response_instance.to_dict()
# create an instance of WhiteLabelingResponse from a dict
white_labeling_response_from_dict = WhiteLabelingResponse.from_dict(white_labeling_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


