import os
import json
import logging
import asyncio
from typing import Any, Dict

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from tools import (
    mailchimp_token_context,
    ping_mailchimp,
    get_account_info,
    get_all_audiences,
    create_audience,
    get_audience_info,
    update_audience,
    delete_audience,
    get_audience_members,
    add_member_to_audience,
    get_member_info,
    update_member,
    delete_member,
    add_member_tags,
    remove_member_tags,
    get_member_activity,
    get_all_campaigns,
    create_campaign,
    get_campaign_info,
    set_campaign_content,
    send_campaign,
    schedule_campaign,
    delete_campaign,
)

# Load env early
load_dotenv()

logger = logging.getLogger("mailchimp-mcp-server")
logging.basicConfig(level=logging.INFO)

MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY") or ""

async def run_server(log_level: str = "INFO"):
    """Run the Mailchimp MCP server with stdio transport for Claude Desktop."""
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Set the API key in context
    if MAILCHIMP_API_KEY:
        mailchimp_token_context.set(MAILCHIMP_API_KEY)
        logger.info("Mailchimp API key configured")
    else:
        logger.warning("No Mailchimp API key found in environment")
    
    app = Server("mailchimp-mcp-server")

    # ----------------------------- Tool Registry -----------------------------#
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List all available Mailchimp tools."""
        tools = [
            # Auth/Account tools
            types.Tool(
                name="mailchimp_ping",
                description="Test Mailchimp Connection - verify API authentication is working correctly.",
                inputSchema={"type": "object", "properties": {}},
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_ACCOUNT", "readOnlyHint": True})
            ),
            types.Tool(
                name="mailchimp_get_account_info",
                description="Get Account Information - retrieve comprehensive account details.",
                inputSchema={"type": "object", "properties": {}},
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_ACCOUNT", "readOnlyHint": True})
            ),
            
            # Audience/List management tools
            types.Tool(
                name="mailchimp_get_all_audiences",
                description="Get All Audiences - retrieve all email lists in the account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "default": 10, "minimum": 1, "maximum": 1000},
                        "offset": {"type": "integer", "default": 0, "minimum": 0}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_AUDIENCE", "readOnlyHint": True})
            ),
            types.Tool(
                name="mailchimp_create_audience",
                description="Create New Audience - create a new email list.",
                inputSchema={
                    "type": "object",
                    "required": ["name", "contact", "permission_reminder", "from_name", "from_email", "subject"],
                    "properties": {
                        "name": {"type": "string"},
                        "contact": {
                            "type": "object",
                            "properties": {
                                "company": {"type": "string"},
                                "address1": {"type": "string"},
                                "city": {"type": "string"},
                                "state": {"type": "string"},
                                "zip": {"type": "string"},
                                "country": {"type": "string"},
                                "phone": {"type": "string"}
                            },
                            "required": ["company", "address1", "city", "state", "zip", "country"]
                        },
                        "permission_reminder": {"type": "string"},
                        "from_name": {"type": "string"},
                        "from_email": {"type": "string"},
                        "subject": {"type": "string"},
                        "language": {"type": "string", "default": "EN_US"},
                        "email_type_option": {"type": "boolean", "default": False},
                        "double_optin": {"type": "boolean", "default": False},
                        "has_welcome": {"type": "boolean", "default": False}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_AUDIENCE"})
            ),
            types.Tool(
                name="mailchimp_get_audience_info",
                description="Get Audience Details - detailed information about a specific audience.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {"list_id": {"type": "string"}}
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_AUDIENCE", "readOnlyHint": True})
            ),
            types.Tool(
                name="mailchimp_update_audience",
                description="Update Audience Settings - modify audience configuration.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "name": {"type": "string"},
                        "contact": {"type": "object"},
                        "permission_reminder": {"type": "string"},
                        "from_name": {"type": "string"},
                        "from_email": {"type": "string"},
                        "subject": {"type": "string"},
                        "language": {"type": "string"},
                        "email_type_option": {"type": "boolean"},
                        "double_optin": {"type": "boolean"},
                        "has_welcome": {"type": "boolean"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_AUDIENCE"})
            ),
            types.Tool(
                name="mailchimp_delete_audience",
                description="Delete Audience - permanently delete an audience and all subscribers.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {"list_id": {"type": "string"}}
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_AUDIENCE"})
            ),
            
            # Member/Contact management tools
            types.Tool(
                name="mailchimp_get_audience_members",
                description="Get Audience Members - retrieve contacts from an audience.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "count": {"type": "integer", "default": 10, "minimum": 1, "maximum": 1000},
                        "offset": {"type": "integer", "default": 0, "minimum": 0},
                        "status": {
                            "type": "string",
                            "enum": ["subscribed", "unsubscribed", "cleaned", "pending", "transactional"]
                        },
                        "since_timestamp_opt": {"type": "string"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_MEMBER", "readOnlyHint": True})
            ),
            types.Tool(
                name="mailchimp_add_member_to_audience",
                description="Add Member to Audience - add a new contact to an audience.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "email_address"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "email_address": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["subscribed", "unsubscribed", "cleaned", "pending", "transactional"],
                            "default": "subscribed"
                        },
                        "merge_fields": {"type": "object"},
                        "interests": {"type": "object"},
                        "language": {"type": "string"},
                        "vip": {"type": "boolean"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "ip_signup": {"type": "string"},
                        "timestamp_signup": {"type": "string"},
                        "ip_opt": {"type": "string"},
                        "timestamp_opt": {"type": "string"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_MEMBER"})
            ),
            types.Tool(
                name="mailchimp_get_member_info",
                description="Get Member Details - detailed information about a specific member.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "email_address"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "email_address": {"type": "string"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_MEMBER", "readOnlyHint": True})
            ),
            types.Tool(
                name="mailchimp_update_member",
                description="Update Member - modify existing member information.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "email_address"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "email_address": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["subscribed", "unsubscribed", "cleaned", "pending", "transactional"]
                        },
                        "merge_fields": {"type": "object"},
                        "interests": {"type": "object"},
                        "language": {"type": "string"},
                        "vip": {"type": "boolean"},
                        "ip_opt": {"type": "string"},
                        "timestamp_opt": {"type": "string"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_MEMBER"})
            ),
            types.Tool(
                name="mailchimp_delete_member",
                description="Delete Member - permanently remove a member from an audience.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "email_address"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "email_address": {"type": "string"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_MEMBER"})
            ),
            types.Tool(
                name="mailchimp_add_member_tags",
                description="Add Member Tags - add organizational tags to a member.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "email_address", "tags"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "email_address": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_MEMBER"})
            ),
            types.Tool(
                name="mailchimp_remove_member_tags",
                description="Remove Member Tags - remove tags from a specific member.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "email_address", "tags"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "email_address": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_MEMBER"})
            ),
            types.Tool(
                name="mailchimp_get_member_activity",
                description="Get Member Activity - retrieve recent activity history for a member.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "email_address"],
                    "properties": {
                        "list_id": {"type": "string"},
                        "email_address": {"type": "string"},
                        "count": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_MEMBER", "readOnlyHint": True})
            ),
            
            # Campaign management tools
            types.Tool(
                name="mailchimp_get_all_campaigns",
                description="Get All Campaigns - retrieve campaigns with optional filtering.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "default": 10, "minimum": 1, "maximum": 1000},
                        "offset": {"type": "integer", "default": 0, "minimum": 0},
                        "type": {"type": "string", "enum": ["regular", "plaintext", "absplit", "rss", "variate"]},
                        "status": {"type": "string", "enum": ["save", "paused", "schedule", "sending", "sent", "canceled", "canceling", "archived"]},
                        "before_send_time": {"type": "string"},
                        "since_send_time": {"type": "string"},
                        "before_create_time": {"type": "string"},
                        "since_create_time": {"type": "string"},
                        "list_id": {"type": "string"},
                        "folder_id": {"type": "string"},
                        "sort_field": {"type": "string", "enum": ["create_time", "send_time"]},
                        "sort_dir": {"type": "string", "enum": ["ASC", "DESC"]}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_CAMPAIGN", "readOnlyHint": True})
            ),
            types.Tool(
                name="mailchimp_create_campaign",
                description="Create Campaign - create a new email campaign in draft mode.",
                inputSchema={
                    "type": "object",
                    "required": ["type", "list_id", "subject_line", "from_name", "reply_to"],
                    "properties": {
                        "type": {"type": "string", "enum": ["regular", "plaintext", "absplit", "rss", "variate"]},
                        "list_id": {"type": "string"},
                        "subject_line": {"type": "string"},
                        "from_name": {"type": "string"},
                        "reply_to": {"type": "string"},
                        "title": {"type": "string"},
                        "folder_id": {"type": "string"},
                        "authenticate": {"type": "boolean", "default": True},
                        "auto_footer": {"type": "boolean", "default": True},
                        "inline_css": {"type": "boolean", "default": True},
                        "auto_tweet": {"type": "boolean", "default": False},
                        "fb_comments": {"type": "boolean", "default": True},
                        "timewarp": {"type": "boolean", "default": False},
                        "template_id": {"type": "integer"},
                        "drag_and_drop": {"type": "boolean", "default": True}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_CAMPAIGN"})
            ),
            types.Tool(
                name="mailchimp_get_campaign_info",
                description="Get Campaign Details - detailed information about a campaign.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_id"],
                    "properties": {"campaign_id": {"type": "string"}}
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_CAMPAIGN", "readOnlyHint": True})
            ),
            types.Tool(
                name="mailchimp_set_campaign_content",
                description="Set Campaign Content - add HTML content, plain text, or template to a campaign.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_id"],
                    "properties": {
                        "campaign_id": {"type": "string"},
                        "html": {"type": "string"},
                        "plain_text": {"type": "string"},
                        "url": {"type": "string"},
                        "template": {"type": "object"},
                        "archive": {"type": "object"},
                        "variate_contents": {"type": "array"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_CAMPAIGN"})
            ),
            types.Tool(
                name="mailchimp_send_campaign",
                description="Send Campaign - send a campaign immediately to all recipients.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_id"],
                    "properties": {"campaign_id": {"type": "string"}}
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_CAMPAIGN"})
            ),
            types.Tool(
                name="mailchimp_schedule_campaign",
                description="Schedule Campaign - schedule a campaign for delivery at a specific time.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_id", "schedule_time"],
                    "properties": {
                        "campaign_id": {"type": "string"},
                        "schedule_time": {"type": "string"},
                        "timewarp": {"type": "boolean", "default": False},
                        "batch_delay": {"type": "integer"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_CAMPAIGN"})
            ),
            types.Tool(
                name="mailchimp_delete_campaign",
                description="Delete Campaign - permanently delete a draft campaign.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_id"],
                    "properties": {"campaign_id": {"type": "string"}}
                },
                annotations=types.ToolAnnotations(**{"category": "MAILCHIMP_CAMPAIGN"})
            ),
        ]
        
        logger.info(f"Returning {len(tools)} tools")
        return tools

    # ---------------------------- Tool Dispatcher ----------------------------#
    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
        logger.info(f"Calling tool: {name}")
        
        try:
            # Auth/Account tools
            if name == "mailchimp_ping":
                result = await ping_mailchimp()
            elif name == "mailchimp_get_account_info":
                result = await get_account_info()
            
            # Audience tools
            elif name == "mailchimp_get_all_audiences":
                result = await get_all_audiences(
                    count=arguments.get("count", 10),
                    offset=arguments.get("offset", 0)
                )
            elif name == "mailchimp_create_audience":
                required_args = ["name", "contact", "permission_reminder", "from_name", "from_email", "subject"]
                for arg in required_args:
                    if arg not in arguments:
                        raise ValueError(f"Missing required argument: {arg}")
                result = await create_audience(
                    name=arguments["name"],
                    contact=arguments["contact"],
                    permission_reminder=arguments["permission_reminder"],
                    from_name=arguments["from_name"],
                    from_email=arguments["from_email"],
                    subject=arguments["subject"],
                    language=arguments.get("language", "EN_US"),
                    email_type_option=arguments.get("email_type_option", False),
                    double_optin=arguments.get("double_optin", False),
                    has_welcome=arguments.get("has_welcome", False)
                )
            elif name == "mailchimp_get_audience_info":
                if not arguments.get("list_id"):
                    raise ValueError("Missing required argument: list_id")
                result = await get_audience_info(arguments["list_id"])
            elif name == "mailchimp_update_audience":
                if not arguments.get("list_id"):
                    raise ValueError("Missing required argument: list_id")
                result = await update_audience(
                    list_id=arguments["list_id"],
                    name=arguments.get("name"),
                    contact=arguments.get("contact"),
                    permission_reminder=arguments.get("permission_reminder"),
                    from_name=arguments.get("from_name"),
                    from_email=arguments.get("from_email"),
                    subject=arguments.get("subject"),
                    language=arguments.get("language"),
                    email_type_option=arguments.get("email_type_option"),
                    double_optin=arguments.get("double_optin"),
                    has_welcome=arguments.get("has_welcome")
                )
            elif name == "mailchimp_delete_audience":
                if not arguments.get("list_id"):
                    raise ValueError("Missing required argument: list_id")
                result = await delete_audience(arguments["list_id"])
            
            # Member tools
            elif name == "mailchimp_get_audience_members":
                if not arguments.get("list_id"):
                    raise ValueError("Missing required argument: list_id")
                result = await get_audience_members(
                    list_id=arguments["list_id"],
                    count=arguments.get("count", 10),
                    offset=arguments.get("offset", 0),
                    status=arguments.get("status"),
                    since_timestamp_opt=arguments.get("since_timestamp_opt")
                )
            elif name == "mailchimp_add_member_to_audience":
                if not arguments.get("list_id") or not arguments.get("email_address"):
                    raise ValueError("Missing required arguments: list_id and email_address")
                result = await add_member_to_audience(
                    list_id=arguments["list_id"],
                    email_address=arguments["email_address"],
                    status=arguments.get("status", "subscribed"),
                    merge_fields=arguments.get("merge_fields"),
                    interests=arguments.get("interests"),
                    language=arguments.get("language"),
                    vip=arguments.get("vip"),
                    tags=arguments.get("tags"),
                    ip_signup=arguments.get("ip_signup"),
                    timestamp_signup=arguments.get("timestamp_signup"),
                    ip_opt=arguments.get("ip_opt"),
                    timestamp_opt=arguments.get("timestamp_opt")
                )
            elif name == "mailchimp_get_member_info":
                if not arguments.get("list_id") or not arguments.get("email_address"):
                    raise ValueError("Missing required arguments: list_id and email_address")
                result = await get_member_info(arguments["list_id"], arguments["email_address"])
            elif name == "mailchimp_update_member":
                if not arguments.get("list_id") or not arguments.get("email_address"):
                    raise ValueError("Missing required arguments: list_id and email_address")
                result = await update_member(
                    list_id=arguments["list_id"],
                    email_address=arguments["email_address"],
                    status=arguments.get("status"),
                    merge_fields=arguments.get("merge_fields"),
                    interests=arguments.get("interests"),
                    language=arguments.get("language"),
                    vip=arguments.get("vip"),
                    ip_opt=arguments.get("ip_opt"),
                    timestamp_opt=arguments.get("timestamp_opt")
                )
            elif name == "mailchimp_delete_member":
                if not arguments.get("list_id") or not arguments.get("email_address"):
                    raise ValueError("Missing required arguments: list_id and email_address")
                result = await delete_member(arguments["list_id"], arguments["email_address"])
            elif name == "mailchimp_add_member_tags":
                if not all([arguments.get("list_id"), arguments.get("email_address"), arguments.get("tags")]):
                    raise ValueError("Missing required arguments: list_id, email_address, and tags")
                result = await add_member_tags(arguments["list_id"], arguments["email_address"], arguments["tags"])
            elif name == "mailchimp_remove_member_tags":
                if not all([arguments.get("list_id"), arguments.get("email_address"), arguments.get("tags")]):
                    raise ValueError("Missing required arguments: list_id, email_address, and tags")
                result = await remove_member_tags(arguments["list_id"], arguments["email_address"], arguments["tags"])
            elif name == "mailchimp_get_member_activity":
                if not arguments.get("list_id") or not arguments.get("email_address"):
                    raise ValueError("Missing required arguments: list_id and email_address")
                result = await get_member_activity(arguments["list_id"], arguments["email_address"], arguments.get("count", 10))
            
            # Campaign tools
            elif name == "mailchimp_get_all_campaigns":
                result = await get_all_campaigns(
                    count=arguments.get("count", 10),
                    offset=arguments.get("offset", 0),
                    type=arguments.get("type"),
                    status=arguments.get("status"),
                    before_send_time=arguments.get("before_send_time"),
                    since_send_time=arguments.get("since_send_time"),
                    before_create_time=arguments.get("before_create_time"),
                    since_create_time=arguments.get("since_create_time"),
                    list_id=arguments.get("list_id"),
                    folder_id=arguments.get("folder_id"),
                    sort_field=arguments.get("sort_field"),
                    sort_dir=arguments.get("sort_dir")
                )
            elif name == "mailchimp_create_campaign":
                required_args = ["type", "list_id", "subject_line", "from_name", "reply_to"]
                for arg in required_args:
                    if arg not in arguments:
                        raise ValueError(f"Missing required argument: {arg}")
                result = await create_campaign(
                    type=arguments["type"],
                    list_id=arguments["list_id"],
                    subject_line=arguments["subject_line"],
                    from_name=arguments["from_name"],
                    reply_to=arguments["reply_to"],
                    title=arguments.get("title"),
                    folder_id=arguments.get("folder_id"),
                    authenticate=arguments.get("authenticate", True),
                    auto_footer=arguments.get("auto_footer", True),
                    inline_css=arguments.get("inline_css", True),
                    auto_tweet=arguments.get("auto_tweet", False),
                    fb_comments=arguments.get("fb_comments", True),
                    timewarp=arguments.get("timewarp", False),
                    template_id=arguments.get("template_id"),
                    drag_and_drop=arguments.get("drag_and_drop", True)
                )
            elif name == "mailchimp_get_campaign_info":
                if not arguments.get("campaign_id"):
                    raise ValueError("Missing required argument: campaign_id")
                result = await get_campaign_info(arguments["campaign_id"])
            elif name == "mailchimp_set_campaign_content":
                if not arguments.get("campaign_id"):
                    raise ValueError("Missing required argument: campaign_id")
                result = await set_campaign_content(
                    campaign_id=arguments["campaign_id"],
                    html=arguments.get("html"),
                    plain_text=arguments.get("plain_text"),
                    url=arguments.get("url"),
                    template=arguments.get("template"),
                    archive=arguments.get("archive"),
                    variate_contents=arguments.get("variate_contents")
                )
            elif name == "mailchimp_send_campaign":
                if not arguments.get("campaign_id"):
                    raise ValueError("Missing required argument: campaign_id")
                result = await send_campaign(arguments["campaign_id"])
            elif name == "mailchimp_schedule_campaign":
                if not arguments.get("campaign_id") or not arguments.get("schedule_time"):
                    raise ValueError("Missing required arguments: campaign_id and schedule_time")
                result = await schedule_campaign(
                    campaign_id=arguments["campaign_id"],
                    schedule_time=arguments["schedule_time"],
                    timewarp=arguments.get("timewarp", False),
                    batch_delay=arguments.get("batch_delay")
                )
            elif name == "mailchimp_delete_campaign":
                if not arguments.get("campaign_id"):
                    raise ValueError("Missing required argument: campaign_id")
                result = await delete_campaign(arguments["campaign_id"])
            
            else:
                error_msg = f"Unknown tool: {name}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=json.dumps({"error": error_msg}))]

            logger.info(f"Tool {name} executed successfully")
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            error_response = {
                "error": f"Tool execution failed: {str(e)}",
                "tool": name,
                "arguments": arguments
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

    # Run with stdio transport for Claude Desktop
    logger.info("Starting Mailchimp MCP server with stdio transport")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


@click.command()
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
def main(log_level: str) -> int:
    """Mailchimp MCP server with stdio transport for Claude Desktop."""
    try:
        asyncio.run(run_server(log_level))
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1


if __name__ == "__main__":
    main()