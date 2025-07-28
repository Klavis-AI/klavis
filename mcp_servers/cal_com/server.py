import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List
import asyncio

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
    # base.py
    auth_token_context,

    # schedule.py
    cal_get_all_schedules,
    cal_create_a_schedule,
    cal_update_a_schedule,
    cal_get_default_schedule,
    cal_get_schedule,
    cal_delete_a_schedule,

    # stripe.py (Not able to test)
    # cal_get_stripe_connect_url,
    # cal_save_stripe_credentials,
    # cal_check_stripe_connection,

    # verified_resources.py
    cal_request_email_verification_code,
    cal_verify_email_code,
    cal_get_verified_emails,
    cal_get_verified_email_by_id,

    # Phone verification functions not working (tested with Indian numbers)
    # 'cal_request_phone_verification_code',
    # 'cal_verify_phone_code',

    cal_get_verified_phones,
    cal_get_verified_phone_by_id,

    # webhooks.py
    cal_get_all_webhooks,
    cal_create_webhook,
    cal_get_webhook,
    cal_update_webhook,
    cal_delete_webhook
)



# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

CAL_COM_MCP_SERVER_PORT = int(os.getenv("CAL_COM_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=CAL_COM_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("cal-com-mcp-server")
#-------------------------------------------------------------------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Get all schedules
            types.Tool(
                name="cal_get_all_schedules",
                description="Retrieve all schedules from Cal.com API.",
                inputSchema={
                    "type": "object",
                    "properties": {},  # No parameters required
                    "required": []
                }
            ),

            # Create a schedule
            types.Tool(
                name="cal_create_a_schedule",
                description="Create a new schedule in Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the new schedule"
                        },
                        "timeZone": {
                            "type": "string",
                            "description": "Time zone ID (e.g., 'America/New_York')"
                        },
                        "isDefault": {
                            "type": "boolean",
                            "description": "Whether this should be the default schedule"
                        },
                        "availability": {
                            "type": "array",
                            "description": "List of availability blocks",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "days": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Capitalized day names (e.g., ['Monday','Tuesday'])"
                                    },
                                    "startTime": {
                                        "type": "string",
                                        "description": "Start time in HH:mm format"
                                    },
                                    "endTime": {
                                        "type": "string",
                                        "description": "End time in HH:mm format"
                                    }
                                }
                            }
                        },
                        "overrides": {
                            "type": "array",
                            "description": "Date-specific overrides",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": {
                                        "type": "string",
                                        "description": "Date in YYYY-MM-DD format"
                                    },
                                    "startTime": {
                                        "type": "string",
                                        "description": "Start time in HH:mm format"
                                    },
                                    "endTime": {
                                        "type": "string",
                                        "description": "End time in HH:mm format"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["name", "timeZone", "isDefault"]
                }
            ),

            types.Tool(
                name="cal_update_a_schedule",
                description="Update an existing schedule in Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schedule_id": {
                            "type": "integer",
                            "description": "ID of the schedule to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "Updated schedule name"
                        },
                        "timeZone": {
                            "type": "string",
                            "description": "Updated time zone ID (e.g., 'America/New_York')"
                        },
                        "isDefault": {
                            "type": "boolean",
                            "description": "Whether to make this the default schedule"
                        },
                        "availability": {
                            "type": "array",
                            "description": "Updated availability blocks",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "days": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Capitalized day names (e.g., ['Monday','Tuesday'])"
                                    },
                                    "startTime": {
                                        "type": "string",
                                        "description": "Start time in HH:mm format (e.g., '09:00')"
                                    },
                                    "endTime": {
                                        "type": "string",
                                        "description": "End time in HH:mm format (e.g., '17:00')"
                                    }
                                }
                            }
                        },
                        "overrides": {
                            "type": "array",
                            "description": "Updated date overrides",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": {
                                        "type": "string",
                                        "description": "Date in YYYY-MM-DD format (e.g., '2023-12-31')"
                                    },
                                    "startTime": {
                                        "type": "string",
                                        "description": "Start time in HH:mm format (e.g., '10:00')"
                                    },
                                    "endTime": {
                                        "type": "string",
                                        "description": "End time in HH:mm format (e.g., '15:00')"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["schedule_id"]
                }
            ),

            # Get default schedule
            types.Tool(
                name="cal_get_default_schedule",
                description="Get the default schedule from Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {},  # No parameters
                    "required": []
                }
            ),

            # Get specific schedule
            types.Tool(
                name="cal_get_schedule",
                description="Get a specific schedule by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schedule_id": {
                            "type": "integer",
                            "description": "ID of the schedule to retrieve"
                        }
                    },
                    "required": ["schedule_id"]
                }
            ),

            # Delete a schedule
            types.Tool(
                name="cal_delete_a_schedule",
                description="Delete a schedule by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schedule_id": {
                            "type": "integer",
                            "description": "ID of the schedule to delete"
                        }
                    },
                    "required": ["schedule_id"]
                }
            ),

            #Stripe.py----------------------------------------------------------------


            #types.Tool(
            #    name="cal_get_stripe_connect_url",
            #    description="Retrieve Stripe Connect URL from Cal.com API for payment setup",
            #    inputSchema={
            #        "type": "object",
            #        "properties": {},  # No parameters required
            #        "required": []
            #    }
            #),
            #types.Tool(
            #    name="cal_save_stripe_credentials",
            #    description="Save Stripe credentials in Cal.com after OAuth authorization",
            #    inputSchema={
            #        "type": "object",
            #        "properties": {
            #            "state": {
            #                "type": "string",
            #                "description": "OAuth state parameter for security verification"
            #            },
            #            "code": {
            #                "type": "string",
            #                "description": "OAuth authorization code from Stripe"
            #            }
            #        },
            #        "required": ["state", "code"]  # Both parameters are required
            #    }
            #),
            #types.Tool(
            #    name="cal_check_stripe_connection",
            #    description="Check Stripe connection status in Cal.com",
            #    inputSchema={
            #        "type": "object",
            #        "properties": {},  # No parameters required
            #        "required": []
            #    }
            #),



            #verified_resources.py---------------------------------------------------
            # Email Verification Tools
            types.Tool(
                name="cal_request_email_verification_code",
                description="Request an email verification code from Cal.com API.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "Email address to verify",
                            "format": "email"
                        }
                    },
                    "required": ["email"]
                }
            ),

            types.Tool(
                name="cal_verify_email_code",
                description="Verify an email address with the received verification code.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "Email address to verify",
                            "format": "email"
                        },
                        "code": {
                            "type": "string",
                            "description": "Verification code received via email"
                        }
                    },
                    "required": ["email", "code"]
                }
            ),

            types.Tool(
                name="cal_get_verified_emails",
                description="Retrieve all verified emails from Cal.com API.",
                inputSchema={
                    "type": "object",
                    "properties": {},  # No parameters required
                    "required": []
                }
            ),

            types.Tool(
                name="cal_get_verified_email_by_id",
                description="Get a specific verified email by its ID from Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email_id": {
                            "type": "integer",
                            "description": "ID of the verified email to retrieve"
                        }
                    },
                    "required": ["email_id"]
                }
            ),

            # Phone Verification Tools (working functions only)
            types.Tool(
                name="cal_get_verified_phones",
                description="Retrieve verified phone numbers with pagination support.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "take": {
                            "type": "integer",
                            "description": "Number of records to return (default: 250, max: 250)",
                            "default": 250,
                            "minimum": 1,
                            "maximum": 250
                        },
                        "skip": {
                            "type": "integer",
                            "description": "Number of records to skip for pagination",
                            "minimum": 0
                        }
                    },
                    "required": []
                }
            ),

            types.Tool(
                name="cal_get_verified_phone_by_id",
                description="Get a specific verified phone number by its ID from Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phone_id": {
                            "type": "integer",
                            "description": "ID of the verified phone to retrieve"
                        }
                    },
                    "required": ["phone_id"]
                }
            ),

            # Webhook Tools-------------------------------------------------------------
            types.Tool(
                name="cal_get_all_webhooks",
                description="Retrieve all webhooks with pagination support from Cal.com API.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "take": {
                            "type": "integer",
                            "description": "Number of records to return (default: 250)",
                            "minimum": 1,
                            "maximum": 250,
                            "default": 250
                        },
                        "skip": {
                            "type": "integer",
                            "description": "Number of records to skip for pagination",
                            "minimum": 0
                        }
                    },
                    "required": []
                }
            ),

            types.Tool(
                name="cal_create_webhook",
                description="Create a new webhook in Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active": {
                            "type": "boolean",
                            "description": "Whether the webhook is active"
                        },
                        "subscriberUrl": {
                            "type": "string",
                            "description": "URL to receive webhook payloads",
                            "format": "uri"
                        },
                        "triggers": {
                            "type": "array",
                            "description": "List of trigger events",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "BOOKING_CREATED",
                                    "BOOKING_PAYMENT_INITIATED",
                                    "BOOKING_PAID",
                                    "BOOKING_RESCHEDULED",
                                    "BOOKING_REQUESTED",
                                    "BOOKING_CANCELLED",
                                    "BOOKING_REJECTED",
                                    "BOOKING_NO_SHOW_UPDATED",
                                    "FORM_SUBMITTED",
                                    "MEETING_ENDED",
                                    "MEETING_STARTED",
                                    "RECORDING_READY",
                                    "INSTANT_MEETING",
                                    "RECORDING_TRANSCRIPTION_GENERATED",
                                    "OOO_CREATED",
                                    "AFTER_HOSTS_CAL_VIDEO_NO_SHOW",
                                    "AFTER_GUESTS_CAL_VIDEO_NO_SHOW",
                                    "FORM_SUBMITTED_NO_EVENT"
                                ]
                            }
                        },
                        "payloadTemplate": {
                            "type": "string",
                            "description": "Custom payload template (JSON string with Liquid variables)"
                        },
                        "secret": {
                            "type": "string",
                            "description": "Secret for verifying webhooks"
                        }
                    },
                    "required": ["active", "subscriberUrl", "triggers"]
                }
            ),

            types.Tool(
                name="cal_get_webhook",
                description="Get a specific webhook by its ID from Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "webhook_id": {
                            "type": "string",
                            "description": "ID of the webhook to retrieve"
                        }
                    },
                    "required": ["webhook_id"]
                }
            ),

            types.Tool(
                name="cal_update_webhook",
                description="Update an existing webhook in Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "webhook_id": {
                            "type": "string",
                            "description": "ID of the webhook to update"
                        },
                        "active": {
                            "type": "boolean",
                            "description": "Whether the webhook is active"
                        },
                        "subscriberUrl": {
                            "type": "string",
                            "description": "New URL to receive webhook payloads",
                            "format": "uri"
                        },
                        "triggers": {
                            "type": "array",
                            "description": "Updated list of trigger events",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "BOOKING_CREATED",
                                    "BOOKING_PAYMENT_INITIATED",
                                    "BOOKING_PAID",
                                    "BOOKING_RESCHEDULED",
                                    "BOOKING_REQUESTED",
                                    "BOOKING_CANCELLED",
                                    "BOOKING_REJECTED",
                                    "BOOKING_NO_SHOW_UPDATED",
                                    "FORM_SUBMITTED",
                                    "MEETING_ENDED",
                                    "MEETING_STARTED",
                                    "RECORDING_READY",
                                    "INSTANT_MEETING",
                                    "RECORDING_TRANSCRIPTION_GENERATED",
                                    "OOO_CREATED",
                                    "AFTER_HOSTS_CAL_VIDEO_NO_SHOW",
                                    "AFTER_GUESTS_CAL_VIDEO_NO_SHOW",
                                    "FORM_SUBMITTED_NO_EVENT"
                                ]
                            }
                        },
                        "payloadTemplate": {
                            "type": "string",
                            "description": "Updated payload template (JSON string with Liquid variables)"
                        },
                        "secret": {
                            "type": "string",
                            "description": "New secret for verifying webhooks"
                        }
                    },
                    "required": ["webhook_id"]
                }
            ),

            types.Tool(
                name="cal_delete_webhook",
                description="Delete a webhook by its ID from Cal.com.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "webhook_id": {
                            "type": "string",
                            "description": "ID of the webhook to delete"
                        }
                    },
                    "required": ["webhook_id"]
                }
            )


        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:

        #Schedule.py------------------------------------------------------------------
        if name == "cal_get_all_schedules":
            try:
                result = cal_get_all_schedules()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting all schedules: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_create_a_schedule":
            try:
                result = cal_create_a_schedule(
                    name=arguments["name"],
                    timeZone=arguments["timeZone"],
                    isDefault=arguments["isDefault"],
                    availability=arguments.get("availability"),
                    overrides=arguments.get("overrides")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_update_a_schedule":
            try:
                result = cal_update_a_schedule(
                    schedule_id=arguments["schedule_id"],
                    name=arguments.get("name"),
                    timeZone=arguments.get("timeZone"),
                    isDefault=arguments.get("isDefault"),
                    availability=arguments.get("availability"),
                    overrides=arguments.get("overrides")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error updating schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_default_schedule":
            try:
                result = cal_get_default_schedule()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting default schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_schedule":
            try:
                result = cal_get_schedule(
                    schedule_id=arguments["schedule_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_delete_a_schedule":
            try:
                result = cal_delete_a_schedule(
                    schedule_id=arguments["schedule_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting schedule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        #verified_resources.py-----------------------------------------------------------
        elif name == "cal_request_email_verification_code":
            try:
                result = cal_request_email_verification_code(
                    email=arguments["email"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error requesting email verification code: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_verify_email_code":
            try:
                result = cal_verify_email_code(
                    email=arguments["email"],
                    code=arguments["code"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error verifying email code: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_verified_emails":
            try:
                result = cal_get_verified_emails()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting verified emails: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_verified_email_by_id":
            try:
                result = cal_get_verified_email_by_id(
                    email_id=arguments["email_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting verified email by ID: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_verified_phones":
            try:
                result = cal_get_verified_phones(
                    take=arguments.get("take"),
                    skip=arguments.get("skip")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting verified phones: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_verified_phone_by_id":
            try:
                result = cal_get_verified_phone_by_id(
                    phone_id=arguments["phone_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting verified phone by ID: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        #webhooks.py-----------------------------------------------------------------------
        elif name == "cal_get_all_webhooks":
            try:
                result = cal_get_all_webhooks(
                    take=arguments.get("take"),
                    skip=arguments.get("skip")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting all webhooks: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_create_webhook":
            try:
                result = cal_create_webhook(
                    active=arguments["active"],
                    subscriberUrl=arguments["subscriberUrl"],
                    triggers=arguments["triggers"],
                    payloadTemplate=arguments.get("payloadTemplate"),
                    secret=arguments.get("secret")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating webhook: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_get_webhook":
            try:
                result = cal_get_webhook(
                    webhook_id=arguments["webhook_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting webhook: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_update_webhook":
            try:
                result = cal_update_webhook(
                    webhook_id=arguments["webhook_id"],
                    active=arguments.get("active"),
                    subscriberUrl=arguments.get("subscriberUrl"),
                    triggers=arguments.get("triggers"),
                    payloadTemplate=arguments.get("payloadTemplate"),
                    secret=arguments.get("secret")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error updating webhook: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_delete_webhook":
            try:
                result = cal_delete_webhook(
                    webhook_id=arguments["webhook_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting webhook: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]


        #Stripe.py-------------------------------------------------------------------------
        '''
        elif name == "cal_get_stripe_connect_url":
            try:
                result = cal_get_stripe_connect_url()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting Stripe URL: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "cal_save_stripe_credentials":
            try:
                result = cal_save_stripe_credentials(
                    state=arguments["state"],
                    code=arguments["code"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error saving credentials: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "cal_check_stripe_connection":
            try:
                result = cal_check_stripe_connection()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error checking connection: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        '''
    #-------------------------------------------------------------------------

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