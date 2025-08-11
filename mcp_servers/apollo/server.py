import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict

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

from tools import (
    # base
    auth_token_context,

    # accounts
    apollo_view_account,
    apollo_update_account,
    apollo_create_account,
    apollo_search_accounts,
    apollo_list_account_stages,
    apollo_update_account_stage_bulk,
    apollo_update_account_owner_bulk,

    # calls
    apollo_update_call,
    apollo_search_calls,
    apollo_create_call_record,

    # contacts
    apollo_create_contact,
    apollo_update_contact,
    apollo_search_contacts,
    apollo_update_contact_stages,
    apollo_list_contact_stages,
    apollo_update_contact_owners,

    # deals
    apollo_update_deal,
    apollo_view_deal,
    apollo_create_deal,
    apollo_list_all_deals,
    apollo_list_deal_stages,

    # enrichment
    apollo_organisation_enrichment,
    apollo_bulk_organisation_enrichment,

    # miscellaneous
    apollo_list_email_accounts,
    apollo_list_users,
    apollo_list_all_custom_fields,
    apollo_get_all_lists_and_tags,
    apollo_view_api_usage_stats,

    # search
    apollo_organization_job_postings,
    apollo_news_articles_search,

    # sequences
    apollo_search_sequences,
    apollo_check_email_stats,
    apollo_search_outreach_emails,
    apollo_update_contact_status_in_sequence,
    apollo_add_contacts_to_sequence,

    # tasks
    apollo_create_tasks,
    apollo_search_tasks,
)


# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

APOLLO_MCP_SERVER_PORT = int(os.getenv("APOLLO_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option("--port", default=APOLLO_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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

    # Create the MCP server instance
    app = Server("apollo-mcp-server")

#-------------------------------------------------------------------------------

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            #accounts.py ----------------------------
            types.Tool(
                name="apollo_create_account",
                description="Create a new account in Apollo by adding a company to your team's Apollo database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Human-readable name of the account (e.g., 'The Irish Copywriters')."
                        },
                        "domain": {
                            "type": "string",
                            "description": "Domain name of the account without 'www.' (e.g., 'apollo.io')."
                        },
                        "owner_id": {
                            "type": "string",
                            "description": "ID of the account owner within your Apollo team."
                        },
                        "account_stage_id": {
                            "type": "string",
                            "description": "Apollo ID for the account stage to assign the account."
                        },
                        "phone": {
                            "type": "string",
                            "description": "Primary phone number for the account, any format accepted."
                        },
                        "raw_address": {
                            "type": "string",
                            "description": "Corporate location like city, state, country."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_update_account",
                description="Update details of an existing account in Apollo using its account ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Apollo ID of the account to update."
                        },
                        "name": {
                            "type": "string",
                            "description": "New human-readable name for the account."
                        },
                        "domain": {
                            "type": "string",
                            "description": "New domain name without 'www.'."
                        },
                        "owner_id": {
                            "type": "string",
                            "description": "New owner ID within your Apollo team."
                        },
                        "account_stage_id": {
                            "type": "string",
                            "description": "New account stage ID."
                        },
                        "raw_address": {
                            "type": "string",
                            "description": "Updated corporate location (city, state, country)."
                        },
                        "phone": {
                            "type": "string",
                            "description": "Updated primary phone number in any format."
                        }
                    },
                    "required": ["account_id"]
                }
            ),
            types.Tool(
                name="apollo_search_accounts",
                description="Search for accounts explicitly added to your team's Apollo database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "q_organization_name": {
                            "type": "string",
                            "description": "Keywords to match part of the account name."
                        },
                        "account_stage_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of account stage IDs to filter results."
                        },
                        "sort_by_field": {
                            "type": "string",
                            "enum": ["account_last_activity_date", "account_created_at", "account_updated_at"],
                            "description": "Field to sort by."
                        },
                        "sort_ascending": {
                            "type": "boolean",
                            "description": "Sort order; true for ascending, false for descending (requires sort_by_field)."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number of results to retrieve."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page for pagination."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_view_account",
                description="Retrieve full details of an existing account in Apollo by account ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Apollo ID of the account to retrieve."
                        }
                    },
                    "required": ["account_id"]
                }
            ),
            types.Tool(
                name="apollo_update_account_stage_bulk",
                description="Update the account stage for multiple accounts in Apollo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Apollo account IDs to update."
                        },
                        "account_stage_id": {
                            "type": "string",
                            "description": "Apollo ID of the new account stage to assign."
                        }
                    },
                    "required": ["account_ids", "account_stage_id"]
                }
            ),
            types.Tool(
                name="apollo_update_account_owner_bulk",
                description="Assign multiple accounts to a different owner in Apollo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Apollo account IDs to reassign."
                        },
                        "owner_id": {
                            "type": "string",
                            "description": "Apollo user ID of the new account owner."
                        }
                    },
                    "required": ["account_ids", "owner_id"]
                }
            ),
            types.Tool(
                name="apollo_list_account_stages",
                description="Retrieve all account stage IDs available in your Apollo team.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),

            #calls.py--------------------------------------
            types.Tool(
                name="apollo_create_call_record",
                description="Create a call record in Apollo to log calls made via outside systems.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "logged": {
                            "type": "boolean",
                            "description": "True to log the call in Apollo."
                        },
                        "user_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Apollo user IDs of the caller(s)."
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "Apollo contact ID of the called person."
                        },
                        "account_id": {
                            "type": "string",
                            "description": "Apollo account ID to associate with the call."
                        },
                        "to_number": {
                            "type": "string",
                            "description": "Phone number dialed."
                        },
                        "from_number": {
                            "type": "string",
                            "description": "Phone number that placed the call."
                        },
                        "status": {
                            "type": "string",
                            "description": "Call status ('queued', 'ringing', 'in-progress', 'completed', 'no_answer', 'failed', 'busy')."
                        },
                        "start_time": {
                            "type": "string",
                            "description": "ISO 8601 formatted start time (GMT or with offset)."
                        },
                        "end_time": {
                            "type": "string",
                            "description": "ISO 8601 formatted end time (GMT or with offset)."
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration of the call in seconds."
                        },
                        "phone_call_purpose_id": {
                            "type": "string",
                            "description": "Call purpose ID in your Apollo account."
                        },
                        "phone_call_outcome_id": {
                            "type": "string",
                            "description": "Call outcome ID in your Apollo account."
                        },
                        "note": {
                            "type": "string",
                            "description": "Additional note for the call record."
                        }
                    },
                    "required": ["logged", "user_ids", "contact_id"]
                }
            ),
            types.Tool(
                name="apollo_search_calls",
                description="Search for calls made or received by your team in Apollo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date_range_max": {
                            "type": "string",
                            "description": "Upper bound date (YYYY-MM-DD) for search."
                        },
                        "date_range_min": {
                            "type": "string",
                            "description": "Lower bound date (YYYY-MM-DD) for search."
                        },
                        "duration_max": {
                            "type": "integer",
                            "description": "Max call duration in seconds."
                        },
                        "duration_min": {
                            "type": "integer",
                            "description": "Min call duration in seconds."
                        },
                        "inbound": {
                            "type": "string",
                            "enum": ["incoming", "outgoing"],
                            "description": "Filter by call direction."
                        },
                        "user_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Apollo user IDs involved in calls."
                        },
                        "contact_label_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of contact IDs involved in calls."
                        },
                        "phone_call_purpose_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by call purpose IDs."
                        },
                        "phone_call_outcome_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by call outcome IDs."
                        },
                        "q_keywords": {
                            "type": "string",
                            "description": "Keywords to narrow call search."
                        },
                        "page": {
                            "type": ["integer", "string"],
                            "description": "Page number for pagination."
                        },
                        "per_page": {
                            "type": ["integer", "string"],
                            "description": "Number of results per page."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_update_call",
                description="Update an existing call record in Apollo by call ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "call_id": {
                            "type": "string",
                            "description": "Apollo ID of the call record to update."
                        },
                        "logged": {
                            "type": "boolean",
                            "description": "True to create an individual record for the call."
                        },
                        "user_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Apollo user IDs of the caller(s)."
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "Apollo contact ID of the called person."
                        },
                        "account_id": {
                            "type": "string",
                            "description": "Apollo account ID associated with the call."
                        },
                        "to_number": {
                            "type": "string",
                            "description": "Phone number dialed."
                        },
                        "from_number": {
                            "type": "string",
                            "description": "Phone number that placed the call."
                        },
                        "status": {
                            "type": "string",
                            "description": "Call status ('queued', 'ringing', 'in-progress', 'completed', 'no_answer', 'failed', 'busy')."
                        },
                        "start_time": {
                            "type": "string",
                            "description": "ISO 8601 formatted start time (GMT or with offset)."
                        },
                        "end_time": {
                            "type": "string",
                            "description": "ISO 8601 formatted end time (GMT or with offset)."
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration of the call in seconds."
                        },
                        "phone_call_purpose_id": {
                            "type": "string",
                            "description": "Call purpose ID in your Apollo account."
                        },
                        "phone_call_outcome_id": {
                            "type": "string",
                            "description": "Call outcome ID in your Apollo account."
                        },
                        "note": {
                            "type": "string",
                            "description": "Additional note for the call record."
                        }
                    },
                    "required": ["call_id"]
                }
            ),

            #contacts.py---------------------------------------------
            types.Tool(
                name="apollo_create_contact",
                description="Create a new contact explicitly added to your team's Apollo database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "Contact's first name (e.g., 'Tim')."
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Contact's last name (e.g., 'Zheng')."
                        },
                        "organization_name": {
                            "type": "string",
                            "description": "Contact's current employer name (e.g., 'apollo')."
                        },
                        "title": {
                            "type": "string",
                            "description": "Contact's current job title (e.g., 'senior research analyst')."
                        },
                        "account_id": {
                            "type": "string",
                            "description": "Apollo account ID to assign the contact."
                        },
                        "email": {
                            "type": "string",
                            "description": "Contact's email address."
                        },
                        "website_url": {
                            "type": "string",
                            "description": "Corporate website URL (full URL, no social links)."
                        },
                        "label_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lists to add the contact to; auto-creates new lists if needed."
                        },
                        "contact_stage_id": {
                            "type": "string",
                            "description": "Apollo ID for the contact stage to assign."
                        },
                        "present_raw_address": {
                            "type": "string",
                            "description": "Contact's personal location (city, state, country)."
                        },
                        "direct_phone": {
                            "type": "string",
                            "description": "Primary phone number (any format)."
                        },
                        "corporate_phone": {
                            "type": "string",
                            "description": "Work/office phone number."
                        },
                        "mobile_phone": {
                            "type": "string",
                            "description": "Mobile phone number."
                        },
                        "home_phone": {
                            "type": "string",
                            "description": "Home phone number."
                        },
                        "other_phone": {
                            "type": "string",
                            "description": "Alternative or unknown type phone number."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_update_contact",
                description="Update details of an existing contact in Apollo by contact ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "Apollo ID of the contact to update."
                        },
                        "first_name": {
                            "type": "string",
                            "description": "Updated first name."
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Updated last name."
                        },
                        "organization_name": {
                            "type": "string",
                            "description": "Updated employer name."
                        },
                        "title": {
                            "type": "string",
                            "description": "Updated job title."
                        },
                        "account_id": {
                            "type": "string",
                            "description": "Updated Apollo account ID."
                        },
                        "email": {
                            "type": "string",
                            "description": "Updated email address."
                        },
                        "website_url": {
                            "type": "string",
                            "description": "Updated corporate website URL (full URL)."
                        },
                        "label_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lists the contact belongs to (replaces existing lists)."
                        },
                        "contact_stage_id": {
                            "type": "string",
                            "description": "Updated contact stage ID."
                        },
                        "present_raw_address": {
                            "type": "string",
                            "description": "Updated personal location (city, state, country)."
                        },
                        "direct_phone": {
                            "type": "string",
                            "description": "Updated primary phone number."
                        },
                        "corporate_phone": {
                            "type": "string",
                            "description": "Updated work/office phone number."
                        },
                        "mobile_phone": {
                            "type": "string",
                            "description": "Updated mobile phone number."
                        },
                        "home_phone": {
                            "type": "string",
                            "description": "Updated home phone number."
                        },
                        "other_phone": {
                            "type": "string",
                            "description": "Updated alternative or unknown phone number."
                        }
                    },
                    "required": ["contact_id"]
                }
            ),
            types.Tool(
                name="apollo_search_contacts",
                description="Search for contacts explicitly added to your team's Apollo database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "q_keywords": {
                            "type": "string",
                            "description": "Keywords to search contact names, titles, companies, or emails."
                        },
                        "contact_stage_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by one or more contact stage IDs."
                        },
                        "sort_by_field": {
                            "type": "string",
                            "enum": [
                                "contact_last_activity_date",
                                "contact_email_last_opened_at",
                                "contact_email_last_clicked_at",
                                "contact_created_at",
                                "contact_updated_at"
                            ],
                            "description": "Field to sort results by."
                        },
                        "sort_ascending": {
                            "type": "boolean",
                            "description": "True for ascending order (requires sort_by_field)."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number of results to retrieve."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_update_contact_stages",
                description="Update the contact stage for multiple contacts in Apollo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Apollo contact IDs to update."
                        },
                        "contact_stage_id": {
                            "type": "string",
                            "description": "Apollo ID of the contact stage to assign."
                        }
                    },
                    "required": ["contact_ids", "contact_stage_id"]
                }
            ),
            types.Tool(
                name="apollo_update_contact_owners",
                description="Assign multiple contacts to a different owner in Apollo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Apollo contact IDs to update."
                        },
                        "owner_id": {
                            "type": "string",
                            "description": "Apollo user ID to assign as the new owner."
                        }
                    },
                    "required": ["contact_ids", "owner_id"]
                }
            ),
            types.Tool(
                name="apollo_list_contact_stages",
                description="Retrieve all available contact stage IDs in your team's Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            #deals.py---------------------------------------------------
            types.Tool(
                name="apollo_create_deal",
                description="Create a new deal for an Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Human-readable name for the deal."
                        },
                        "owner_id": {
                            "type": "string",
                            "description": "ID of the deal owner in your Apollo account."
                        },
                        "account_id": {
                            "type": "string",
                            "description": "ID of the target account (company) for the deal."
                        },
                        "amount": {
                            "type": "string",
                            "description": "Monetary value of the deal (no commas or currency symbols)."
                        },
                        "opportunity_stage_id": {
                            "type": "string",
                            "description": "ID of the deal stage."
                        },
                        "closed_date": {
                            "type": "string",
                            "description": "Estimated close date (YYYY-MM-DD)."
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="apollo_list_all_deals",
                description="Retrieve all deals created for your team's Apollo account with optional sorting and pagination.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sort_by_field": {
                            "type": "string",
                            "enum": ["amount", "is_closed", "is_won"],
                            "description": "Sort deals by amount, is_closed, or is_won."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number to retrieve."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_view_deal",
                description="Retrieve detailed information about a specific deal in your team's Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "opportunity_id": {
                            "type": "string",
                            "description": "Unique ID of the deal to retrieve."
                        }
                    },
                    "required": ["opportunity_id"]
                }
            ),
            types.Tool(
                name="apollo_update_deal",
                description="Update details of an existing deal in your team's Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "opportunity_id": {
                            "type": "string",
                            "description": "Unique ID of the deal to update."
                        },
                        "owner_id": {
                            "type": "string",
                            "description": "New owner ID for the deal."
                        },
                        "name": {
                            "type": "string",
                            "description": "Updated human-readable deal name."
                        },
                        "amount": {
                            "type": "string",
                            "description": "Updated monetary value (no commas or currency symbols)."
                        },
                        "opportunity_stage_id": {
                            "type": "string",
                            "description": "New deal stage ID."
                        },
                        "closed_date": {
                            "type": "string",
                            "description": "Updated estimated close date (YYYY-MM-DD)."
                        },
                        "is_closed": {
                            "type": "boolean",
                            "description": "Mark deal as closed if True."
                        },
                        "is_won": {
                            "type": "boolean",
                            "description": "Mark deal as won if True."
                        },
                        "source": {
                            "type": "string",
                            "description": "Update the deal's source."
                        },
                        "account_id": {
                            "type": "string",
                            "description": "Update associated company ID."
                        }
                    },
                    "required": ["opportunity_id"]
                }
            ),
            types.Tool(
                name="apollo_list_deal_stages",
                description="Retrieve all deal stages available in your team's Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            #enrichment.py-----------------------------------------------
            types.Tool(
                name="apollo_organisation_enrichment",
                description="Enrich data for a single organization by domain.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "Domain of the company to enrich (exclude www., @, etc.). Example: apollo.io or microsoft.com"
                        }
                    },
                    "required": ["domain"]
                }
            ),
            types.Tool(
                name="apollo_bulk_organisation_enrichment",
                description="Enrich data for up to 10 organizations in one call.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of company domains to enrich (exclude www., @, etc.). Example: ['apollo.io', 'microsoft.com']"
                        }
                    },
                    "required": ["domains"]
                }
            ),
            #miscellaneous.py------------------------------------------------
            types.Tool(
                name="apollo_view_api_usage_stats",
                description="Retrieve your team's Apollo API usage statistics and rate limits.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_list_users",
                description="Retrieve the list of all users (teammates) in your Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "Page number of results to retrieve."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_list_email_accounts",
                description="Retrieve information about linked email inboxes used by teammates in your Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_get_all_lists_and_tags",
                description="Retrieve all lists and tags created in your Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_list_all_custom_fields",
                description="Retrieve all custom fields created in your Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            #search.py--------------------------------------------------------
            types.Tool(
                name="apollo_organization_job_postings",
                description="Retrieve current job postings for a specific organization.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "organization_id": {
                            "type": "string",
                            "description": "Unique Apollo ID of the company."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for paginated results."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of job postings per page to improve performance."
                        }
                    },
                    "required": ["organization_id"]
                }
            ),
            types.Tool(
                name="apollo_news_articles_search",
                description="Search news articles related to companies in the Apollo database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "organization_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Apollo IDs of companies to include in the search."
                        },
                        "categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by news categories or sub-categories (e.g., hires, investment, contract)."
                        },
                        "published_at_min": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD) for the date range filter."
                        },
                        "published_at_max": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD) for the date range filter."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for paginated results."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page to improve performance."
                        }
                    },
                    "required": ["organization_ids"]
                }
            ),
            #sequences.py----------------------------------------------
            types.Tool(
                name="apollo_search_sequences",
                description="Search for sequences created in your team's Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "q_name": {
                            "type": "string",
                            "description": "Keywords to filter sequence names (partial matches only)."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number to retrieve for paginated results."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page to improve performance."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_add_contacts_to_sequence",
                description="Add contacts to an existing sequence in your Apollo account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sequence_id": {
                            "type": "string",
                            "description": "Apollo ID of the sequence to add contacts to."
                        },
                        "emailer_campaign_id": {
                            "type": "string",
                            "description": "Same as sequence_id."
                        },
                        "contact_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Apollo contact IDs to add."
                        },
                        "send_email_from_email_account_id": {
                            "type": "string",
                            "description": "Apollo email account ID used to send emails."
                        },
                        "sequence_no_email": {
                            "type": "boolean",
                            "description": "Add contacts without email addresses.",
                            "default": False
                        },
                        "sequence_unverified_email": {
                            "type": "boolean",
                            "description": "Add contacts with unverified emails.",
                            "default": False
                        },
                        "sequence_job_change": {
                            "type": "boolean",
                            "description": "Add contacts who recently changed jobs.",
                            "default": False
                        },
                        "sequence_active_in_other_campaigns": {
                            "type": "boolean",
                            "description": "Add contacts active in other sequences.",
                            "default": False
                        },
                        "sequence_finished_in_other_campaigns": {
                            "type": "boolean",
                            "description": "Add contacts finished in other sequences.",
                            "default": False
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Apollo user ID performing the action (for activity logs)."
                        }
                    },
                    "required": ["sequence_id", "emailer_campaign_id", "contact_ids",
                                 "send_email_from_email_account_id"]
                }
            ),
            types.Tool(
                name="apollo_update_contact_status_in_sequence",
                description="Update contact status in one or more sequences.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "emailer_campaign_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Apollo IDs of sequences to update."
                        },
                        "contact_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Apollo contact IDs whose sequence status will be updated."
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["mark_as_finished", "remove", "stop"],
                            "description": "Action to perform on contacts within sequences."
                        }
                    },
                    "required": ["emailer_campaign_ids", "contact_ids", "mode"]
                }
            ),
            types.Tool(
                name="apollo_search_outreach_emails",
                description="Search for outreach emails sent as part of Apollo sequences.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "emailer_message_stats": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter emails by their status (e.g., delivered, opened)."
                        },
                        "emailer_message_reply_classes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter emails by recipient response sentiment (e.g., willing_to_meet)."
                        },
                        "user_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter emails sent by specific user IDs."
                        },
                        "email_account_id_and_aliases": {
                            "type": "string",
                            "description": "Filter by linked email account and its aliases."
                        },
                        "emailer_campaign_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Include emails from specific sequences only."
                        },
                        "not_emailer_campaign_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Exclude emails from specific sequences."
                        },
                        "emailer_message_date_range_mode": {
                            "type": "string",
                            "description": "Mode for date filtering, either 'due_at' or 'completed_at'."
                        },
                        "emailerMessageDateRange_max": {
                            "type": "string",
                            "description": "Upper bound date (YYYY-MM-DD)."
                        },
                        "emailerMessageDateRange_min": {
                            "type": "string",
                            "description": "Lower bound date (YYYY-MM-DD)."
                        },
                        "not_sent_reason_cds": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter emails by reasons for not being sent."
                        },
                        "q_keywords": {
                            "type": "string",
                            "description": "Keyword search in email content or sender."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page."
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="apollo_check_email_stats",
                description="Retrieve detailed statistics and information for a specific outreach email sent via an Apollo sequence.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email_id": {
                            "type": "string",
                            "description": "The unique ID of the email to retrieve stats for."
                        }
                    },
                    "required": ["email_id"]
                }
            ),
            #tasks.py------------------------------------------------------
            types.Tool(
                name="apollo_create_tasks",
                description="Create tasks for multiple contacts in Apollo to track upcoming actions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the task owner who will take action."
                        },
                        "contact_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Apollo contact IDs to assign tasks."
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Task priority."
                        },
                        "due_at": {
                            "type": "string",
                            "description": "Task due date/time in ISO 8601 format (e.g., '2025-02-15T08:10:30Z')."
                        },
                        "task_type": {
                            "type": "string",
                            "enum": [
                                "call",
                                "outreach_manual_email",
                                "linkedin_step_connect",
                                "linkedin_step_message",
                                "linkedin_step_view_profile",
                                "linkedin_step_interact_post",
                                "action_item"
                            ],
                            "description": "Task type."
                        },
                        "status": {
                            "type": "string",
                            "enum": ["scheduled", "completed", "archived"],
                            "description": "Task status."
                        },
                        "note": {
                            "type": "string",
                            "description": "Additional context or description for the task."
                        }
                    },
                    "required": ["user_id", "contact_ids", "priority", "due_at", "task_type", "status"]
                }
            ),
            types.Tool(
                name="apollo_search_tasks",
                description="Search for tasks created by your team in Apollo with filtering and sorting options.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sort_by_field": {
                            "type": "string",
                            "enum": ["task_due_at", "task_priority"],
                            "description": "Sort tasks by future due date or priority."
                        },
                        "open_factor_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Task types to get counts of tasks by type."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number to retrieve."
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of tasks per page."
                        }
                    }
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
            name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:

        # accounts.py ----------------------------
        if name == "apollo_create_account":
            try:
                result = await apollo_create_account(
                    name=arguments.get("name"),
                    domain=arguments.get("domain"),
                    owner_id=arguments.get("owner_id"),
                    account_stage_id=arguments.get("account_stage_id"),
                    phone=arguments.get("phone"),
                    raw_address=arguments.get("raw_address"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_account":
            account_id = arguments.get("account_id")
            if not account_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: account_id.",
                    )
                ]
            try:
                result = await apollo_update_account(
                    account_id=account_id,
                    name=arguments.get("name"),
                    domain=arguments.get("domain"),
                    owner_id=arguments.get("owner_id"),
                    account_stage_id=arguments.get("account_stage_id"),
                    raw_address=arguments.get("raw_address"),
                    phone=arguments.get("phone"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_search_accounts":
            try:
                result = await apollo_search_accounts(
                    q_organization_name=arguments.get("q_organization_name"),
                    account_stage_ids=arguments.get("account_stage_ids"),
                    sort_by_field=arguments.get("sort_by_field"),
                    sort_ascending=arguments.get("sort_ascending"),
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_view_account":
            account_id = arguments.get("account_id")
            if not account_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: account_id.",
                    )
                ]
            try:
                result = await apollo_view_account(account_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_account_stage_bulk":
            account_ids = arguments.get("account_ids")
            account_stage_id = arguments.get("account_stage_id")
            if not account_ids or not account_stage_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameters: account_ids, account_stage_id.",
                    )
                ]
            try:
                result = await apollo_update_account_stage_bulk(account_ids, account_stage_id)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_account_owner_bulk":
            account_ids = arguments.get("account_ids")
            owner_id = arguments.get("owner_id")
            if not account_ids or not owner_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameters: account_ids, owner_id.",
                    )
                ]
            try:
                result = await apollo_update_account_owner_bulk(account_ids, owner_id)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_list_account_stages":
            try:
                result = await apollo_list_account_stages()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        #calls.py--------------------------------------
        elif name == "apollo_create_call_record":
            logged = arguments.get("logged")
            user_ids = arguments.get("user_ids")
            contact_id = arguments.get("contact_id")
            if logged is None or not user_ids or not contact_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameters: logged, user_ids, contact_id.",
                    )
                ]
            try:
                result = await apollo_create_call_record(
                    logged=logged,
                    user_ids=user_ids,
                    contact_id=contact_id,
                    account_id=arguments.get("account_id"),
                    to_number=arguments.get("to_number"),
                    from_number=arguments.get("from_number"),
                    status=arguments.get("status"),
                    start_time=arguments.get("start_time"),
                    end_time=arguments.get("end_time"),
                    duration=arguments.get("duration"),
                    phone_call_purpose_id=arguments.get("phone_call_purpose_id"),
                    phone_call_outcome_id=arguments.get("phone_call_outcome_id"),
                    note=arguments.get("note"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_search_calls":
            try:
                result = await apollo_search_calls(
                    date_range_max=arguments.get("date_range_max"),
                    date_range_min=arguments.get("date_range_min"),
                    duration_max=arguments.get("duration_max"),
                    duration_min=arguments.get("duration_min"),
                    inbound=arguments.get("inbound"),
                    user_ids=arguments.get("user_ids"),
                    contact_label_ids=arguments.get("contact_label_ids"),
                    phone_call_purpose_ids=arguments.get("phone_call_purpose_ids"),
                    phone_call_outcome_ids=arguments.get("phone_call_outcome_ids"),
                    q_keywords=arguments.get("q_keywords"),
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_call":
            call_id = arguments.get("call_id")
            if not call_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: call_id.",
                    )
                ]
            try:
                result = await apollo_update_call(
                    call_id=call_id,
                    logged=arguments.get("logged"),
                    user_ids=arguments.get("user_ids"),
                    contact_id=arguments.get("contact_id"),
                    account_id=arguments.get("account_id"),
                    to_number=arguments.get("to_number"),
                    from_number=arguments.get("from_number"),
                    status=arguments.get("status"),
                    start_time=arguments.get("start_time"),
                    end_time=arguments.get("end_time"),
                    duration=arguments.get("duration"),
                    phone_call_purpose_id=arguments.get("phone_call_purpose_id"),
                    phone_call_outcome_id=arguments.get("phone_call_outcome_id"),
                    note=arguments.get("note"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # contacts.py---------------------------------------------
        elif name == "apollo_create_contact":
            try:
                result = await apollo_create_contact(
                    first_name=arguments.get("first_name"),
                    last_name=arguments.get("last_name"),
                    organization_name=arguments.get("organization_name"),
                    title=arguments.get("title"),
                    account_id=arguments.get("account_id"),
                    email=arguments.get("email"),
                    website_url=arguments.get("website_url"),
                    label_names=arguments.get("label_names"),
                    contact_stage_id=arguments.get("contact_stage_id"),
                    present_raw_address=arguments.get("present_raw_address"),
                    direct_phone=arguments.get("direct_phone"),
                    corporate_phone=arguments.get("corporate_phone"),
                    mobile_phone=arguments.get("mobile_phone"),
                    home_phone=arguments.get("home_phone"),
                    other_phone=arguments.get("other_phone"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_contact":
            contact_id = arguments.get("contact_id")
            if not contact_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: contact_id.",
                    )
                ]
            try:
                result = await apollo_update_contact(
                    contact_id=contact_id,
                    first_name=arguments.get("first_name"),
                    last_name=arguments.get("last_name"),
                    organization_name=arguments.get("organization_name"),
                    title=arguments.get("title"),
                    account_id=arguments.get("account_id"),
                    email=arguments.get("email"),
                    website_url=arguments.get("website_url"),
                    label_names=arguments.get("label_names"),
                    contact_stage_id=arguments.get("contact_stage_id"),
                    present_raw_address=arguments.get("present_raw_address"),
                    direct_phone=arguments.get("direct_phone"),
                    corporate_phone=arguments.get("corporate_phone"),
                    mobile_phone=arguments.get("mobile_phone"),
                    home_phone=arguments.get("home_phone"),
                    other_phone=arguments.get("other_phone"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_search_contacts":
            try:
                result = await apollo_search_contacts(
                    q_keywords=arguments.get("q_keywords"),
                    contact_stage_ids=arguments.get("contact_stage_ids"),
                    sort_by_field=arguments.get("sort_by_field"),
                    sort_ascending=arguments.get("sort_ascending"),
                    per_page=arguments.get("per_page"),
                    page=arguments.get("page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_contact_stages":
            contact_ids = arguments.get("contact_ids")
            contact_stage_id = arguments.get("contact_stage_id")
            if not contact_ids or not contact_stage_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameters: contact_ids, contact_stage_id.",
                    )
                ]
            try:
                result = await apollo_update_contact_stages(contact_ids, contact_stage_id)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_contact_owners":
            contact_ids = arguments.get("contact_ids")
            owner_id = arguments.get("owner_id")
            if not contact_ids or not owner_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameters: contact_ids, owner_id.",
                    )
                ]
            try:
                result = await apollo_update_contact_owners(contact_ids, owner_id)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_list_contact_stages":
            try:
                result = await apollo_list_contact_stages()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        #deals.py-----------------------------------------------------------------
        elif name == "apollo_create_deal":
            name_arg = arguments.get("name")
            if not name_arg:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: name.",
                    )
                ]
            try:
                result = await apollo_create_deal(
                    name=name_arg,
                    owner_id=arguments.get("owner_id"),
                    account_id=arguments.get("account_id"),
                    amount=arguments.get("amount"),
                    opportunity_stage_id=arguments.get("opportunity_stage_id"),
                    closed_date=arguments.get("closed_date"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_list_all_deals":
            try:
                result = await apollo_list_all_deals(
                    sort_by_field=arguments.get("sort_by_field"),
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_view_deal":
            opportunity_id = arguments.get("opportunity_id")
            if not opportunity_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: opportunity_id.",
                    )
                ]
            try:
                result = await apollo_view_deal(opportunity_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_deal":
            opportunity_id = arguments.get("opportunity_id")
            if not opportunity_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: opportunity_id.",
                    )
                ]
            try:
                result = await apollo_update_deal(
                    opportunity_id=opportunity_id,
                    owner_id=arguments.get("owner_id"),
                    name=arguments.get("name"),
                    amount=arguments.get("amount"),
                    opportunity_stage_id=arguments.get("opportunity_stage_id"),
                    closed_date=arguments.get("closed_date"),
                    is_closed=arguments.get("is_closed"),
                    is_won=arguments.get("is_won"),
                    source=arguments.get("source"),
                    account_id=arguments.get("account_id"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_list_deal_stages":
            try:
                result = await apollo_list_deal_stages()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        #enrichment.py----------------------------------------------------
        elif name == "apollo_organisation_enrichment":
            domain = arguments.get("domain")
            if not domain:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: domain.",
                    )
                ]
            try:
                result = await apollo_organisation_enrichment(domain)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_bulk_organisation_enrichment":
            domains = arguments.get("domains")
            if not domains or not isinstance(domains, list) or len(domains) == 0:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing or invalid required parameter: domains.",
                    )
                ]
            try:
                result = await apollo_bulk_organisation_enrichment(domains)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        #miscellaneous.py---------------------------------------------------
        elif name == "apollo_view_api_usage_stats":
            try:
                result = await apollo_view_api_usage_stats()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_list_users":
            try:
                result = await apollo_list_users(
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_list_email_accounts":
            try:
                result = await apollo_list_email_accounts()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_get_all_lists_and_tags":
            try:
                result = await apollo_get_all_lists_and_tags()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_list_all_custom_fields":
            try:
                result = await apollo_list_all_custom_fields()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        #search.py-----------------------------------------------------
        elif name == "apollo_organization_job_postings":
            organization_id = arguments.get("organization_id")
            if not organization_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: organization_id.",
                    )
                ]
            try:
                result = await apollo_organization_job_postings(
                    organization_id=organization_id,
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_news_articles_search":
            organization_ids = arguments.get("organization_ids")
            if not organization_ids or not isinstance(organization_ids, list) or len(organization_ids) == 0:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing or invalid required parameter: organization_ids.",
                    )
                ]
            try:
                result = await apollo_news_articles_search(
                    organization_ids=organization_ids,
                    categories=arguments.get("categories"),
                    published_at_min=arguments.get("published_at_min"),
                    published_at_max=arguments.get("published_at_max"),
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        #sequence.py--------------------------------------------
        elif name == "apollo_search_sequences":
            try:
                result = await apollo_search_sequences(
                    q_name=arguments.get("q_name"),
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_add_contacts_to_sequence":
            required_params = ["sequence_id", "emailer_campaign_id", "contact_ids", "send_email_from_email_account_id"]
            if not all(param in arguments for param in required_params):
                return [
                    types.TextContent(
                        type="text",
                        text=f"Missing required parameters. Required: {', '.join(required_params)}.",
                    )
                ]
            try:
                result = await apollo_add_contacts_to_sequence(
                    sequence_id=arguments["sequence_id"],
                    emailer_campaign_id=arguments["emailer_campaign_id"],
                    contact_ids=arguments["contact_ids"],
                    send_email_from_email_account_id=arguments["send_email_from_email_account_id"],
                    sequence_no_email=arguments.get("sequence_no_email", False),
                    sequence_unverified_email=arguments.get("sequence_unverified_email", False),
                    sequence_job_change=arguments.get("sequence_job_change", False),
                    sequence_active_in_other_campaigns=arguments.get("sequence_active_in_other_campaigns", False),
                    sequence_finished_in_other_campaigns=arguments.get("sequence_finished_in_other_campaigns", False),
                    user_id=arguments.get("user_id"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_update_contact_status_in_sequence":
            required_params = ["emailer_campaign_ids", "contact_ids", "mode"]
            if not all(param in arguments for param in required_params):
                return [
                    types.TextContent(
                        type="text",
                        text=f"Missing required parameters. Required: {', '.join(required_params)}.",
                    )
                ]
            try:
                result = await apollo_update_contact_status_in_sequence(
                    emailer_campaign_ids=arguments["emailer_campaign_ids"],
                    contact_ids=arguments["contact_ids"],
                    mode=arguments["mode"],
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_search_outreach_emails":
            try:
                result = await apollo_search_outreach_emails(
                    emailer_message_stats=arguments.get("emailer_message_stats"),
                    emailer_message_reply_classes=arguments.get("emailer_message_reply_classes"),
                    user_ids=arguments.get("user_ids"),
                    email_account_id_and_aliases=arguments.get("email_account_id_and_aliases"),
                    emailer_campaign_ids=arguments.get("emailer_campaign_ids"),
                    not_emailer_campaign_ids=arguments.get("not_emailer_campaign_ids"),
                    emailer_message_date_range_mode=arguments.get("emailer_message_date_range_mode"),
                    emailerMessageDateRange_max=arguments.get("emailerMessageDateRange_max"),
                    emailerMessageDateRange_min=arguments.get("emailerMessageDateRange_min"),
                    not_sent_reason_cds=arguments.get("not_sent_reason_cds"),
                    q_keywords=arguments.get("q_keywords"),
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_check_email_stats":
            email_id = arguments.get("email_id")
            if not email_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Missing required parameter: email_id.",
                    )
                ]
            try:
                result = await apollo_check_email_stats(email_id=email_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        #tasks.py-----------------------------------------------
        elif name == "apollo_create_tasks":
            required_params = ["user_id", "contact_ids", "priority", "due_at", "task_type", "status"]
            if not all(param in arguments for param in required_params):
                return [
                    types.TextContent(
                        type="text",
                        text=f"Missing required parameters. Required: {', '.join(required_params)}.",
                    )
                ]
            try:
                result = await apollo_create_tasks(
                    user_id=arguments["user_id"],
                    contact_ids=arguments["contact_ids"],
                    priority=arguments["priority"],
                    due_at=arguments["due_at"],
                    task_type=arguments["task_type"],
                    status=arguments["status"],
                    note=arguments.get("note"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "apollo_search_tasks":
            try:
                result = await apollo_search_tasks(
                    sort_by_field=arguments.get("sort_by_field"),
                    open_factor_names=arguments.get("open_factor_names"),
                    page=arguments.get("page"),
                    per_page=arguments.get("per_page"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

    #-----------------------------------------------------------------------------------------------------------

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