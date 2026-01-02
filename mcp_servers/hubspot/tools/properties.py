"""
HubSpot Properties API tools with Klavis sanitization layer.

All responses are validated through Pydantic schemas.
All errors are sanitized to expose only HTTP status codes.
"""

import logging
import json
import ast
from typing import List, Dict, Any, Optional
from hubspot.crm.objects import Filter, FilterGroup, PublicObjectSearchRequest
from hubspot.crm.properties import PropertyCreate

from .base import get_hubspot_client, safe_api_call
from .schemas import (
    PropertyDefinition,
    PropertyList,
    SearchResults,
    SearchResultItem,
    CreateResult,
    normalize_deal
)
from .errors import (
    KlavisError,
    ValidationError,
    sanitize_exception
)

# Configure logging
logger = logging.getLogger(__name__)


def _build_dealstage_label_map(client) -> Dict[str, str]:
    """
    Build a mapping from deal stage ID to its human-readable label.
    """
    stage_id_to_label: Dict[str, str] = {}
    try:
        pipelines = client.crm.pipelines.pipelines_api.get_all("deals")
        for pipeline in getattr(pipelines, "results", []) or []:
            try:
                stages = client.crm.pipelines.pipeline_stages_api.get_all("deals", pipeline.id)
                for stage in getattr(stages, "results", []) or []:
                    if getattr(stage, "id", None) and getattr(stage, "label", None):
                        stage_id_to_label[stage.id] = stage.label
            except Exception:
                pass
    except Exception:
        pass
    return stage_id_to_label


async def hubspot_list_properties(object_type: str) -> PropertyList:
    """
    List all properties for a given object type.

    Parameters:
    - object_type: One of "contacts", "companies", "deals", or "tickets"

    Returns:
    - Klavis-normalized PropertyList schema
    """
    client = get_hubspot_client()
    
    logger.info(f"Executing hubspot_list_properties for object_type: {object_type}")
    
    try:
        props = safe_api_call(
            client.crm.properties.core_api.get_all,
            resource_type="property",
            object_type=object_type
        )
        
        # Normalize response through Klavis schema
        property_definitions = []
        for p in getattr(props, 'results', []) or []:
            property_definitions.append(PropertyDefinition(
                name=getattr(p, 'name', ''),
                label=getattr(p, 'label', ''),
                type=getattr(p, 'type', ''),
                field_type=getattr(p, 'field_type', '')
            ))
        
        logger.info(f"Successfully executed hubspot_list_properties for object_type: {object_type}")
        return PropertyList(
            properties=property_definitions,
            object_type=object_type
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="property")


async def hubspot_search_by_property(
    object_type: str,
    property_name: str,
    operator: str,
    value: str,
    properties: List[str],
    limit: int = 10
) -> SearchResults:
    """
    Search HubSpot objects by property.

    Parameters:
    - object_type: One of "contacts", "companies", "deals", or "tickets"
    - property_name: Field to search
    - operator: Filter operator
    - value: Value to search for
    - properties: List of fields to return
    - limit: Max number of results

    Returns:
    - Klavis-normalized SearchResults schema
    """
    client = get_hubspot_client()
    
    logger.info(f"Executing hubspot_search_by_property on {object_type}: {property_name} {operator} {value}")

    try:
        # Build Filter with correct fields depending on operator
        filter_kwargs = {"property_name": property_name, "operator": operator}

        # Operators that require no value
        if operator in {"HAS_PROPERTY", "NOT_HAS_PROPERTY"}:
            pass

        # Operators that require a list of values
        elif operator in {"IN", "NOT_IN"}:
            values_list: List[str] = []
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    values_list = [str(v) for v in parsed]
            except Exception:
                try:
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, list):
                        values_list = [str(v) for v in parsed]
                except Exception:
                    values_list = [v.strip().strip('"\'') for v in value.split(',') if v.strip()]

            if not values_list:
                raise ValidationError(resource_type=object_type)

            filter_kwargs["values"] = values_list

        # Between expects two endpoints
        elif operator == "BETWEEN":
            low = None
            high = None
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list) and len(parsed) >= 2:
                    low, high = str(parsed[0]), str(parsed[1])
            except Exception:
                try:
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, list) and len(parsed) >= 2:
                        low, high = str(parsed[0]), str(parsed[1])
                except Exception:
                    pass

            if low is None or high is None:
                raise ValidationError(resource_type=object_type)

            filter_kwargs["value"] = low
            filter_kwargs["high_value"] = high

        # All other operators use single value
        else:
            filter_kwargs["value"] = value

        search_request = PublicObjectSearchRequest(
            filter_groups=[
                FilterGroup(filters=[
                    Filter(**filter_kwargs)
                ])
            ],
            properties=list(properties),
            limit=limit
        )

        # Execute search based on object type
        if object_type == "contacts":
            results = safe_api_call(
                client.crm.contacts.search_api.do_search,
                resource_type="contact",
                public_object_search_request=search_request
            )
        elif object_type == "companies":
            results = safe_api_call(
                client.crm.companies.search_api.do_search,
                resource_type="company",
                public_object_search_request=search_request
            )
        elif object_type == "deals":
            results = safe_api_call(
                client.crm.deals.search_api.do_search,
                resource_type="deal",
                public_object_search_request=search_request
            )
        elif object_type == "tickets":
            results = safe_api_call(
                client.crm.tickets.search_api.do_search,
                resource_type="ticket",
                public_object_search_request=search_request
            )
        else:
            raise ValidationError(resource_type=object_type)

        logger.info(f"hubspot_search_by_property: Found {len(results.results)} result(s)")
        
        # Normalize results through Klavis schema
        search_items = []
        stage_label_map = None
        
        # Get stage labels for deals
        if object_type == "deals":
            stage_label_map = _build_dealstage_label_map(client)
        
        for obj in getattr(results, 'results', []) or []:
            obj_id = getattr(obj, 'id', '')
            props = getattr(obj, 'properties', {}) or {}
            
            # Convert properties to dict if needed
            if hasattr(props, '__dict__'):
                props = dict(props)
            else:
                props = dict(props) if props else {}
            
            # Enrich deals with stage labels
            if object_type == "deals" and stage_label_map:
                stage_id = props.get("dealstage")
                if stage_id and stage_id in stage_label_map:
                    props["dealstage_label"] = stage_label_map[stage_id]
            
            search_items.append(SearchResultItem(
                id=str(obj_id),
                properties=props
            ))
        
        return SearchResults(
            results=search_items,
            total=len(search_items)
        )

    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type=object_type)


async def hubspot_create_property(
    name: str,
    label: str,
    description: str,
    object_type: str
) -> CreateResult:
    """
    Create a new custom property for HubSpot objects.

    Parameters:
    - name: Internal name of the property
    - label: Display label
    - description: Property description
    - object_type: One of "contacts", "companies", "deals", or "tickets"

    Returns:
    - Klavis-normalized CreateResult schema
    """
    client = get_hubspot_client()
    
    try:
        logger.info(f"Creating property with name: {name}, object_type: {object_type}")

        group_map = {
            "contacts": "contactinformation",
            "companies": "companyinformation",
            "deals": "dealinformation",
            "tickets": "ticketinformation"
        }

        if object_type not in group_map:
            raise ValidationError(resource_type="property")

        group_name = group_map[object_type]

        property_create = PropertyCreate(
            name=name,
            label=label,
            group_name=group_name,
            type="string",
            field_type="text",
            description=description
        )

        safe_api_call(
            client.crm.properties.core_api.create,
            resource_type="property",
            object_type=object_type,
            property_create=property_create
        )

        logger.info("Successfully created property")
        return CreateResult(
            status="success",
            message="Property created successfully",
            resource_id=name
        )
    except KlavisError:
        raise
    except Exception as e:
        raise sanitize_exception(e, resource_type="property")
