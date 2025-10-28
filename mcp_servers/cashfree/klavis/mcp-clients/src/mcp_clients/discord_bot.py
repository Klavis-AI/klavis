import asyncio
import logging
import os
from typing import Any, List, Optional
from urllib.parse import quote

import discord
from discord import Embed, Color, DMChannel, Thread
from discord.ext import commands
from discord.ui import View
from dotenv import load_dotenv

from mcp_clients.base_bot import BaseBot, BotContext
from mcp_clients.config import USE_PRODUCTION_DB
from mcp_clients.llms.base import ChatMessage, MessageRole, TextContent, FileContent, Conversation
from mcp_clients.mcp_client import MCPClient

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("discord_bot")

# Define long-running tools
LONG_RUNNING_TOOLS = [
    "generate_web_reports",
    "firecrawl_deep_research",
]

# Get environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEBSITE_URL = os.getenv("WEBSITE_URL")

# Check if required environment variables are set
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set")


class DiscordBotContext(BotContext):
    """
    Discord-specific context for the bot operations.
    Extends the base BotContext with Discord-specific attributes.
    """

    def __init__(
            self,
            platform_name: str,
            user_id: str,
            is_dm: bool,
            channel,
            user_message,
            thread,
    ):
        """
        Initialize the Discord bot context.

        Args:
            platform_name: Name of the platform ('discord')
            user_id: Discord user ID
            channel: Discord channel object
            user_message: Optional user message object
            is_dm: Whether the message is in a DM channel
            thread: Optional thread object
        """
        super().__init__(
            platform_name=platform_name, user_id=user_id, user_message=user_message
        )
        self.channel = channel
        self.is_dm = is_dm
        self.thread = thread

    def get_channel_id(self) -> Optional[str]:
        """
        Get the Discord channel ID for the current context.

        Returns:
            String representation of the channel ID, or None if not applicable
        """
        if self.channel:
            return str(self.channel.id)
        return None

    def get_thread_id(self) -> Optional[str]:
        """
        Get the thread ID for the current context, if applicable.

        Returns:
            String representation of the thread ID, or None if not applicable
        """
        if (
                self.user_message
                and hasattr(self.user_message, "thread")
                and self.user_message.thread
        ):
            return str(self.user_message.thread.id)
        return None


class DiscordBot(BaseBot):
    """
    Discord-specific implementation of the bot.
    Extends the base bot with Discord-specific functionality.
    """

    def __init__(self):
        """
        Initialize the Discord bot.
        """
        super().__init__(platform_name="discord")

        # Initialize Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True  # Enable members intent to receive member join events
        self.client = commands.Bot(command_prefix="!", intents=intents)

        # Add user lock to prevent concurrent message processing
        self.user_locks = {}

        # Register event handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        self.client.event(self.on_member_join)

        # Set up slash commands
        self._setup_commands()

    async def on_ready(self):
        """Event handler when bot is ready"""
        logger.info(f"Logged in as {self.client.user.name} ({self.client.user.id})")

        # Sync commands with Discord
        try:
            synced = await self.client.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_message(self, message):
        """Handle message events - respond when bot is @mentioned or in DMs"""
        # Don't respond to own messages
        if message.author == self.client.user:
            return

        # Check if the message is in a DM channel
        is_dm = isinstance(message.channel, DMChannel) or not message.guild
        thread = None

        if not is_dm and not f"<@{self.client.user.id}>" in message.content:
            return

        if not is_dm:
            # Check if the message is in a thread
            if isinstance(message.channel, Thread):
                thread = message.channel
            else:
                thread = await message.create_thread(
                    name=message.content[:60].replace(f"<@{self.client.user.id}>", "")
                )
        user_id = str(message.author.id)
        context = DiscordBotContext(
            platform_name="discord",
            user_id=user_id,
            channel=message.channel,
            user_message=message,
            is_dm=is_dm,
            thread=thread,
        )

        if user_id not in self.user_locks:
            self.user_locks[user_id] = asyncio.Lock()

        # Try to acquire the lock, but don't block if it's already locked
        if self.user_locks[user_id].locked():
            await self.send_message(
                context,
                "I'm still processing your previous message. Please wait a moment before sending another one.",
            )
            return

        # Process the message with the lock acquired
        try:
            # Add timeout for the processing block while lock is held
            async with asyncio.timeout(200), self.user_locks[user_id]:
                verification_result = await self.verify_user(context)

                if not verification_result["connected"]:
                    if not is_dm:
                        # Send message in the current context
                        await self.send_message(
                            context,
                            f"You need to link your {context.platform_name} account with our website to use the AI assistant features. I have sent you a Direct Message to link your account.",
                        )

                    try:
                        await message.author.send(
                            f"You need to link your {context.platform_name} account with our website to use the AI assistant features using the login button below.",
                            view=self.create_login_view(message.author.name, user_id),
                        )
                    except discord.Forbidden:
                        await self.send_message(
                            context,
                            f"Your DMs are disabled. Use the login button below to link your account.",
                            view=self.create_login_view(message.author.name, user_id),
                        )
                    except Exception as e:
                        logger.error(f"Error sending DM: {e}", exc_info=True)

                    return

                context.mcp_client_id = verification_result["mcp_client_id"]
                context.llm_id = verification_result["llm_id"]

                server_urls = await self.get_server_urls(context)

                if not server_urls:
                    await self.send_message(
                        context,
                        "Not connected to any MCP server. Features are limited.",
                        view=self.create_config_view(),
                    )
                    # Don't return here to allow processing with 0 MCP server

                usage_under_limit = await self.check_and_update_usage_limit(context)
                if not usage_under_limit:
                    await self.send_message(
                        context,
                        "You have reached your usage limit. Please upgrade your account to continue.",
                    )
                    return

                mcp_client = await self.initialize_mcp_client(
                    context=context, server_urls=server_urls
                )
                messages_history = await self.get_messages_history(
                    conversation=mcp_client.conversation,
                    context=context,
                )

            try:
                # Process the query and return the result from the streaming implementation
                await self.process_query_with_streaming(
                    mcp_client, messages_history, context
                )
            except Exception as e:
                logger.error(f"Error processing query: {e}", exc_info=True)
                await self.send_message(context, f"Error processing query: {str(e)}")
            finally:
                await mcp_client.cleanup()
        except asyncio.TimeoutError:
            logger.warning(f"Processing timed out for user {user_id} after 200 seconds. Lock released.")
            # Ensure the lock is released if timeout occurs (async with handles this)
            # Inform the user about the timeout
            await self.send_message(
                context,
                "The previous operation took too long and timed out. Please try again.",
            )

    async def on_member_join(self, member):
        """Event handler when a new member joins the server"""
        logger.info(f"New member joined: {member.name} ({member.id})")

        try:
            # Create the welcome embed
            welcome_embed = self.create_welcome_embed(self.client.user)

            # Create view with user information
            welcome_view = self.create_login_view(member.name, str(member.id))

            # Send DM to the new member
            await member.send(embed=welcome_embed, view=welcome_view)
            logger.info(f"Sent welcome DM to new member: {member.name} ({member.id})")
        except discord.Forbidden:
            logger.warning(
                f"Could not send DM to {member.name} - user may have DMs disabled"
            )
        except Exception as e:
            logger.error(f"Error sending welcome DM: {e}", exc_info=True)

    def _setup_commands(self):
        """Set up slash commands for the bot"""

        @self.client.tree.command(
            name="welcome", description="Display the welcome message with buttons"
        )
        async def slash_welcome(interaction: discord.Interaction):
            """Show the welcome message with buttons"""
            # Get the user from the interaction
            user = interaction.user

            # Create the welcome embed and view with user information
            welcome_embed = self.create_welcome_embed(self.client.user)
            view = self.create_login_view(user.name, str(user.id))

            # Send the welcome message as the interaction response
            await interaction.response.send_message(embed=welcome_embed, view=view)

    async def send_message(
            self,
            context: DiscordBotContext,
            message: str,
            view=None,
            embed=None,
    ) -> Any:
        """
        Send a message on Discord.

        Args:
            context: Discord bot context containing channel info
            message: Message text to send
            view: Discord view to send with the message
            embed: Discord embed to send with the message

        Returns:
            Discord message object
        """
        if context.thread:
            return await context.thread.send(message, view=view, embed=embed)
        else:
            return await context.channel.send(message, view=view, embed=embed)

    async def process_query_with_streaming(
            self,
            mcp_client: MCPClient,
            messages_history: List[ChatMessage],
            context: DiscordBotContext,
    ) -> Any:
        """
        Process a query with streaming in Discord-specific way.

        Args:
            mcp_client: MCP client instance
            messages_history: List of previous messages
            context: Discord bot context for the interaction

        Returns:
            Final message object or None
        """
        MESSAGE_SPLIT_TOKEN = mcp_client.get_message_split_token()

        try:
            buffer = ""
            async with (
                context.thread.typing() if context.thread else context.channel.typing(),
                asyncio.timeout(200.0),
            ):
                async for chunk in mcp_client.process_query_stream(
                        messages_history,
                        self.store_new_messages if USE_PRODUCTION_DB else None,
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

                                    if special_content.startswith("[Calling tool"):
                                        # Use the helper method to create the embed
                                        embed = self.create_tool_call_embed(
                                            special_content, title="📲 Tool Call"
                                        )
                                        await self.send_message(
                                            context, "", embed=embed
                                        )
                                    elif "still running" in special_content:
                                        # Create an embed for tool running status
                                        embed = Embed(
                                            title="⏳ Tool Running",
                                            description=special_content.strip("[]"),
                                            color=Color.gold(),
                                        )
                                        await self.send_message(
                                            context, "", embed=embed
                                        )
                                else:
                                    # Regular message
                                    await self.send_message(context, part)
                                # Short delay to make messages feel natural
                                await asyncio.sleep(0.5)

                        buffer = parts[-1]
                # Send any remaining content
                if buffer.strip():
                    # Check if the remaining buffer contains a special message
                    if "<special>" in buffer:
                        special_content = buffer.split("<special>")[1].strip()
                        if special_content.startswith("[Calling tool"):
                            # Use the helper method to create the embed
                            embed = self.create_tool_call_embed(
                                special_content, title="📲 Tool Call"
                            )
                            return await self.send_message(context, "", embed=embed)
                        elif "still running" in special_content:
                            embed = Embed(
                                title="⏳ Tool Running",
                                description=special_content.strip("[]"),
                                color=Color.gold(),
                            )
                            return await self.send_message(context, "", embed=embed)
                    return await self.send_message(context, buffer)
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return await self.send_message(context, f"Error processing query: {str(e)}")

    def create_login_view(
            self,
            platform_username: str,
            platform_user_id: str,
    ) -> View:
        """
        Create a login config view with buttons

        Args:
            platform_username: Discord username to pass in URL
            platform_user_id: Discord user ID to pass in URL

        Returns:
            A Discord UI View object with buttons
        """
        view = View(timeout=None)  # Buttons persist indefinitely

        # Construct login URL with query parameters
        login_url = f"{WEBSITE_URL}/auth/sign-in"

        # URL encode the parameters
        encoded_username = quote(platform_username)
        login_url = f"{login_url}?platform=discord&external_user_id={platform_user_id}&external_username={encoded_username}"

        # Add URL buttons
        login_button = discord.ui.Button(
            style=discord.ButtonStyle.primary, label="Login", emoji="🔐", url=login_url
        )
        view.add_item(login_button)

        return view

    def create_config_view(self) -> View:
        """
        Create a config view with buttons

        Args:
            platform_username: Discord username to pass in URL
            platform_user_id: Discord user ID to pass in URL

        Returns:
            A Discord UI View object with buttons
        """
        view = View(timeout=None)  # Buttons persist indefinitely

        configure_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Configure",
            emoji="⚙️",
            url=f"{WEBSITE_URL}/home",
        )
        view.add_item(configure_button)

        return view

    def create_welcome_embed(self, bot_user) -> Embed:
        """
        Create a welcome embed for new servers

        Args:
            bot_user: Discord bot user object

        Returns:
            A Discord Embed object
        """
        welcome_embed = Embed(
            title="Welcome to Klavis AI Discord MCP Client",
            description="I can help you with various tasks by connecting to multiple MCP servers.",
            color=Color.blue(),
            timestamp=discord.utils.utcnow(),  # Add current timestamp to the embed
        )

        # Add a bot avatar or logo as thumbnail
        welcome_embed.set_thumbnail(url=bot_user.display_avatar.url)

        # Add server info section
        welcome_embed.add_field(
            name="⚡ Quick Start",
            value="Click the **Login** button below to get started. You can connect to multiple servers and use tools from all of them! Once connected, simply mention the bot with your query.",
            inline=False,
        )

        # Add feature highlights with emojis
        welcome_embed.add_field(
            name="🔍 AI Assistance",
            value="@mention the bot with your message or DM me privately to ask questions or get help with tasks. The bot will use tools from all connected servers.",
            inline=True,
        )

        welcome_embed.add_field(
            name="🌐 Multi-Server Support",
            value="Connect to multiple internal and external MCP servers on our website.",
            inline=False,
        )

        # Add a footer with version information
        welcome_embed.set_footer(
            text=f"MCP Discord Client v1.0 | {bot_user.name}",
            icon_url=bot_user.display_avatar.url,
        )

        return welcome_embed

    async def send_welcome_message(self, channel, user):
        """Send a rich welcome message with buttons to the specified channel

        Args:
            channel: Discord channel to send the message to
            user: Discord user object
        """
        logger.info(f"Sending welcome message to channel {channel.id}")

        # Create a rich embed for the welcome card
        welcome_embed = self.create_welcome_embed(self.client.user)

        # Create a custom view with buttons, passing user info
        view = self.create_login_view(user.name, str(user.id))

        # Send the welcome message
        await channel.send(embed=welcome_embed, view=view)

    async def get_messages_history(
            self, conversation: Conversation, context: BotContext, limit: int = 6
    ) -> List[ChatMessage]:
        """
        Get the previous messages for the conversation.

        Args:
            context: Discord bot context containing channel info
            limit: Maximum number of previous messages to retrieve (not including the current message)

        Returns:
            List of ChatMessage objects representing previous messages
        """
        discord_context = context
        chat_messages = []

        try:
            # Fetch last 'limit' messages from the Discord channel
            async for message in discord_context.channel.history(limit=limit + 1):
                content = []
                if message.author.id == self.client.user.id:
                    role = MessageRole.ASSISTANT
                    content.append(TextContent(text=message.content))
                else:
                    role = MessageRole.USER
                    username = message.author.display_name
                    content.append(
                        TextContent(text=f"User {username} says: {message.content}")
                    )
                    for attachment in message.attachments:
                        content.append(
                            FileContent(
                                url=attachment.url,
                                filename=attachment.filename,
                                extension=attachment.filename.split(".")[-1],
                            )
                        )

                # Create a ChatMessage object
                chat_message = ChatMessage(
                    role=role,
                    content=content,
                )

                chat_messages.append(chat_message)

            # Reverse the list to get messages in chronological order
            chat_messages.reverse()

        except Exception as e:
            logger.error(f"Error retrieving previous messages: {e}", exc_info=True)
            # Return empty list in case of error
            return []

        return chat_messages

    def create_tool_call_embed(
            self, special_content: str, title: str = "📲 MCP Server Call"
    ) -> Embed:
        """
        Create an embed for tool calls with special handling for long-running tools.

        Args:
            special_content: The special content string with tool information
            title: The title to use for the embed

        Returns:
            Discord Embed object with appropriate tool information
        """
        tool_name = ""
        try:
            content = special_content.strip("[]")
            tool_parts = content.split("with arguments")
            tool_name = tool_parts[0].replace("Calling tool", "").strip()
        except:
            pass

        description = special_content.strip("[]")

        footer_text = "Working on your request..."
        # Add footer note for long-running tools
        if any(tool in tool_name for tool in LONG_RUNNING_TOOLS):
            footer_text = "This tool may take several minutes to complete..."

        embed = Embed(title=title, description=description, color=Color.blue())
        embed.set_footer(text=footer_text)

        return embed

    def run(self):
        """Run the Discord bot"""
        print(DISCORD_TOKEN)
        self.client.run(DISCORD_TOKEN)


def main():
    """Run the Discord bot"""
    # Create and run the bot
    bot = DiscordBot()
    bot.run()


if __name__ == "__main__":
    main()
