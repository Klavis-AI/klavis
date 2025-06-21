import contextlib
import os
from contextvars import ContextVar
from collections.abc import AsyncIterator
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv
import json
from hubspot import HubSpot
import logging
from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest
from hubspot.crm.properties import PropertyCreate
from hubspot.crm.contacts import SimplePublicObjectInputForCreate, SimplePublicObjectInput
from hubspot.crm.companies import SimplePublicObjectInputForCreate
from hubspot.crm.companies import SimplePublicObjectInput

logger = logging.getLogger(__name__)

client = HubSpot(access_token="<access_token>")

load_dotenv()

HUBSPOT_MCP_SERVER_PORT = int(os.getenv("HUBSPOT_MCP_SERVER_PORT", "5000"))

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')


class RetryableToolError(Exception):
    def __init__(self, message: str, additional_prompt_content: str = "", retry_after_ms: int = 1000,
                 developer_message: str = ""):
        super().__init__(message)
        self.additional_prompt_content = additional_prompt_content
        self.retry_after_ms = retry_after_ms
        self.developer_message = developer_message


# =======================================Tools Start=======================================

async def hubspot_list_properties(object_type: str) -> list[dict]:
    """
    List all properties for a given object type.

    Parameters:
    - object_type: One of "contacts", "companies", "deals", or "tickets"

    Returns:
    - List of property metadata
    """
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
            results = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
        elif object_type == "companies":
            results = client.crm.companies.search_api.do_search(public_object_search_request=search_request)
        elif object_type == "deals":
            results = client.crm.deals.search_api.do_search(public_object_search_request=search_request)
        elif object_type == "tickets":
            results = client.crm.tickets.search_api.do_search(public_object_search_request=search_request)
        else:
            raise ValueError(f"Unsupported object type: {object_type}")

        logger.info(f"hubspot_search_by_property: Found {len(results.results)} result(s)")
        return [obj.properties for obj in results.results]

    except Exception as e:
        logger.exception(f"Error executing hubspot_search_by_property: {e}")
        return (f"Error executing hubspot_search_by_property: {e}")


# <-------------------------- Contacts -------------------------->

async def get_HubSpot_contacts(limit: int = 10):
    """
    Fetch a list of contacts from HubSpot.

    Parameters:
    - limit: Number of contacts to retrieve

    Returns:
    - Paginated contacts response
    """
    try:
        logger.info(f"Fetching up to {limit} contacts from HubSpot")
        result = client.crm.contacts.basic_api.get_page(limit=limit)
        logger.info("Successfully fetched contacts")
        return result
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}")
        raise e


async def get_HubSpot_contact_by_id(contact_id: str):
    """
    Get a specific contact by ID.

    Parameters:
    - contact_id: ID of the contact to retrieve

    Returns:
    - Contact object
    """
    try:
        logger.info(f"Fetching contact with ID: {contact_id}")
        result = client.crm.contacts.basic_api.get_by_id(contact_id)
        logger.info("Successfully fetched contact")
        return result
    except Exception as e:
        logger.error(f"Error fetching contact by ID: {e}")
        raise e


async def hubspot_create_property(name: str, label: str, description: str) -> str:
    """
    Create a new custom property for contacts.

    Parameters:
    - name: Internal property name
    - label: Display label for the property
    - description: Description of the property

    Returns:
    - Confirmation message
    """
    try:
        logger.info(f"Creating property with name: {name}, label: {label}")
        property = PropertyCreate(
            name=name,
            label=label,
            group_name="contactinformation",
            type="string",
            description=description
        )
        client.crm.properties.core_api.create(
            object_type="contacts",
            property_create=property
        )
        logger.info("Successfully created property")
        return "Property Created"
    except Exception as e:
        logger.error(f"Error creating property: {e}")
        raise e


async def hubspot_delete_contant_by_id(contact_id: str) -> str:
    """
    Delete a contact by ID.

    Parameters:
    - contact_id: ID of the contact to delete

    Returns:
    - Status message
    """
    try:
        logger.info(f"Deleting contact with ID: {contact_id}")
        client.crm.contacts.basic_api.archive(contact_id)
        logger.info("Successfully deleted contact")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        raise e


async def hubspot_create_contact(properties: str) -> str:
    """
    Create a new contact using JSON string of properties.

    Parameters:
    - properties: JSON string containing contact fields

    Returns:
    - Status message
    """
    try:
        properties = json.loads(properties)
        logger.info(f"Creating contact with properties: {properties}")
        data = SimplePublicObjectInputForCreate(properties=properties)
        client.crm.contacts.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Successfully created contact")
        return "Created"
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise e


async def hubspot_update_contact_by_id(contact_id: str, updates: str) -> str:
    """
    Update a contact by ID.

    Parameters:
    - contact_id: ID of the contact to update
    - updates: JSON string of properties to update

    Returns:
    - Status message
    """
    try:
        updates = json.loads(updates)
        logger.info(f"Updating contact ID: {contact_id} with updates: {updates}")
        data = SimplePublicObjectInput(properties=updates)
        client.crm.contacts.basic_api.update(contact_id, data)
        logger.info("Successfully updated contact")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return f"Error occurred: {e}"


# <-------------------------- Companies -------------------------->

async def hubspot_create_companies(properties: str) -> str:
    """
    Create a new company using JSON string of properties.

    Parameters:
    - properties: JSON string of company fields

    Returns:
    - Status message
    """
    try:
        logger.info("Creating company...")
        properties = json.loads(properties)
        data = SimplePublicObjectInputForCreate(properties=properties)
        client.crm.companies.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Company created successfully.")
        return "Created"
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        return f"Error occurred: {e}"


async def get_HubSpot_companies(limit: int = 10):
    """
    Fetch a list of companies from HubSpot.

    Parameters:
    - limit: Number of companies to retrieve

    Returns:
    - Paginated companies response
    """
    try:
        logger.info(f"Fetching up to {limit} companies...")
        result = client.crm.companies.basic_api.get_page(limit=limit)
        logger.info(f"Fetched {len(result.results)} companies successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        return None


async def get_HubSpot_companies_by_id(company_id: str):
    """
    Get a company by ID.

    Parameters:
    - company_id: ID of the company

    Returns:
    - Company object
    """
    try:
        logger.info(f"Fetching company with ID: {company_id}...")
        result = client.crm.companies.basic_api.get_by_id(company_id)
        logger.info(f"Fetched company ID: {company_id} successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching company by ID: {e}")
        return None


async def hubspot_update_company_by_id(company_id: str, updates: str) -> str:
    """
    Update a company by ID.

    Parameters:
    - company_id: ID of the company to update
    - updates: JSON string of property updates

    Returns:
    - Status message
    """
    try:
        logger.info(f"Updating company ID: {company_id}...")
        updates = json.loads(updates)
        update = SimplePublicObjectInput(properties=updates)
        client.crm.companies.basic_api.update(company_id, update)
        logger.info(f"Company ID: {company_id} updated successfully.")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return f"Error occurred: {e}"


async def hubspot_delete_company_by_id(company_id: str) -> str:
    """
    Delete a company by ID.

    Parameters:
    - company_id: ID of the company

    Returns:
    - Status message
    """
    try:
        logger.info(f"Deleting company ID: {company_id}...")
        client.crm.companies.basic_api.archive(company_id)
        logger.info(f"Company ID: {company_id} deleted successfully.")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting company: {e}")
        return f"Error occurred: {e}"


# <--------------------------Deals-------------------------->

async def get_HubSpot_deals(limit: int = 10):
    """
    Fetch a list of deals from HubSpot.

    Parameters:
    - limit: Number of deals to return

    Returns:
    - List of deal records
    """
    try:
        logger.info(f"Fetching up to {limit} deals...")
        result = client.crm.deals.basic_api.get_page(limit=limit)
        logger.info(f"Fetched {len(result.results)} deals successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching deals: {e}")
        return None


async def get_HubSpot_deal_by_id(deal_id: str):
    """
    Fetch a deal by its ID.

    Parameters:
    - deal_id: HubSpot deal ID

    Returns:
    - Deal object
    """
    try:
        logger.info(f"Fetching deal ID: {deal_id}...")
        result = client.crm.deals.basic_api.get_by_id(deal_id)
        logger.info(f"Fetched deal ID: {deal_id} successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching deal by ID: {e}")
        return None


async def hubspot_create_deal(properties: str):
    """
    Create a new deal.

    Parameters:
    - properties: JSON string of deal properties

    Returns:
    - Newly created deal
    """
    try:
        logger.info("Creating a new deal...")
        props = json.loads(properties)
        data = SimplePublicObjectInputForCreate(properties=props)
        result = client.crm.deals.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Deal created successfully.")
        return result
    except Exception as e:
        logger.error(f"Error creating deal: {e}")
        return f"Error occurred: {e}"


async def hubspot_update_deal_by_id(deal_id: str, updates: str):
    """
    Update a deal by ID.

    Parameters:
    - deal_id: HubSpot deal ID
    - updates: JSON string of updated fields

    Returns:
    - "Done" on success, error message otherwise
    """
    try:
        logger.info(f"Updating deal ID: {deal_id}...")
        data = SimplePublicObjectInput(properties=json.loads(updates))
        client.crm.deals.basic_api.update(deal_id, data)
        logger.info(f"Deal ID: {deal_id} updated successfully.")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed for deal ID {deal_id}: {e}")
        return f"Error occurred: {e}"


async def hubspot_delete_deal_by_id(deal_id: str):
    """
    Delete a deal by ID.

    Parameters:
    - deal_id: HubSpot deal ID

    Returns:
    - None
    """
    try:
        logger.info(f"Deleting deal ID: {deal_id}...")
        client.crm.deals.basic_api.archive(deal_id)
        logger.info(f"Deal ID: {deal_id} deleted successfully.")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting deal: {e}")
        return f"Error occurred: {e}"


# <--------------------------Tickets-------------------------->

async def get_HubSpot_tickets(limit: int = 10):
    """
    Fetch a list of tickets from HubSpot.

    Parameters:
    - limit: Number of tickets to return

    Returns:
    - List of ticket records
    """
    try:
        logger.info(f"Fetching up to {limit} tickets...")
        result = client.crm.tickets.basic_api.get_page(limit=limit)
        logger.info(f"Fetched {len(result.results)} tickets successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}")
        return None


async def get_HubSpot_ticket_by_id(ticket_id: str):
    """
    Fetch a ticket by its ID.

    Parameters:
    - ticket_id: HubSpot ticket ID

    Returns:
    - Ticket object
    """
    try:
        logger.info(f"Fetching ticket ID: {ticket_id}...")
        result = client.crm.tickets.basic_api.get_by_id(ticket_id)
        logger.info(f"Fetched ticket ID: {ticket_id} successfully.")
        return result
    except Exception as e:
        logger.error(f"Error fetching ticket by ID: {e}")
        return None


async def hubspot_create_ticket(properties: str):
    """
    Create a new ticket.

    Parameters:
    - properties: JSON string of ticket properties

    Returns:
    - Newly created ticket
    """
    try:
        logger.info("Creating new ticket...")
        props = json.loads(properties)
        data = SimplePublicObjectInputForCreate(properties=props)
        result = client.crm.tickets.basic_api.create(simple_public_object_input_for_create=data)
        logger.info("Ticket created successfully.")
        return result
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return f"Error occurred: {e}"


async def hubspot_update_ticket_by_id(ticket_id: str, updates: str):
    """
    Update a ticket by ID.

    Parameters:
    - ticket_id: HubSpot ticket ID
    - updates: JSON string of updated fields

    Returns:
    - "Done" on success, error message otherwise
    """
    try:
        logger.info(f"Updating ticket ID: {ticket_id}...")
        data = SimplePublicObjectInput(properties=json.loads(updates))
        client.crm.tickets.basic_api.update(ticket_id, data)
        logger.info(f"Ticket ID: {ticket_id} updated successfully.")
        return "Done"
    except Exception as e:
        logger.error(f"Update failed for ticket ID {ticket_id}: {e}")
        return f"Error occurred: {e}"


async def hubspot_delete_ticket_by_id(ticket_id: str):
    """
    Delete a ticket by ID.

    Parameters:
    - ticket_id: HubSpot ticket ID

    Returns:
    - None
    """
    try:
        logger.info(f"Deleting ticket ID: {ticket_id}...")
        client.crm.tickets.basic_api.archive(ticket_id)
        logger.info(f"Ticket ID: {ticket_id} deleted successfully.")
        return "Deleted"
    except Exception as e:
        logger.error(f"Error deleting ticket ID {ticket_id}: {e}")
        return f"Error occurred: {e}"


# =======================================Tools Finish=======================================

@click.command()
@click.option("--port", default=HUBSPOT_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(
        port: int,
        log_level: str,
        json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("hubspot-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="hubspot_list_properties",
                description="List all property metadata for a HubSpot object type like contacts, companies, deals, or tickets.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "object_type": {
                            "type": "string",
                            "description": "The HubSpot object type. One of 'contacts', 'companies', 'deals', or 'tickets'.",
                            "enum": ["contacts", "companies", "deals", "tickets"]
                        }
                    },
                    "required": ["object_type"]
                }
            ),
            types.Tool(
                name="hubspot_search_by_property",
                description="Search HubSpot objects by a specific property and value using a filter operator.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "object_type": {
                            "type": "string",
                            "description": "The object type to search (contacts, companies, deals, tickets)."
                        },
                        "property_name": {
                            "type": "string",
                            "description": "The property name to filter by."
                        },
                        "operator": {
                            "type": "string",
                            "description": """Filter operator
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
                                            - All other operators expect a single string (even for numbers or dates)"""
                        },
                        "value": {
                            "type": "string",
                            "description": "The value to match against the property."
                        },
                        "properties": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of properties to return in the result."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of results to return."
                        }
                    },
                    "required": ["object_type", "property_name", "operator", "value", "properties"]
                }
            ),
            types.Tool(
                name="get_HubSpot_contacts",
                description="Fetch a list of contacts from HubSpot.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of contacts to retrieve. Defaults to 10.",
                            "default": 10,
                            "minimum": 1
                        }
                    }
                }
            ),
            types.Tool(
                name="get_HubSpot_contact_by_id",
                description="Get a specific contact by HubSpot contact ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "The HubSpot contact ID."
                        }
                    },
                    "required": ["contact_id"]
                }
            ),
            types.Tool(
                name="hubspot_create_property",
                description="Create a new custom property for HubSpot contacts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Internal name of the property."
                        },
                        "label": {
                            "type": "string",
                            "description": "Label shown in the HubSpot UI."
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the property."
                        }
                    },
                    "required": ["name", "label", "description"]
                }
            ),
            types.Tool(
                name="hubspot_delete_contant_by_id",
                description="Delete a contact from HubSpot by contact ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "The HubSpot contact ID to delete."
                        }
                    },
                    "required": ["contact_id"]
                }
            ),
            types.Tool(
                name="hubspot_create_contact",
                description="Create a new contact using a JSON string of properties.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "properties": {
                            "type": "string",
                            "description": "JSON string containing contact fields and values."
                        }
                    },
                    "required": ["properties"]
                }
            ),
            types.Tool(
                name="hubspot_update_contact_by_id",
                description="Update a contact in HubSpot by contact ID using JSON property updates.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "HubSpot contact ID to update."
                        },
                        "updates": {
                            "type": "string",
                            "description": "JSON string with fields to update."
                        }
                    },
                    "required": ["contact_id", "updates"]
                }
            ),
            types.Tool(
                name="hubspot_create_companies",
                description="Create a new company using a JSON string of fields.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "properties": {
                            "type": "string",
                            "description": "JSON string containing company fields and values."
                        }
                    },
                    "required": ["properties"]
                }
            ),
            types.Tool(
                name="get_HubSpot_companies",
                description="Fetch a list of companies from HubSpot.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of companies to retrieve. Defaults to 10.",
                            "default": 10,
                            "minimum": 1
                        }
                    }
                }
            ),
            types.Tool(
                name="get_HubSpot_companies_by_id",
                description="Get a company from HubSpot by company ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "string",
                            "description": "The HubSpot company ID."
                        }
                    },
                    "required": ["company_id"]
                }
            ),
            types.Tool(
                name="hubspot_update_company_by_id",
                description="Update an existing company by ID using JSON property updates.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "string",
                            "description": "The HubSpot company ID to update."
                        },
                        "updates": {
                            "type": "string",
                            "description": "JSON string with fields to update."
                        }
                    },
                    "required": ["company_id", "updates"]
                }
            ),
            types.Tool(
                name="hubspot_delete_company_by_id",
                description="Delete a company from HubSpot by company ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "string",
                            "description": "The HubSpot company ID to delete."
                        }
                    },
                    "required": ["company_id"]
                }
            ),
            types.Tool(
                name="get_HubSpot_deals",
                description="Fetch a list of deals from HubSpot.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of deals to retrieve. Defaults to 10.",
                            "default": 10,
                            "minimum": 1
                        }
                    }
                }
            ),
            types.Tool(
                name="get_HubSpot_deal_by_id",
                description="Fetch a deal by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deal_id": {
                            "type": "string",
                            "description": "The HubSpot deal ID."
                        }
                    },
                    "required": ["deal_id"]
                }
            ),
            types.Tool(
                name="hubspot_create_deal",
                description="Create a new deal using a JSON string of properties.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "properties": {
                            "type": "string",
                            "description": "JSON string with fields to create the deal."
                        }
                    },
                    "required": ["properties"]
                }
            ),
            types.Tool(
                name="hubspot_update_deal_by_id",
                description="Update an existing deal using a JSON string of updated properties.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deal_id": {
                            "type": "string",
                            "description": "The ID of the deal to update."
                        },
                        "updates": {
                            "type": "string",
                            "description": "JSON string of the properties to update."
                        }
                    },
                    "required": ["deal_id", "updates"]
                }
            ),
            types.Tool(
                name="hubspot_delete_deal_by_id",
                description="Delete a deal from HubSpot by deal ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deal_id": {
                            "type": "string",
                            "description": "The ID of the deal to delete."
                        }
                    },
                    "required": ["deal_id"]
                }
            ),
            types.Tool(
                name="get_HubSpot_tickets",
                description="Fetch a list of tickets from HubSpot.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of tickets to retrieve. Defaults to 10.",
                            "default": 10,
                            "minimum": 1
                        }
                    }
                }
            ),
            types.Tool(
                name="get_HubSpot_ticket_by_id",
                description="Fetch a ticket by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "The HubSpot ticket ID."
                        }
                    },
                    "required": ["ticket_id"]
                }
            ),
            types.Tool(
                name="hubspot_create_ticket",
                description="Create a new ticket using a JSON string of properties.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "properties": {
                            "type": "string",
                            "description": "JSON string with fields to create the ticket."
                        }
                    },
                    "required": ["properties"]
                }
            ),
            types.Tool(
                name="hubspot_update_ticket_by_id",
                description="Update an existing ticket using a JSON string of updated properties.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "The ID of the ticket to update."
                        },
                        "updates": {
                            "type": "string",
                            "description": "JSON string of the properties to update."
                        }
                    },
                    "required": ["ticket_id", "updates"]
                }
            ),
            types.Tool(
                name="hubspot_delete_ticket_by_id",
                description="Delete a ticket from HubSpot by ticket ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "The ID of the ticket to delete."
                        }
                    },
                    "required": ["ticket_id"]
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
            name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            if name == "hubspot_list_properties":
                object_type = arguments.get("object_type")
                result = await hubspot_list_properties(object_type)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "hubspot_search_by_property":
                object_type = arguments.get("object_type")
                property_name = arguments.get("property_name")
                operator = arguments.get("operator")
                value = arguments.get("value")
                properties = arguments.get("properties", [])
                limit = arguments.get("limit", 10)

                if not all([object_type, property_name, operator, value, properties]):
                    return [types.TextContent(
                        type="text",
                        text="Missing required parameters. Required: object_type, property_name, operator, value, properties."
                    )]

                result = await hubspot_search_by_property(
                    object_type, property_name, operator, value, properties, limit
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


            elif name == "get_HubSpot_contacts":
                limit = arguments.get("limit", 10)
                result = await get_HubSpot_contacts(limit)
                return [types.TextContent(type="text", text=str(result))]

            elif name == "get_HubSpot_contact_by_id":
                contact_id = arguments["contact_id"]
                result = await get_HubSpot_contact_by_id(contact_id)
                return [types.TextContent(type="text", text=str(result))]

            elif name == "hubspot_create_property":
                result = await hubspot_create_property(
                    name=arguments["name"],
                    label=arguments["label"],
                    description=arguments["description"]
                )
                return [types.TextContent(type="text", text=result)]

            elif name == "hubspot_delete_contant_by_id":
                contact_id = arguments["contact_id"]
                result = await hubspot_delete_contant_by_id(contact_id)
                return [types.TextContent(type="text", text=result)]

            elif name == "hubspot_create_contact":
                result = await hubspot_create_contact(arguments["properties"])
                return [types.TextContent(type="text", text=result)]

            elif name == "hubspot_update_contact_by_id":
                result = await hubspot_update_contact_by_id(
                    contact_id=arguments["contact_id"],
                    updates=arguments["updates"]
                )
                return [types.TextContent(type="text", text=result)]

            elif name == "hubspot_create_companies":
                result = await hubspot_create_companies(arguments["properties"])
                return [types.TextContent(type="text", text=result)]

            elif name == "get_HubSpot_companies":
                limit = arguments.get("limit", 10)
                result = await get_HubSpot_companies(limit)
                return [types.TextContent(type="text", text=str(result))]

            elif name == "get_HubSpot_companies_by_id":
                company_id = arguments["company_id"]
                result = await get_HubSpot_companies_by_id(company_id)
                return [types.TextContent(type="text", text=str(result))]

            elif name == "hubspot_update_company_by_id":
                result = await hubspot_update_company_by_id(
                    company_id=arguments["company_id"],
                    updates=arguments["updates"]
                )
                return [types.TextContent(type="text", text=result)]

            elif name == "hubspot_delete_company_by_id":
                result = await hubspot_delete_company_by_id(arguments["company_id"])
                return [types.TextContent(type="text", text=result)]

            elif name == "get_HubSpot_deals":
                limit = arguments.get("limit", 10)
                result = await get_HubSpot_deals(limit)
                return [types.TextContent(type="text", text=str(result))]

            elif name == "get_HubSpot_deal_by_id":
                deal_id = arguments["deal_id"]
                result = await get_HubSpot_deal_by_id(deal_id)
                return [types.TextContent(type="text", text=str(result))]

            elif name == "hubspot_create_deal":
                result = await hubspot_create_deal(arguments["properties"])
                return [types.TextContent(type="text", text=str(result))]

            elif name == "hubspot_update_deal_by_id":
                result = await hubspot_update_deal_by_id(
                    deal_id=arguments["deal_id"],
                    updates=arguments["updates"]
                )
                return [types.TextContent(type="text", text=result)]

            elif name == "hubspot_delete_deal_by_id":
                result = await hubspot_delete_deal_by_id(arguments["deal_id"])
                return [types.TextContent(type="text", text="Deleted")]

            elif name == "get_HubSpot_tickets":
                limit = arguments.get("limit", 10)
                result = await get_HubSpot_tickets(limit)
                return [types.TextContent(type="text", text=str(result))]

            elif name == "get_HubSpot_ticket_by_id":
                ticket_id = arguments["ticket_id"]
                result = await get_HubSpot_ticket_by_id(ticket_id)
                return [types.TextContent(type="text", text=str(result))]

            elif name == "hubspot_create_ticket":
                result = await hubspot_create_ticket(arguments["properties"])
                return [types.TextContent(type="text", text=str(result))]

            elif name == "hubspot_update_ticket_by_id":
                result = await hubspot_update_ticket_by_id(
                    ticket_id=arguments["ticket_id"],
                    updates=arguments["updates"]
                )
                return [types.TextContent(type="text", text=result)]

            elif name == "hubspot_delete_ticket_by_id":
                result = await hubspot_delete_ticket_by_id(arguments["ticket_id"])
                return [types.TextContent(type="text", text="Deleted")]

            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

            # Set up SSE transport

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")

        # Extract auth token from headers (allow None - will be handled at tool level)
        auth_token = request.headers.get('x-auth-token')

        # Set the auth token in context for this request (can be None)
        token = auth_token_context.set(auth_token or "")
        try:
            async with sse.connect_sse(
                    request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)

        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
            scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")

        # Extract auth token from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')

        # Set the auth token in context for this request (can be None/empty)
        token = auth_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),

            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    main()