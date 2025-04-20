import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

import time

from mcp_clients.config import USE_PRODUCTION_DB
# Define empty result structures for when database is not used
from mcp_clients.llms.base import Conversation, ChatMessage
from mcp_clients.mcp_client import MCPClient

if USE_PRODUCTION_DB:
    from mcp_clients.database import database

logger = logging.getLogger("base_bot")


class BotContext(ABC):
    """
    Base context class for chat platform operations.
    Contains context information needed for responses.
    """

    def __init__(
            self,
            platform_name: str,
            user_id: str,
            mcp_client_id: str = None,
            llm_id: str = None,
            user_message: Any = None,
    ):
        """
        Initialize the bot context.

        Args:
            platform_name: Name of the platform (e.g., 'discord', 'slack')
            user_id: The user ID on the platform
            user_message: Platform-specific user message
        """
        self.platform_name = platform_name
        self.user_id = user_id
        self.user_message = user_message
        self.mcp_client_id = mcp_client_id
        self.llm_id = llm_id

    @abstractmethod
    def get_channel_id(self) -> Optional[str]:
        """
        Get the channel ID for the current context.
        Must be implemented by platform-specific subclasses.
        
        Returns:
            String representation of the channel ID, or None if not applicable
        """
        pass

    @abstractmethod
    def get_thread_id(self) -> Optional[str]:
        """
        Get the thread ID for the current context, if applicable.
        Must be implemented by platform-specific subclasses.
        
        Returns:
            String representation of the thread ID, or None if not applicable
        """
        pass


class BaseBot(ABC):
    """
    Base class for platform-specific bots.
    Handles common functionality across different platforms.
    """

    def __init__(self, platform_name: str):
        """
        Initialize the base bot.

        Args:
            platform_name: Name of the platform (e.g., 'discord', 'slack')
        """
        self.platform_name = platform_name
        logger.info(f"Initializing {platform_name} bot")

    @abstractmethod
    async def send_message(self, context: BotContext, message: str) -> Any:
        """
        Send a message on the platform.

        Args:
            context: Bot context containing channel info
            message: Message text to send

        Returns:
            Platform-specific response object
        """
        pass

    async def verify_user(self, context: BotContext) -> Dict[str, Any]:
        """
        Verify the user.
        """
        start_time = time.time()

        if USE_PRODUCTION_DB:
            verification_result = await database.get_user_connection_information(
                context.platform_name, context.user_id
            )
            logger.info(f"Verify user took {time.time() - start_time} seconds to complete")

            if verification_result["error"]:
                await self.send_message(
                    context, f"Error verifying user: {verification_result['error']}"
                )
        else:
            # Skip database operation, return dummy result
            verification_result = {
                "connected": True,
                "mcp_client_id": None,
                "llm_id": None,
                "error": None
            }
            logger.info("Database operations skipped: verify_user")

        return verification_result

    async def check_and_update_usage_limit(self, context: BotContext) -> bool:
        """
        Check if the user has reached the usage limit and update it if so.
        """
        start_time = time.time()

        if USE_PRODUCTION_DB:
            result = await database.check_and_update_usage_limit(context.mcp_client_id)
            logger.info(f"Check and update usage limit took {time.time() - start_time} seconds to complete")
            if result["error"]:
                await self.send_message(
                    context, f"Error checking and updating usage limit: {result['error']}"
                )
                return False
            return result["success"]
        else:
            # Skip database operation, return dummy result
            logger.info("Database operations skipped: check_and_update_usage_limit")
            return True

    async def get_server_urls(self, context: BotContext) -> List[str]:
        """
        Get the server URLs for the user.
        """
        start_time = time.time()

        if USE_PRODUCTION_DB:
            mcp_servers = await database.get_connected_mcp_servers(
                context.mcp_client_id
            )
            logger.info(f"Get server urls took {time.time() - start_time} seconds to complete")
            if mcp_servers["error"]:
                await self.send_message(
                    context, f"Error getting connected servers: {mcp_servers['error']}"
                )
                return []

            server_urls = []

            for server in mcp_servers["servers"]:
                if server["instance_id"]:
                    server_urls.append(
                        f"{server['server_url']}/sse?instance_id={server['instance_id']}"
                    )
                else:
                    server_urls.append(server["external_mcp_server_link"])

            return server_urls
        else:
            # Read server URLs from JSON file
            json_path = os.path.join(os.path.dirname(__file__), 'local_mcp_servers.json')
            with open(json_path, 'r') as f:
                data = json.load(f)
            logger.info("Reading server URLs from local_mcp_servers.json")
            return data.get("server_urls", [])

    async def initialize_mcp_client(
            self, context: BotContext, server_urls: List[str] = None
    ) -> Any:
        """
        Initialize an MCP client for the user.

        Args:
            context: Bot context for the interaction
            server_urls: Optional list of MCP server URLs to connect to

        Returns:
            Platform-specific response object
        """

        # Get api_name and provider from database
        if USE_PRODUCTION_DB:
            llm_info = await database.get_llm_api_name(context.llm_id)
            logger.info(f"LLM info: {llm_info}")
        else:
            # Skip database operation
            llm_info = ("gpt-4o", "openai")
            logger.info("Database operations skipped: get_llm_api_name")

        api_name = None
        provider = None

        if llm_info:
            if isinstance(llm_info, tuple) and len(llm_info) == 2:
                api_name, provider = llm_info
            else:
                # For backward compatibility if only api_name is returned
                api_name = llm_info

        if USE_PRODUCTION_DB:
            conversation_result = await database.find_or_create_conversation(
                conversation_id=context.conversation_id if hasattr(context, "conversation_id") else None,
                channel_id=context.get_channel_id(),
                mcp_client_id=context.mcp_client_id,
                thread_id=context.get_thread_id(),
            )

            if conversation_result["error"]:
                await self.send_message(
                    context, f"Error creating conversation: {conversation_result['error']}"
                )
                return
        else:
            # Skip database operation, use dummy values
            conversation_result = {
                "error": None,
                "conversation": Conversation(
                    id="dummy_conversation_id",
                    messages=[],
                    channel_id=context.get_channel_id(),
                    thread_id=context.get_thread_id(),
                )
            }
            logger.info("Database operations skipped: find_or_create_conversation")

        # Create a new MCP client for this query
        mcp_client = MCPClient(
            self.platform_name, api_name, provider, conversation_result["conversation"]
        )

        # Connect to each server
        for server_url in server_urls:
            await mcp_client.connect_to_server(server_url)

        return mcp_client

    async def store_new_messages(
            self, conversation_id: str, messages: List[ChatMessage]
    ) -> None:
        """
        Store new messages in the conversation.
        """
        if USE_PRODUCTION_DB:
            return await database.add_messages(conversation_id, messages)
        else:
            # Skip database operation
            logger.info(f"Database operations skipped: store_new_messages for {len(messages)} messages")
            return None

    @abstractmethod
    async def process_query_with_streaming(
            self, mcp_client: MCPClient, messages_history: List[ChatMessage], context: BotContext
    ) -> Any:
        """
        Process a query with streaming in a platform-specific way.

        Args:
            mcp_client: MCP client instance
            messages_history: List of previous messages
            context: Bot context for the interaction

        Returns:
            Platform-specific response object
        """
        pass

    @abstractmethod
    async def run(self):
        """
        Run the bot.
        """
        pass

    @abstractmethod
    async def get_messages_history(self, conversation: Conversation, context: BotContext, limit: int = 6) -> List[
        ChatMessage]:
        """
        Get the messages history.
        """
        pass
