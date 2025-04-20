"""
Handlers for Slack message events, including app mentions and direct messages.
"""
import asyncio
import logging
from typing import Dict, Any, List
from urllib.parse import quote

from mcp_clients.config import USE_PRODUCTION_DB
from mcp_clients.slack.context import SlackBotContext
from mcp_clients.slack.settings import settings

logger = logging.getLogger("slack_bot")

if USE_PRODUCTION_DB:
    from mcp_clients.database.database import get_mcp_client_id_by_slack_info
else:
    # Define dummy function when database is not used
    async def get_mcp_client_id_by_slack_info(team_id, user_id):
        logger.info(
            f"Database operations skipped: get_mcp_client_id_by_slack_info for team_id={team_id}, user_id={user_id}")
        return None


def create_login_blocks(platform_username: str, platform_user_id: str, team_id: str = None) -> List[Dict[str, Any]]:
    """
    Create Slack blocks with a login button similar to Discord format
    
    Args:
        platform_username: Slack username to pass in URL
        platform_user_id: Slack user ID to pass in URL
        team_id: Slack team ID to pass in URL
        
    Returns:
        A list of Slack block objects with a login button
    """
    # Construct login URL with query parameters
    login_url = f"{settings.WEBSITE_URL}/auth/sign-in"

    # URL encode the parameters
    encoded_username = quote(platform_username)
    login_url = f"{login_url}?platform=slack&external_user_id={platform_user_id}&external_username={encoded_username}"

    # Add team_id if available
    if team_id:
        login_url = f"{login_url}&external_id={team_id}"

    # Create blocks with login button
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"You need to link your Slack account with our website to use the AI assistant features using the login button below."
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Login",
                        "emoji": True
                    },
                    "action_id": "login_button",
                    "url": login_url,
                    "style": "primary"
                }
            ]
        }
    ]


def create_connect_mcp_server_blocks(mcp_client_id: str = None) -> List[Dict[str, Any]]:
    """
    Create Slack blocks with warning and a button to connect to MCP servers
    
    Args:
        mcp_client_id: Optional MCP client ID to add to the URL
    
    Returns:
        A list of Slack block objects with warning and connect button
    """
    # Construct configure URL
    configure_url = f"{settings.WEBSITE_URL}/home"

    # Add mcp_client_id as path parameter if available
    if mcp_client_id:
        configure_url = f"{configure_url}/mcp-client/{mcp_client_id}"

    # Create blocks with warning and connect button
    return [
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "⚠️ Not connected to any MCP server. Some features may be limited."
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Connect",
                        "emoji": True
                    },
                    "action_id": "connect_mcp_server_button",
                    "url": configure_url,
                    "style": "primary"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "⏳ _Working on your request..._"
                }
            ]
        },
    ]


def register_message_handlers(app, bot):
    """Register all message-related event handlers with the Slack app."""
    # Add user lock to prevent concurrent message processing
    if not hasattr(bot, 'user_locks'):
        bot.user_locks = {}

    async def add_loading_reaction(client, channel_id, message_ts):
        """Add loading reaction to a message"""
        try:
            await client.reactions_add(
                channel=channel_id,
                timestamp=message_ts,
                name="thinking_face"
            )
        except Exception as e:
            logger.error(f"Error adding loading reaction: {e}")

    async def remove_loading_reaction(client, channel_id, message_ts):
        """Remove loading reaction from a message"""
        try:
            await client.reactions_remove(
                channel=channel_id,
                timestamp=message_ts,
                name="thinking_face"
            )
        except Exception as e:
            logger.error(f"Error removing loading reaction: {e}")

    @app.event("app_mention")
    async def handle_app_mention(event, context, client, ack, logger):
        """Handle mentions of the bot in public channels"""
        await ack()

        # Retrieve the bot token from the context provided by the authorize method
        bot_token = context.get("bot_token")
        if not bot_token:
            logger.error("No bot token available in context")
            return

        user_id = event.get("user")
        text = event.get("text", "")
        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts", event.get("ts"))
        message_ts = event.get("ts")

        await add_loading_reaction(client, channel_id, message_ts)

        # Check if user has a message currently being processed
        if user_id not in bot.user_locks:
            bot.user_locks[user_id] = asyncio.Lock()

        # Try to acquire the lock, but don't block if it's already locked
        if bot.user_locks[user_id].locked():
            try:
                await client.chat_postMessage(
                    channel=channel_id,
                    text="I'm still processing your previous message. Please wait a moment before sending another one.",
                    thread_ts=thread_ts
                )
                await remove_loading_reaction(client, channel_id, message_ts)
            except Exception as e:
                logger.error(f"Error sending busy message: {e}")
            return

        # Extract clean text from mention (remove the bot mention)
        clean_text = text
        # Find the bot mention pattern and remove it
        if "<@" in text:
            parts = text.split(">", 1)
            if len(parts) > 1:
                clean_text = parts[1].strip()

        logger.info(f"--- Received app mention from user {user_id} in channel {channel_id}: {clean_text}")

        # Process the message with the lock acquired
        try:
            async with asyncio.timeout(200), bot.user_locks[user_id]:
                # Create Slack context with the bot token
                slack_context = SlackBotContext(
                    platform_name="slack",
                    user_id=user_id,
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    user_message=event,
                    bot_token=bot_token
                )

                verification_result = await bot.verify_user(slack_context)

                if not verification_result["connected"]:
                    await remove_loading_reaction(client, channel_id, message_ts)
                    # Get user information to pass to login blocks
                    try:
                        user_info = await client.users_info(user=user_id)
                        if user_info["ok"]:
                            username = user_info["user"].get("real_name", user_id)
                        else:
                            username = user_id
                    except Exception as e:
                        logger.error(f"Error getting user info: {e}")
                        username = user_id

                    # Get team ID from context
                    team_id = context.get("team_id")

                    try:
                        # Send login blocks as a DM to the user
                        await client.chat_postMessage(
                            channel=user_id,  # Sending to user's DM
                            text="Please login to use the Klavis.ai bot",
                            blocks=create_login_blocks(username, user_id, team_id)
                        )

                        # Notify in the thread that login instructions were sent via DM
                        await client.chat_postMessage(
                            channel=channel_id,
                            thread_ts=thread_ts,
                            text="I've sent you instructions on how to login via direct message. Please check your DMs to connect."
                        )
                    except Exception as e:
                        logger.error(f"Error sending login message: {e}")
                    return

                slack_context.mcp_client_id = verification_result["mcp_client_id"]
                slack_context.llm_id = verification_result["llm_id"]

                server_urls = await bot.get_server_urls(slack_context)
                if not server_urls:
                    team_id = context.get("team_id")
                    mcp_client_id = await get_mcp_client_id_by_slack_info(team_id, user_id)

                    await client.chat_postMessage(
                        channel=channel_id,
                        thread_ts=thread_ts,
                        blocks=create_connect_mcp_server_blocks(
                            mcp_client_id or verification_result.get("mcp_client_id"))
                    )
                    # Don't return here to allow processing with 0 MCP server

                if clean_text:
                    usage_under_limit = await bot.check_and_update_usage_limit(slack_context)
                    if not usage_under_limit:
                        await bot.send_message(
                            slack_context,
                            "You have reached your usage limit. Please upgrade your account to continue.",
                        )
                        await remove_loading_reaction(client, channel_id, message_ts)
                        return

                    try:
                        mcp_client = await bot.initialize_mcp_client(
                            context=slack_context, server_urls=server_urls
                        )
                        messages_history = await bot.get_messages_history(mcp_client.conversation, slack_context)

                        # Process the query and return the result from the streaming implementation
                        await bot.process_query_with_streaming(
                            mcp_client, messages_history, slack_context
                        )
                    except Exception as e:
                        logger.error(f"Error processing query: {e}", exc_info=True)
                        await bot.send_message(slack_context, f"Error processing query: {str(e)}")
                    finally:
                        await remove_loading_reaction(client, channel_id, message_ts)
                        logger.info(
                            f" --- Completed processing query from user {user_id} in channel {channel_id}: {clean_text}")
                        await mcp_client.cleanup()

        except asyncio.TimeoutError:
            logger.warning(
                f"Processing timed out for user {user_id} in channel {channel_id} after 200 seconds. Lock released.")
            try:
                await client.chat_postMessage(
                    channel=channel_id,
                    text="The previous operation took too long and timed out. Please try again.",
                    thread_ts=thread_ts
                )
            except Exception as e:
                logger.error(f"Error sending timeout message: {e}")
        finally:
            # Ensure reaction is removed regardless of timeout or success/failure
            await remove_loading_reaction(client, channel_id, message_ts)
            # Lock is released automatically by async with when exiting the block or due to timeout/exception

    @app.event("message")
    async def handle_direct_message(event, context, client, ack, logger):
        """Handle direct messages to the bot"""
        # Only process DMs, not messages in channels
        if event.get("channel_type") == "im" and not event.get("bot_id"):
            await ack()

            # Retrieve the bot token from the context provided by the authorize method
            bot_token = context.get("bot_token")
            if not bot_token:
                logger.error("No bot token available in context")
                return

            user_id = event.get("user")
            text = event.get("text", "")
            channel_id = event.get("channel")
            thread_ts = event.get("thread_ts",
                                  event.get("ts"))  # since we reply DM in thread, we set thread_ts to event ts
            message_ts = event.get("ts")

            await add_loading_reaction(client, channel_id, message_ts)

            # Check if user has a message currently being processed
            if user_id not in bot.user_locks:
                bot.user_locks[user_id] = asyncio.Lock()

            # Try to acquire the lock, but don't block if it's already locked
            if bot.user_locks[user_id].locked():
                try:
                    await client.chat_postMessage(
                        channel=channel_id,
                        text="I'm still processing your previous message. Please wait a moment before sending another one."
                    )
                    await remove_loading_reaction(client, channel_id, message_ts)
                except Exception as e:
                    logger.error(f"Error sending busy message: {e}")
                return

            logger.info(f"---Received DM from user {user_id} in channel {channel_id}: {text}")
            try:
                # Process the message with the lock acquired
                async with asyncio.timeout(200), bot.user_locks[user_id]:
                    # Create Slack context with the bot token
                    slack_context = SlackBotContext(
                        platform_name="slack",
                        user_id=user_id,
                        channel_id=channel_id,
                        thread_ts=thread_ts,
                        user_message=event,
                        bot_token=bot_token
                    )

                    verification_result = await bot.verify_user(slack_context)

                    if not verification_result["connected"]:
                        await remove_loading_reaction(client, channel_id, message_ts)
                        # Get user information to pass to login blocks
                        try:
                            user_info = await client.users_info(user=user_id)
                            if user_info["ok"]:
                                username = user_info["user"].get("real_name", user_id)
                            else:
                                username = user_id
                        except Exception as e:
                            logger.error(f"Error getting user info: {e}")
                            username = user_id

                        # Get team ID from context
                        team_id = context.get("team_id")

                        # Use create_login_blocks function to generate blocks with proper login URL
                        await client.chat_postMessage(
                            channel=channel_id,
                            thread_ts=thread_ts,
                            text="Please login to use the Klavis.ai bot",
                            blocks=create_login_blocks(username, user_id, team_id)
                        )
                        return

                    slack_context.mcp_client_id = verification_result["mcp_client_id"]
                    slack_context.llm_id = verification_result["llm_id"]

                    server_urls = await bot.get_server_urls(slack_context)
                    if not server_urls:
                        team_id = context.get("team_id")
                        mcp_client_id = await get_mcp_client_id_by_slack_info(team_id, user_id)

                        await client.chat_postMessage(
                            channel=channel_id,
                            thread_ts=thread_ts,
                            blocks=create_connect_mcp_server_blocks(
                                mcp_client_id or verification_result.get("mcp_client_id"))
                        )
                        # Don't return here to allow processing with 0 MCP server

                    # Process the message content
                    if text:
                        usage_under_limit = await bot.check_and_update_usage_limit(slack_context)
                        if not usage_under_limit:
                            await bot.send_message(
                                slack_context,
                                "You have reached your usage limit. Please upgrade your account to continue.",
                            )
                            await remove_loading_reaction(client, channel_id, message_ts)
                            return

                        try:
                            mcp_client = await bot.initialize_mcp_client(
                                context=slack_context, server_urls=server_urls
                            )
                            messages_history = await bot.get_messages_history(mcp_client.conversation, slack_context)

                            # Process the query and return the result from the streaming implementation
                            await bot.process_query_with_streaming(
                                mcp_client, messages_history, slack_context
                            )
                        except Exception as e:
                            logger.error(f"Error processing query: {e}", exc_info=True)
                            await bot.send_message(slack_context, f"Error processing query: {str(e)}")
                        finally:
                            await remove_loading_reaction(client, channel_id, message_ts)
                            logger.info(
                                f" --- Completed processing query from user {user_id} in channel {channel_id}: {text}")
                            await mcp_client.cleanup()
            except asyncio.TimeoutError:
                logger.warning(
                    f"Processing timed out for user {user_id} in channel {channel_id} after 200 seconds. Lock released.")
                try:
                    await client.chat_postMessage(
                        channel=channel_id,
                        text="The previous operation took too long and timed out. Please try again.",
                        thread_ts=thread_ts
                    )
                except Exception as e:
                    logger.error(f"Error sending timeout message: {e}")
            finally:
                # Ensure reaction is removed regardless of timeout or success/failure
                await remove_loading_reaction(client, channel_id, message_ts)
                # Lock is released automatically by async with when exiting the block or due to timeout/exception
