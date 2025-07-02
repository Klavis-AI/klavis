import logging
from hubspot.crm.objects import Filter, FilterGroup, PublicObjectSearchRequest
from hubspot.crm.properties import PropertyCreate
from .base import get_hubspot_client

# Configure logging
logger = logging.getLogger(__name__)

async def hubspot_list_properties(object_type: str) -> list[dict]:
    """
    List all properties for a given object type.

    Parameters:
    - object_type: One of "contacts", "companies", "deals", or "tickets"

    Returns:
    - List of property metadata
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    logger.info(f"Executing hubspot_list_properties for object_type: {object_type}")
    try:
        props = client.crm.properties.core_api.get_all(object_type)
        logger.info(f"Successfully Executed hubspot_list_properties for object_type: {object_type}")
        return [
            {
                "name": p.name,
                "label": p.label,
                "type": p.type,
                "field_type": p.field_type
            }
            for p in props.results
        ]
    except Exception as e:
        logger.exception(f"Error executing hubspot_list_properties: {e}")
        raise e

async def hubspot_search_by_property(
    object_type: str,
    property_name: str,
    operator: str,
    value: str,
    properties: list[str],
    limit: int = 10
) -> list[dict]:
    """
    Search HubSpot objects by property.

    Parameters:
    - object_type: One of "contacts", "companies", "deals", or "tickets"
    - property_name: Field to search
    - operator: Filter operator (see note below)
    - value: Value to search for
    - properties: List of fields to return
    - limit: Max number of results

    Returns:
    - List of result dictionaries

    Note:
    Supported operators (with expected value format and behavior):

    - EQ (Equal): Matches records where the property exactly equals the given value.
      Example: "lifecyclestage" EQ "customer"

    - NEQ (Not Equal): Matches records where the property does not equal the given value.
      Example: "country" NEQ "India"

    - GT (Greater Than): Matches records where the property is greater than the given value.
      Example: "numberofemployees" GT "100"

    - GTE (Greater Than or Equal): Matches records where the property is greater than or equal to the given value.
      Example: "revenue" GTE "50000"

    - LT (Less Than): Matches records where the property is less than the given value.
      Example: "score" LT "75"

    - LTE (Less Than or Equal): Matches records where the property is less than or equal to the given value.
      Example: "createdate" LTE "2023-01-01T00:00:00Z"

    - BETWEEN: Matches records where the property is within a specified range.
      Value must be a list of two values [start, end].
      Example: "createdate" BETWEEN ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]

    - IN: Matches records where the property is one of the values in the list.
      Value must be a list.
      Example: "industry" IN ["Technology", "Healthcare"]

    - NOT_IN: Matches records where the property is none of the values in the list.
      Value must be a list.
      Example: "state" NOT_IN ["CA", "NY"]

    - CONTAINS_TOKEN: Matches records where the property contains the given word/token (case-insensitive).
      Example: "notes" CONTAINS_TOKEN "demo"

    - NOT_CONTAINS_TOKEN: Matches records where the property does NOT contain the given word/token.
      Example: "comments" NOT_CONTAINS_TOKEN "urgent"

    - STARTS_WITH: Matches records where the property value starts with the given substring.
      Example: "firstname" STARTS_WITH "Jo"

    - ENDS_WITH: Matches records where the property value ends with the given substring.
      Example: "email" ENDS_WITH "@gmail.com"

    - ON_OR_AFTER: For datetime fields, matches records where the date is the same or after the given value.
      Example: "createdate" ON_OR_AFTER "2024-01-01T00:00:00Z"

    - ON_OR_BEFORE: For datetime fields, matches records where the date is the same or before the given value.
      Example: "closedate" ON_OR_BEFORE "2024-12-31T23:59:59Z"

    Value type rules:
    - If the operator expects a list (e.g., IN, BETWEEN), pass value as a JSON-encoded string list: '["a", "b"]'
    - All other operators expect a single string (even for numbers or dates)
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    logger.info(f"Executing hubspot_search_by_property on {object_type}: {property_name} {operator} {value}")

    try:
        search_request = PublicObjectSearchRequest(
            filter_groups=[
                FilterGroup(filters=[
                    Filter(property_name=property_name, operator=operator, value=value)
                ])
            ],
            properties=list(properties),
            limit=limit
        )

        if object_type == "contacts":
            results =  client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
        elif object_type == "companies":
            results =  client.crm.companies.search_api.do_search(public_object_search_request=search_request)
        elif object_type == "deals":
            results =  client.crm.deals.search_api.do_search(public_object_search_request=search_request)
        elif object_type == "tickets":
            results =  client.crm.tickets.search_api.do_search(public_object_search_request=search_request)
        else:
            raise ValueError(f"Unsupported object type: {object_type}")

        logger.info(f"hubspot_search_by_property: Found {len(results.results)} result(s)")
        return [obj.properties for obj in results.results]

    except Exception as e:
        logger.exception(f"Error executing hubspot_search_by_property: {e}")
        return (f"Error executing hubspot_search_by_property: {e}")

async def hubspot_create_property(name: str, label: str, description: str, object_type: str) -> str:
    """
    Create a new custom property for HubSpot objects.
    """
    client = get_hubspot_client()
    if not client:
        raise ValueError("HubSpot client not available. Please check authentication.")
    
    try:
        logger.info(f"Creating property with name: {name}, label: {label}, object_type: {object_type}")

        group_map = {
            "contacts": "contactinformation",
            "companies": "companyinformation",
            "deals": "dealinformation",
            "tickets": "ticketinformation"
        }

        if object_type not in group_map:
            raise ValueError(f"Invalid object_type '{object_type}'")

        group_name = group_map[object_type]

        property = PropertyCreate(
            name=name,
            label=label,
            group_name=group_name,
            type="string",        # backend data type
            field_type="text",    # frontend input type
            description=description
        )

        client.crm.properties.core_api.create(
            object_type=object_type,
            property_create=property
        )

        logger.info("Successfully created property")
        return "Property Created"
    except Exception as e:
        logger.error(f"Error creating property: {e}")
        raise e

