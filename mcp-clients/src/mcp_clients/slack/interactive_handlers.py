"""
Handlers for Slack interactive components like buttons, modals, and other UI elements.
"""
import logging

logger = logging.getLogger("slack_bot")


def register_interactive_handlers(app):
    """Register all interactive component handlers with the Slack app."""

    @app.action("login_button")
    async def handle_login_button(ack, body, logger):
        """Handle login button click actions"""
        await ack()
        logger.info(f"Login button clicked: {body.get('user', {}).get('id')}")

    @app.action("connect_mcp_server_button")
    async def handle_connect_mcp_server_button(ack, body, logger):
        """Handle connect to MCP server button click actions"""
        await ack()
        logger.info(f"Connect to MCP server button clicked: {body.get('user', {}).get('id')}")
