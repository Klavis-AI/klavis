import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncApp
from slack_bolt.authorization import AuthorizeResult
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from mcp_clients.base_bot import BaseBot
from mcp_clients.config import USE_PRODUCTION_DB
from mcp_clients.llms.base import ChatMessage, Conversation, MessageRole, TextContent, FileContent
from mcp_clients.mcp_client import MCPClient
from mcp_clients.slack.context import SlackBotContext
from mcp_clients.slack.event_routes import LoggingMiddleware, setup_http_routes
from mcp_clients.slack.oauth_routes import setup_oauth_routes
from mcp_clients.slack.settings import settings

if USE_PRODUCTION_DB:
    from mcp_clients.database.database import get_slack_auth_metadata
else:
    # Define dummy function when database is not used
    async def get_slack_auth_metadata(team_id):
        logging.getLogger("slack_bot").info(f"Database operations skipped: get_slack_auth_metadata for {team_id}")
        return {
            "access_token": os.getenv("SLACK_BOT_TOKEN"),
            "app_id": os.getenv("SLACK_APP_ID"),
            "bot_user_id": os.getenv("SLACK_BOT_USER_ID")
        }

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("slack_bot")

# Define long-running tools
LONG_RUNNING_TOOLS = [
    "generate_web_reports",
    "firecrawl_deep_research",
]

app = FastAPI(title="Slack MCP Bot")

# Add logging middleware
app.add_middleware(LoggingMiddleware)


# Add a health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


class SlackBot(BaseBot):
    """
    Slack-specific implementation of the bot.
    Extends the base bot with Slack-specific functionality.
    """

    def __init__(self):
        """
        Initialize the Slack bot.
        """
        super().__init__(platform_name="slack")

        self.app: AsyncApp = AsyncApp(
            signing_secret=settings.SLACK_SIGNING_SECRET,
            authorize=self.authorize
        )

        # Create router for FastAPI
        self.router: APIRouter = APIRouter(tags=["slack"])

        # Create slack handler
        self.slack_handler: AsyncSlackRequestHandler = AsyncSlackRequestHandler(self.app)

        # Add user lock to prevent concurrent message processing
        self.user_locks = {}

        # Register OAuth routes
        self._setup_oauth_routes()

        # Register HTTP routes
        self._setup_http_routes()

        # Register event handlers
        self._setup_event_handlers()

    def _setup_oauth_routes(self) -> None:
        """
        Set up OAuth routes for Slack app installation
        """
        setup_oauth_routes(router=self.router)

    def _setup_http_routes(self) -> None:
        """Set up HTTP routes for the FastAPI integration"""
        setup_http_routes(router=self.router, slack_handler=self.slack_handler)

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for the Slack app"""
        from mcp_clients.slack.message_handlers import register_message_handlers
        from mcp_clients.slack.interactive_handlers import register_interactive_handlers
        # Register message handlers (app mentions and DMs)
        register_message_handlers(self.app, self)
        # Register interactive handlers (buttons, etc.)
        register_interactive_handlers(self.app)

    @staticmethod
    async def authorize(enterprise_id: Optional[str], team_id: Optional[str], logger: logging.Logger) -> Optional[
        AuthorizeResult]:
        """
        The function to authorize an incoming request from Slack by checking if there is a team/user in the installation data.
        
        Args:
            enterprise_id: The enterprise ID from Slack request
            team_id: The team ID from Slack request
            logger: Logger instance
            
        Returns:
            AuthorizeResult: An authorization result object with the bot token information
        """
        logger.info(f"Authorizing Slack request for team_id={team_id}, enterprise_id={enterprise_id}")

        if not team_id:
            logger.error("No team_id provided for authorization")
            return None

        try:
            # Get auth data from database using the team_id
            auth_data = await get_slack_auth_metadata(team_id)

            if not auth_data:
                logger.error(f"No authorization information found for team {team_id}")
                return None

            # Extract token and IDs from auth metadata
            bot_token = auth_data.get("access_token")
            bot_id = auth_data.get("app_id")
            bot_user_id = auth_data.get("bot_user_id")

            if not bot_token:
                logger.error(f"No bot token found for team {team_id}")
                return None

            logger.info(f"Successfully authorized request for team {team_id}")
            return AuthorizeResult(
                enterprise_id=enterprise_id,
                team_id=team_id,
                bot_token=bot_token,
                bot_id=bot_id,
                bot_user_id=bot_user_id
            )
        except Exception as e:
            logger.error(f"Error during Slack authorization: {str(e)}")
            return None

    async def send_message(self, context: SlackBotContext, message: str) -> Optional[Dict[str, Any]]:
        """
        Send a message on Slack.

        Args:
            context: Slack bot context
            message: Message text to send

        Returns:
            Slack message object
        """
        try:
            # Create a client for this specific operation using the token from context
            if hasattr(context, 'bot_token') and context.bot_token:
                client = AsyncWebClient(token=context.bot_token)
            else:
                # If no token in context, use default client as fallback
                client = AsyncWebClient()
                logger.warning("No bot token in context, using default client (likely to fail)")

            message_params = {
                "channel": context.channel_id,
                "text": message
            }

            # Reply in thread if thread_ts is available (for both DMs and public channels)
            if context.thread_ts:
                message_params["thread_ts"] = context.thread_ts

            response = await client.chat_postMessage(**message_params)
            return response
        except SlackApiError as e:
            logger.error(f"Error sending message: {e}")
            return None

    async def _create_special_message_blocks(self, special_content: str) -> tuple:
        """
        Create Slack blocks for special messages based on their content.
        
        Args:
            special_content: The content of the special message
            
        Returns:
            tuple: (blocks, header_text, fallback_text)
        """
        blocks = []
        header_text = ""
        fallback_text = ""

        if special_content.startswith("[Calling tool"):
            # Extract tool name and arguments from the message
            content = special_content.strip("[]")
            # Try to extract tool name and arguments using basic parsing
            try:
                tool_parts = content.split("with arguments")
                tool_name = tool_parts[0].replace("Calling tool", "").strip()
                tool_args = tool_parts[1].strip() if len(tool_parts) > 1 else ""
            except:
                tool_name = ""
                tool_args = content

            header_text = "✨ MCP Server Call"
            fallback_text = "Tool call in progress"

            waiting_message = "⏳ _Working on your request..._"
            if any(tool in tool_name for tool in LONG_RUNNING_TOOLS):
                waiting_message = f"⏳ _This tool may take several minutes to complete..._"

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": header_text,
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Tool:*\n`{tool_name}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Arguments:*\n```{tool_args[:200]}{'...' if len(tool_args) > 200 else ''}```"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": waiting_message
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
        elif "still running" in special_content:
            header_text = "Tool Running"
            fallback_text = "Tool still running"

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⏳ Tool Still Running",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": special_content.strip("[]")
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "_Tool is still running. Please wait..._"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
        else:
            # Default case
            header_text = "Special Message"
            fallback_text = "Special message received"

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "ℹ️ System Message",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": special_content.strip("[]")
                    }
                },
                {
                    "type": "divider"
                }
            ]

        return blocks, fallback_text

    async def _send_special_message(self, context: SlackBotContext, special_content: str) -> Optional[Dict[str, Any]]:
        """
        Send a special message with formatted blocks.
        
        Args:
            context: Slack bot context
            special_content: The content of the special message
            
        Returns:
            Optional response from the API call
        """
        blocks, fallback_text = await self._create_special_message_blocks(special_content)

        # Create a client for this specific operation
        if hasattr(context, 'bot_token') and context.bot_token:
            client = AsyncWebClient(token=context.bot_token)
            message_params = {
                "channel": context.channel_id,
                "blocks": blocks,
                "text": fallback_text
            }
            if context.thread_ts:
                message_params["thread_ts"] = context.thread_ts
            return await client.chat_postMessage(**message_params)
        return None

    async def process_query_with_streaming(
            self,
            mcp_client: MCPClient,
            messages_history: List[ChatMessage],
            context: SlackBotContext
    ) -> Optional[Dict[str, Any]]:
        """
        Process a query with streaming in Slack-specific way.

        Args:
            mcp_client: MCP client instance
            messages_history: List of previous messages
            context: Slack bot context for the interaction

        Returns:
            Final message object or None
        """
        # Get the platform-specific message split token
        MESSAGE_SPLIT_TOKEN = mcp_client.get_message_split_token()

        try:
            buffer = ""
            async with asyncio.timeout(settings.STREAMING_TIMEOUT):
                async for chunk in mcp_client.process_query_stream(
                        messages_history, self.store_new_messages if USE_PRODUCTION_DB else None
                ):
                    buffer += chunk
                    # Check if the chunk contains a message split token
                    if MESSAGE_SPLIT_TOKEN in buffer:
                        # Split the chunk at the token
                        parts = buffer.split(MESSAGE_SPLIT_TOKEN)

                        # Process subsequent parts except the last one
                        for part in parts[:-1]:
                            if part.strip():
                                # Check if this is a special message
                                if "<special>" in part:
                                    # Extract the special message content
                                    special_content = part.split("<special>")[1].strip()
                                    await self._send_special_message(context, special_content)
                                else:
                                    # Regular message
                                    await self.send_message(context, part)
                                # Short delay to make messages feel natural
                                await asyncio.sleep(settings.STREAMING_SLEEP_DELAY)

                        buffer = parts[-1]
                # Send any remaining content
                if buffer.strip():
                    # Check if the remaining buffer contains a special message
                    if "<special>" in buffer:
                        special_content = buffer.split("<special>")[1].strip()
                        return await self._send_special_message(context, special_content)
                    return await self.send_message(context, buffer)
        except asyncio.TimeoutError:
            logger.error("Timeout occurred during streaming response")
            return await self.send_message(context, "The response took too long. Please try again.")
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return await self.send_message(context, f"Error processing query: {str(e)}")

    async def get_messages_history(self, conversation: Conversation, slack_context: SlackBotContext, limit: int = 6) -> \
            List[ChatMessage]:
        """
        Get the previous messages for the conversation.
        
        Args:
            context: Slack bot context containing channel info
            limit: Maximum number of previous messages to retrieve (not including the current message)
            
        Returns:
            List of ChatMessage objects representing previous messages
        """
        chat_messages = []
        try:
            # Create a client with the token from context
            if hasattr(slack_context, 'bot_token') and slack_context.bot_token:
                auth_token = slack_context.bot_token
            else:
                auth_token = settings.SLACK_BOT_TOKEN
                logger.warning("No bot token in context, using default token")
            client = AsyncWebClient(token=auth_token)
            # Parameters for the conversations_history API call
            params = {
                "channel": slack_context.channel_id,
                "limit": limit + 1
            }

            # If thread_ts is provided, get messages from that thread
            if hasattr(slack_context, 'thread_ts') and slack_context.thread_ts:
                params["ts"] = slack_context.thread_ts
                # For threads, we need to use replies API instead
                response = await client.conversations_replies(**params)
                logger.info(f"--- Replies response: {response}")
            else:
                # For regular channel messages
                response = await client.conversations_history(**params)
                logger.info(f"--- History response: {response}")
            if response["ok"]:
                messages = response["messages"]

                # Process each message
                for message in messages:
                    content = []
                    is_bot_message = "bot_id" in message
                    if is_bot_message:
                        role = MessageRole.ASSISTANT
                        content.append(
                            TextContent(text=message.get("text", ""))
                        )
                    else:
                        role = MessageRole.USER
                        # Try to get username from user field if available
                        user_id = message.get("user", "unknown")
                        try:
                            # Get user info
                            user_info = await client.users_info(user=user_id)
                            if user_info["ok"]:
                                username = user_info["user"].get("real_name", user_id)
                            else:
                                username = user_id
                        except:
                            username = user_id
                        content.append(
                            TextContent(text=f"User {username} says: {message.get('text', '')}")
                        )
                        for file in message.get("files", []):
                            content.append(
                                FileContent(
                                    url=file.get("url_private"),
                                    filename=file.get("name"),
                                    extension=file.get("filetype"),
                                    auth_token=auth_token
                                )
                            )
                    # Create a ChatMessage object
                    chat_message = ChatMessage(
                        role=role,
                        content=content,
                    )

                    chat_messages.append(chat_message)

            else:
                logger.error(f"Error fetching Slack conversation history: {response.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Error retrieving previous messages: {e}", exc_info=True)
            # Return empty list in case of error
            return []

        return chat_messages

    def get_router(self) -> APIRouter:
        """
        Get the FastAPI router for Slack endpoints.
        
        Returns:
            FastAPI router with Slack endpoints
        """
        return self.router

    def run(self, port: Optional[int] = None) -> None:
        """
        Run the bot (placeholder - overridden by FastAPI integration)
        
        Args:
            port: The port to run on (ignored for SlackBot)
        """
        pass


def main():
    # Initialize the bot and register its router with the app
    bot = SlackBot()
    app.include_router(bot.get_router())
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)


# For local development
if __name__ == "__main__":
    main()
