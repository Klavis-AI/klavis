"""
YouTube MCP Agent Example
-------------------------

This script demonstrates how to:

1. Load API keys from environment variables.
2. Initialize the Klavis client.
3. Create a YouTube MCP server instance.
4. Set up a Google ADK Agent with access to that MCP server.
"""

import os
import logging
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from klavis import Klavis
from klavis.types import McpServerName

# ----------------------------------------------------------------------
# Logging Configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,  # Use DEBUG if you want more detail
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("YouTubeMCP")

# ----------------------------------------------------------------------
# Environment Setup
# ----------------------------------------------------------------------
load_dotenv()

KLAVIS_API_KEY = os.getenv("KLAVIS_API_KEY")
if not KLAVIS_API_KEY:
    logger.error("❌ Missing KLAVIS_API_KEY in environment variables.")
    raise EnvironmentError("KLAVIS_API_KEY not found in .env file")

# ----------------------------------------------------------------------
# Klavis Client Initialization
# ----------------------------------------------------------------------
logger.info("Initializing Klavis client...")
klavis_client = Klavis(api_key=KLAVIS_API_KEY)

# ----------------------------------------------------------------------
# Create YouTube MCP Server
# ----------------------------------------------------------------------
logger.info("Creating YouTube MCP server instance...")
youtube_mcp_instance = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.YOUTUBE,
    user_id="1234",
    platform_name="Klavis",
)

youtube_mcp_server_url = youtube_mcp_instance.server_url
logger.info(
    "✅ YouTube MCP server created at %s (instance id: %s)",
    youtube_mcp_server_url,
    youtube_mcp_instance.instance_id,
)

# ----------------------------------------------------------------------
# Agent Setup
# ----------------------------------------------------------------------
logger.info("Setting up root agent with MCP toolset...")

root_agent = Agent(
    name="Gemini",
    model="gemini-2.0-flash",
    description="An AI agent that can answer user questions",
    instruction="You are a helpful agent who can answer user questions",
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=youtube_mcp_server_url,
            ),
        )
    ],
)

logger.info("✅ Root agent '%s' initialized and ready.", root_agent.name)
