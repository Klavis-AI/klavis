"""
MCP Agent Example: YouTube + Gmail
----------------------------------

This script demonstrates how to:

1. Load API keys securely from environment variables.
2. Initialize the Klavis client.
3. Create MCP server instances for YouTube and Gmail.
4. Redirect user to Gmail OAuth flow for authorization.
5. Create specialized agents for YouTube and Gmail.
6. Combine them into a root Gemini agent for orchestration.

Requirements:
- A `.env` file containing KLAVIS_API_KEY
- Valid Klavis account with MCP server support
- Browser access for Gmail OAuth flow

Usage:
    Run the following command to launch the Dev UI: adk web
    Run the following command, to chat with your agent: adk run multi_tool_agent
    API Server: adk api_server

Doc:
    https://google.github.io/adk-docs/get-started/quickstart/#run-your-agent
    https://google.github.io/adk-docs/tools/mcp-tools/#further-resources
"""

import os
import logging
import webbrowser
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
    level=logging.INFO,  # Use DEBUG for verbose logging
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("MCP_Agent_Example")

# ----------------------------------------------------------------------
# Environment Setup
# ----------------------------------------------------------------------
load_dotenv()

KLAVIS_API_KEY = os.getenv("KLAVIS_API_KEY")
if not KLAVIS_API_KEY:
    logger.error("❌ Missing KLAVIS_API_KEY in environment variables.")
    raise EnvironmentError("KLAVIS_API_KEY not found in .env file")

logger.info("✅ Loaded KLAVIS_API_KEY from environment.")

# ----------------------------------------------------------------------
# Klavis Client Initialization
# ----------------------------------------------------------------------
logger.info("Initializing Klavis client...")
klavis_client = Klavis(api_key=KLAVIS_API_KEY)
logger.info("✅ Klavis client initialized.")

# ----------------------------------------------------------------------
# Create YouTube MCP Server
# ----------------------------------------------------------------------
logger.info("Creating YouTube MCP server instance...")
youtube_mcp_server = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.YOUTUBE,
    user_id="1234",
    platform_name="Klavis",
)

youtube_mcp_server_url = youtube_mcp_server.server_url
logger.info(
    "✅ YouTube MCP server created at %s (instance id: %s)",
    youtube_mcp_server_url,
    youtube_mcp_server.instance_id,
)

# ----------------------------------------------------------------------
# Create Gmail MCP Server with OAuth
# ----------------------------------------------------------------------
logger.info("Creating Gmail MCP server instance...")
gmail_mcp_server = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.GMAIL,
    user_id="1234",
    platform_name="Klavis",
)

logger.info("✅ Gmail MCP server instance created.")

# Redirect user to Gmail OAuth
if gmail_mcp_server.oauth_url:
    logger.info("🔐 Redirecting to Gmail OAuth authorization page...")
    try:
        webbrowser.open(gmail_mcp_server.oauth_url)
        logger.info("✅ Gmail OAuth page opened in browser.")
    except Exception as e:
        logger.warning("⚠️ Could not open browser automatically. Please visit: %s", gmail_mcp_server.oauth_url)
else:
    logger.error("❌ Gmail server did not return an OAuth URL.")

gmail_mcp_server_url = gmail_mcp_server.server_url
logger.info(
    "✅ Gmail MCP server created at %s (instance id: %s)",
    gmail_mcp_server_url,
    gmail_mcp_server.instance_id,
)

# ----------------------------------------------------------------------
# Agent Setup
# ----------------------------------------------------------------------
logger.info("Setting up agents with MCP toolsets...")

youtube_agent = Agent(
    name="YouTube_Agent",
    model="gemini-2.0-flash",
    description="Agent specialized in handling YouTube queries.",
    instruction="You are a helpful YouTube agent.",
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=youtube_mcp_server_url,
            ),
        )
    ],
)

gmail_agent = Agent(
    name="Gmail_Agent",
    model="gemini-2.0-flash",
    description="Agent specialized in handling Gmail queries.",
    instruction="You are a helpful Gmail agent.",
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=gmail_mcp_server_url,
            ),
        )
    ],
)

gemini_agent = Agent(
    name="Gemini",
    model="gemini-2.0-flash",
    description="Root Orchestrator Agent",
    instruction="You are a helpful orchestrator agent combining Gmail and YouTube capabilities.",
    sub_agents=[youtube_agent, gmail_agent],
)

root_agent = gemini_agent
logger.info("✅ Root agent '%s' initialized and ready.", root_agent.name)
