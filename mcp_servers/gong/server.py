import contextlib
import base64
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

import click
import mcp.types as types
from dotenv import load_dotenv
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    access_key_context,
    access_key_secret_context,
    extract_credentials,
    get_transcripts_by_user,
    get_call_transcripts,
    get_extensive_data,
    list_calls,
    add_new_call,
    get_call_by_id,
)

logger = logging.getLogger(__name__)

load_dotenv()

GONG_MCP_SERVER_PORT = int(os.getenv("GONG_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=GONG_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level")
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(port: int, log_level: str, json_response: bool) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("gong-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="gong_get_transcripts_by_user",
                description=(
                    "Get call transcripts associated with a user by email address "
                    "including all participants on the call and their companies."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["user_email"],
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "description": "Email address of the user.",
                        },
                        "from_date": {
                            "type": "string",
                            "description": "ISO start datetime to filter calls (optional).",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "ISO end datetime to filter calls (optional).",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of calls to return (default 10).",
                            "default": 10,
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_TRANSCRIPT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_get_extensive_data",
                description="Lists detailed call data by various filters: call IDs, date range, or user IDs. At least one filter parameter must be provided. Supports custom exposedFields for granular control over returned data.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "call_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of Gong call IDs to fetch (max 100).",
                        },
                        "from_date": {
                            "type": "string",
                            "description": "ISO-8601 formatted datetime to filter calls from (e.g., '2018-02-18T02:30:00-07:00' or '2018-02-18T08:00:00Z'). Required if filtering by date range.",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "ISO-8601 formatted datetime to filter calls until. Required if filtering by date range.",
                        },
                        "user_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of user IDs to filter calls hosted by these users.",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "Workspace identifier to filter calls.",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor returned by previous request (optional).",
                        },
                        "context": {
                            "type": "string",
                            "description": "Context level for the data: 'None', 'Extended', etc. (default 'Extended').",
                            "default": "Extended",
                        },
                        "context_timing": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Context timing values (e.g., ['Now']).",
                        },
                        "exposed_fields": {
                            "type": "object",
                            "description": "Custom exposedFields object to specify exactly which data to return. Can include: parties, content (structure, topics, trackers, brief, outline, highlights, transcript, callOutcome, keyPoints), interaction (speakers, video, personInteractionStats, questions), collaboration (publicComments), media. If not provided, defaults to parties and basic content fields.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_CALL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_get_call_transcripts",
                description="Retrieve transcripts for calls that took place during a specified date period. If call IDs are specified, only transcripts for calls with those IDs that took place during the time period are returned (Gong /v2/calls/transcript).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "call_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of Gong call IDs (max 100). If not provided, returns all calls in the specified date range.",
                        },
                        "from_date": {
                            "type": "string",
                            "description": "ISO-8601 formatted datetime (e.g., '2018-02-17T02:30:00-08:00') from which to retrieve transcripts. If omitted, defaults to 30 days in the past.",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "ISO-8601 formatted datetime until which to retrieve transcripts. If omitted, defaults to now.",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "Optional Gong workspace ID to filter by.",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor returned by previous API call to retrieve the next page of records.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_TRANSCRIPT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_list_calls",
                description="List calls that took place during a specified date range.",
                inputSchema={
                    "type": "object",
                    "required": ["from_date", "to_date"],
                    "properties": {
                        "from_date": {
                            "type": "string", 
                            "description": "ISO-8601 formatted datetime (e.g., '2018-02-18T02:30:00-07:00' or '2018-02-18T08:00:00Z') from which to list calls. Returns calls that started on or after the specified date and time."
                        },
                        "to_date": {
                            "type": "string", 
                            "description": "ISO-8601 formatted datetime until which to list calls. Returns calls that started up to but excluding specified date and time."
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor returned by previous API call to retrieve the next page of records."
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "Optional workspace identifier to filter calls belonging to a specific workspace."
                        },
                        "limit": {
                            "type": "integer", 
                            "description": "Maximum calls to return (default 50).", 
                            "default": 50
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_CALL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_get_call_by_id",
                description="Retrieve data for a specific call by its Gong ID.",
                inputSchema={
                    "type": "object",
                    "required": ["call_id"],
                    "properties": {
                        "call_id": {
                            "type": "string",
                            "description": "Gong's unique numeric identifier for the call (up to 20 digits)."
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_CALL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_add_new_call",
                description="Add a new call record to Gong. Either provide a downloadMediaUrl or use the returned callId to upload media in a follow-up request.",
                inputSchema={
                    "type": "object",
                    "required": ["clientUniqueId", "actualStart", "parties", "direction", "primaryUser"],
                    "properties": {
                        "clientUniqueId": {
                            "type": "string",
                            "description": "A call's unique identifier in the PBX or the recording system (0 to 2048 chars). Gong uses this to prevent duplicate uploads.",
                        },
                        "title": {
                            "type": "string",
                            "description": "The title of the call. Available in Gong for indexing and search.",
                        },
                        "purpose": {
                            "type": "string",
                            "description": "The purpose of the call (0 to 255 chars, optional).",
                        },
                        "scheduledStart": {
                            "type": "string",
                            "description": "ISO-8601 formatted datetime when the call was scheduled to begin (e.g., '2018-02-18T02:30:00-07:00' or '2018-02-18T08:00:00Z').",
                        },
                        "scheduledEnd": {
                            "type": "string",
                            "description": "ISO-8601 formatted datetime when the call was scheduled to end.",
                        },
                        "actualStart": {
                            "type": "string",
                            "description": "ISO-8601 formatted datetime when the call actually started (required).",
                        },
                        "duration": {
                            "type": "number",
                            "description": "The actual call duration in seconds.",
                        },
                        "parties": {
                            "type": "array",
                            "description": "List of call participants. Must include the primaryUser.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "emailAddress": {"type": "string"},
                                    "name": {"type": "string"},
                                    "title": {"type": "string"},
                                    "userId": {"type": "string"},
                                    "speakerId": {"type": "string"},
                                    "context": {"type": "array", "items": {"type": "object"}},
                                    "affiliation": {"type": "string", "enum": ["Internal", "External", "Unknown"]},
                                }
                            }
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["Inbound", "Outbound", "Conference", "Unknown"],
                            "description": "Whether the call is inbound, outbound, conference, or unknown (required).",
                        },
                        "disposition": {
                            "type": "string",
                            "description": "The disposition of the call (0 to 255 chars).",
                        },
                        "context": {
                            "type": "array",
                            "description": "List of references to external systems (CRM, Telephony, Case Management, etc.).",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "system": {"type": "string"},
                                    "objects": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "objectType": {"type": "string"},
                                                "objectId": {"type": "string"},
                                                "fields": {"type": "array", "items": {"type": "object"}}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "customData": {
                            "type": "string",
                            "description": "Optional metadata associated with the call for troubleshooting.",
                        },
                        "speakersTimeline": {
                            "type": "object",
                            "description": "Audio recording speech segments (who spoke when). Mutually exclusive with mediaChannelId.",
                            "properties": {
                                "segments": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "speakerId": {"type": "string"},
                                            "start": {"type": "number"},
                                            "end": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        },
                        "meetingUrl": {
                            "type": "string",
                            "description": "The URL of the conference call by which users join the meeting.",
                        },
                        "callProviderCode": {
                            "type": "string",
                            "description": "Code identifying the conferencing/telephony provider (e.g., zoom, clearslide, gotomeeting, ringcentral). Contact Gong support for the proper value.",
                        },
                        "downloadMediaUrl": {
                            "type": "string",
                            "description": "URL from which Gong can download the media file (max 1.5GB). Content-type must be audio/video or application/octet-stream. If provided, skip the 'Add call media' step.",
                        },
                        "workspaceId": {
                            "type": "string",
                            "description": "Optional workspace identifier. If specified, the call will be placed in this workspace.",
                        },
                        "languageCode": {
                            "type": "string",
                            "description": "Language code for transcription (e.g., en-US, es-ES, fr-FR). Optional - Gong auto-detects if not specified.",
                        },
                        "flowContext": {
                            "type": "object",
                            "description": "The task ID the call should be associated with.",
                            "properties": {
                                "taskId": {"type": "string"}
                        }
                        },
                        "primaryUser": {
                            "type": "string",
                            "description": "The Gong internal user ID of the team member who hosted the call (required).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_CALL"}),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "gong_get_transcripts_by_user":
            user_email = arguments.get("user_email")
            if not user_email:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'user_email' argument is required.",
                    )
                ]

            limit = arguments.get("limit", 10)
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            try:
                result = await get_transcripts_by_user(
                    user_email=user_email,
                    from_date=from_date,
                    to_date=to_date,
                    limit=limit,
                )
                return [
                    types.TextContent(type="text", text=json.dumps(result, indent=2))
                ]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_get_extensive_data":
            call_ids = arguments.get("call_ids")
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            user_ids = arguments.get("user_ids")
            workspace_id = arguments.get("workspace_id")
            cursor = arguments.get("cursor")
            context = arguments.get("context", "Extended")
            context_timing = arguments.get("context_timing")
            exposed_fields = arguments.get("exposed_fields")
            try:
                result = await get_extensive_data(
                    call_ids=call_ids,
                    from_date=from_date,
                    to_date=to_date,
                    user_ids=user_ids,
                    workspace_id=workspace_id,
                    cursor=cursor,
                    context=context,
                    context_timing=context_timing,
                    exposed_fields=exposed_fields,
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_get_call_transcripts":
            call_ids = arguments.get("call_ids")
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            workspace_id = arguments.get("workspace_id")
            cursor = arguments.get("cursor")
            try:
                result = await get_call_transcripts(
                    call_ids=call_ids,
                    from_date=from_date,
                    to_date=to_date,
                    workspace_id=workspace_id,
                    cursor=cursor,
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_list_calls":
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            
            if not from_date or not to_date:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'from_date' and 'to_date' are required parameters.",
                    )
                ]
            
            limit = arguments.get("limit", 50)
            cursor = arguments.get("cursor")
            workspace_id = arguments.get("workspace_id")
            try:
                result = await list_calls(from_date, to_date, limit, cursor, workspace_id)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_get_call_by_id":
            call_id = arguments.get("call_id")
            
            if not call_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'call_id' is a required parameter.",
                    )
                ]
            
            try:
                result = await get_call_by_id(call_id)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_add_new_call":
            # Validate required fields
            required_fields = ["clientUniqueId", "actualStart", "parties", "direction", "primaryUser"]
            missing_fields = [field for field in required_fields if field not in arguments]
            if missing_fields:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: Missing required fields: {', '.join(missing_fields)}",
                    )
                ]
            
            try:
                # Pass the entire arguments dict as the call_data
                result = await add_new_call(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract credentials from headers
        credentials = extract_credentials(request)
        
        # Set the credentials in context for this request
        access_key_token = access_key_context.set(credentials['access_key'])
        access_key_secret_token = access_key_secret_context.set(credentials['access_key_secret'])
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            access_key_context.reset(access_key_token)
            access_key_secret_context.reset(access_key_secret_token)
        
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract credentials from headers
        credentials = extract_credentials(scope)
        
        # Set the credentials in context for this request
        access_key_token = access_key_context.set(credentials['access_key'])
        access_key_secret_token = access_key_secret_context.set(credentials['access_key_secret'])
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            access_key_context.reset(access_key_token)
            access_key_secret_context.reset(access_key_secret_token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Gong MCP Server started")
            try:
                yield
            finally:
                logger.info("Gong MCP Server shutting down")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info("Server listening on port %s", port)
    logger.info("SSE endpoint: http://localhost:%s/sse", port)
    logger.info("StreamableHTTP endpoint: http://localhost:%s/mcp", port)

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0

if __name__ == "__main__":
    main() 