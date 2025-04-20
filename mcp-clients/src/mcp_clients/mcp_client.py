import asyncio
import base64
import logging
import os
import uuid
from contextlib import AsyncExitStack
from typing import Any, AsyncGenerator, Dict, List, Tuple, Optional
from urllib.parse import urlparse

import markitdown
import time
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.sse import sse_client

from mcp_clients.llms.anthropic import Anthropic
from mcp_clients.llms.base import Conversation, BaseLLM, LLMMessageFormat, ContentType, MessageRole, \
    ToolResultContent, ChatMessage
from mcp_clients.llms.openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_client")

SENSITIVE_PARAMS = [
    "auth_token", "token", "api_key", "secret", "password", "credential",
    "access_token", "refresh_token", "private_key", "authorization"
]


class MCPClient:
    """
    Generic MCP Client class that handles interactions with MCP servers.
    This class is platform-agnostic and can be used across different platforms.
    """

    def __init__(
            self,
            platform_name: str = None,
            api_name: str = None,
            provider: str = None,
            conversation: Conversation = None,
    ):
        """
        Initialize the MCP client.

        Args:
            platform_name: Optional name of the platform (e.g., "discord", "slack")
            api_name: Optional API name for the LLM model
            provider: Optional provider name for the LLM model (e.g., "anthropic", "openai")
            channel_id: Optional channel ID
            thread_id: Optional thread ID
        """
        # Dictionary of server_id -> session
        self.sessions: Dict[str, ClientSession] = {}
        # Maps server_id -> exit_stack for cleanup
        self.exit_stacks: Dict[str, AsyncExitStack] = {}
        # Maps server_id -> server_url/command for reference
        self.server_info: Dict[str, str] = {}
        # Cache of server_id -> list of tools
        self.tool_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.conversation = conversation
        # Initialize LLM client
        self.llm_client = self._initialize_llm_client(api_name, provider)

        # Set platform context if provided
        if platform_name:
            self.llm_client.set_platform(platform_name)

    def _initialize_llm_client(
            self, api_name: str = None, provider: str = None
    ) -> BaseLLM:
        """
        Initialize LLM client based on provided provider and set model based on api_name

        Args:
            api_name: API name to use as model identifier
            provider: Provider name ("anthropic" or "openai")

        Returns:
            BaseLLM: An initialized LLM client
        """

        # Determine which client to use based on provider
        if provider:
            if provider.lower() == "anthropic":
                logger.info("Initializing Anthropic client based on provider")
                return Anthropic(model=api_name)
            elif provider.lower() == "openai":
                logger.info("Initializing OpenAI client based on provider")
                return OpenAI(model=api_name)
            elif provider.lower() == "google":
                logger.info("Initializing Google client based on provider")
                return OpenAI(
                    api_key=os.getenv("GEMINI_API_KEY"),
                    model=api_name,
                    base_url=os.getenv("GEMINI_BASE_URL"),
                )
        else:
            # Default to Anthropic if no provider is specified
            logger.info("Defaulting to Anthropic client")
            return Anthropic(model=api_name)

    def _redact_sensitive_args(self, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive information like auth tokens from tool arguments.
        
        Args:
            tool_args: Dictionary of tool arguments
            
        Returns:
            Dictionary with sensitive values redacted
        """
        if not isinstance(tool_args, dict):
            return tool_args

        redacted_args = {}
        for key, value in tool_args.items():
            # Check if this parameter name matches any sensitive patterns
            is_sensitive = any(param in key.lower() for param in SENSITIVE_PARAMS)

            if is_sensitive and isinstance(value, str):
                # Redact the value, preserving first and last two characters if long enough
                if len(value) > 8:
                    redacted_args[key] = f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
                else:
                    redacted_args[key] = "********"
            elif isinstance(value, dict):
                # Recursively redact nested dictionaries
                redacted_args[key] = self._redact_sensitive_args(value)
            else:
                redacted_args[key] = value

        return redacted_args

    async def connect_to_server(
            self, url: str, args: list = None, env: Dict[str, str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Connect to an MCP server via URL

        Args:
            url: URL to connect to
            args: Command-line arguments (for stdio connection)
            env: Environment variables (for stdio connection)

        Returns:
            A tuple of (success/error message, server_id if successful or None)
        """
        if args is None:
            args = []

        # Generate a unique server ID
        server_id = str(uuid.uuid4())

        try:
            # Create new exit stack for this server
            exit_stack = AsyncExitStack()
            self.exit_stacks[server_id] = exit_stack

            if urlparse(url).scheme in ("http", "https"):
                # Use SSE client for HTTP(S) URLs
                streams = await exit_stack.enter_async_context(sse_client(url))
            else:
                # Use stdio client for commands
                server_parameters = StdioServerParameters(
                    command=url, args=args, env=env
                )
                streams = await exit_stack.enter_async_context(
                    stdio_client(server_parameters)
                )

            session = await exit_stack.enter_async_context(ClientSession(*streams))

            # Initialize the session
            logger.info(f"Initializing session for server {server_id}")
            await session.initialize()
            logger.info(f"Session initialized for server {server_id}")

            # Store the session and server info
            self.sessions[server_id] = session
            self.server_info[server_id] = url

            # Initialize tool cache for this server
            await self.refresh_tool_cache(server_id)

            return (
                f"Connected to MCP server successfully! Server ID: {server_id}",
                server_id,
            )

        except Exception as e:
            if server_id in self.exit_stacks:
                await self.exit_stacks[server_id].aclose()
                del self.exit_stacks[server_id]
            logger.exception(f"Error connecting to MCP server: {e}")
            return f"Error connecting to MCP server: {str(e)}", None

    async def refresh_tool_cache(self, server_id: str) -> List[Dict[str, Any]]:
        """
        Refresh the tool cache for a specific server

        Args:
            server_id: The ID of the server to refresh tools for

        Returns:
            List of tools provided by the server
        """
        if server_id not in self.sessions:
            logger.error(f"Cannot refresh tool cache: Server {server_id} not found")
            return []

        try:
            session = self.sessions[server_id]
            response = await session.list_tools()

            # Cache tools from this server
            server_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                    "server_id": server_id,  # Add server_id to track which server provides this tool
                }
                for tool in response.tools
            ]

            # Update the cache
            self.tool_cache[server_id] = server_tools

            logger.info(
                f"Updated cache with {len(server_tools)} tools from server {server_id}"
            )
            return server_tools
        except Exception as e:
            logger.error(
                f"Error refreshing tool cache for server {server_id}: {str(e)}"
            )
            return []

    async def get_tools_for_server(
            self, server_id: str, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get the current tools available from a specific server

        Args:
            server_id: The ID of the server to get tools for
            use_cache: Whether to use cached tools (if available)

        Returns:
            List of tools provided by the server
        """
        if server_id not in self.sessions:
            logger.error(f"Cannot get tools: Server {server_id} not found")
            return []

        # Check if we have a cached version and should use it
        if use_cache and server_id in self.tool_cache:
            logger.info(f"Using cached tools for server {server_id}")
            return self.tool_cache[server_id]

        # If no cache or cache refresh requested, query the server
        return await self.refresh_tool_cache(server_id)

    async def list_all_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from all connected servers by querying each server

        Returns:
            List of all available tools
        """
        all_tools = []

        # Query each server for its current tools
        for server_id in self.sessions.keys():
            server_tools = await self.get_tools_for_server(server_id)
            for tool in server_tools:
                if self.llm_client.get_message_format() == LLMMessageFormat.ANTHROPIC:
                    all_tools.append(
                        {
                            "name": tool["name"],
                            "description": tool["description"],
                            "input_schema": tool["input_schema"],
                        }
                    )
                elif self.llm_client.get_message_format() == LLMMessageFormat.OPENAI:
                    all_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool["name"],
                                "description": tool["description"],
                                "parameters": tool["input_schema"],
                            },
                        }
                    )

        return all_tools

    async def find_server_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Find which server provides a specific tool by using the cache

        Args:
            tool_name: The name of the tool to find

        Returns:
            Server ID if found, None otherwise
        """
        for server_id, tools in self.tool_cache.items():
            for tool in tools:
                if tool["name"] == tool_name:
                    return server_id

        # If not found in cache, check all servers
        for server_id in self.sessions.keys():
            if server_id not in self.tool_cache:
                tools = await self.get_tools_for_server(server_id)
                for tool in tools:
                    if tool["name"] == tool_name:
                        return server_id

        return None

    async def _process_tool_call(
            self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a tool call and return the result

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Yields:
            Progress updates and final tool result as strings
        """
        # Find which server provides this tool by querying all servers
        server_id = await self.find_server_for_tool(tool_name)
        if not server_id:
            error_msg = f"No server found for tool '{tool_name}'"
            logger.error(error_msg)
            yield f"\n[Error: {error_msg}]\n"
            return

        # Get the session for this server
        session = self.sessions.get(server_id)
        if not session:
            error_msg = f"No session found for server {server_id} (tool: {tool_name})"
            logger.error(error_msg)
            yield f"\n[Error: {error_msg}]\n"
            return

        try:
            message_split_token = self.llm_client.get_message_split_token()
            # Create a task for the actual tool call
            tool_call_task = asyncio.create_task(session.call_tool(tool_name, arguments))

            # Wait for the tool call to complete with progress updates every 30 seconds
            start_time = asyncio.get_event_loop().time()
            while not tool_call_task.done():
                # Wait for either 30 seconds to pass or the task to complete
                try:
                    result = await asyncio.wait_for(asyncio.shield(tool_call_task), timeout=30.0)
                    yield str(result)
                    return
                except asyncio.TimeoutError:
                    # Tool call is still running after 30 seconds
                    elapsed = int(asyncio.get_event_loop().time() - start_time)
                    logger.info(f"Tool call {tool_name} still running after {elapsed} seconds")
                    yield f"\n<special>[Tool {tool_name} still running... ({elapsed} seconds elapsed)]{message_split_token}\n"

            # If we reach here, the task completed
            yield str(await tool_call_task)
        except Exception as e:
            logger.error(
                f"Error calling tool {tool_name} on server {server_id}: {str(e)}",
                exc_info=True,
            )
            yield f"\n[Error calling tool {tool_name}: {str(e)}]\n"

    def is_final_response(self, messages: List[ChatMessage]) -> bool:
        """
        Check if the messages are final response by examining if it contains any tool calls
        """
        # Check if all messages are not tool calls
        return all(
            content.type != ContentType.TOOL_CALL
            for message in messages
            for content in message.content
        )

    async def process_query_stream(
            self,
            messages_history: List[ChatMessage],
            store_new_messages_callback: callable = None,
    ) -> AsyncGenerator[str, None]:
        """
        Process a query using Claude and available tools with streaming responses

        Args:
            messages_history: List of previous messages
            store_new_messages_callback: A callback function to store new messages
        Yields:
            Text chunks from the streaming response
        """

        # Create initial chat message
        chat_messages = messages_history
        messages_history_len = len(messages_history)

        # Get all available tools from all servers
        available_tools = await self.list_all_tools()
        logger.info(f"Found {len(available_tools)} available tools across all servers")
        resources = await self.list_all_resources()
        text_resource_contents = []
        for resource in resources:
            resource_content = await self.read_resource(resource["server_id"], resource["uri"])
            text_resource_contents.extend([content["text"] for content in resource_content if content["text"]])

        has_tool_call = True

        while has_tool_call:
            # Convert ChatMessages to provider-specific format
            provider_messages = self.llm_client.from_chat_messages(chat_messages)

            start_time = time.time()
            # Use the LLMClient to create the streaming generator
            async for chunk_text in self.llm_client.create_streaming_generator(
                    provider_messages, available_tools, text_resource_contents
            ):
                yield chunk_text
            logger.info(f"LLM took {time.time() - start_time} seconds to complete")
            # Get the last provider message (added by streaming generator)
            last_provider_message = provider_messages[-1]

            # Convert it to ChatMessage format
            last_chat_messages = self.llm_client.to_chat_messages(
                [last_provider_message]
            )

            # Add to our chat history
            chat_messages.extend(last_chat_messages)

            if self.is_final_response(last_chat_messages):
                has_tool_call = False
                break

            # Get the platform-specific message split token
            message_split_token = self.llm_client.get_message_split_token()

            # Process tool calls in the message
            tool_result_content = []

            for message in last_chat_messages:
                for content in message.content:
                    if content.type == ContentType.TOOL_CALL:
                        tool_name = content.name
                        tool_args = content.arguments

                        # Redact sensitive information from tool arguments before displaying
                        display_args = self._redact_sensitive_args(tool_args) if tool_args else None
                        yield f"\n<special>[Calling tool {tool_name} with arguments {str(display_args)[:100]}...]{message_split_token}\n"

                        # Process tool call with progress updates
                        result_text = ""
                        start_time = time.time()
                        async for update in self._process_tool_call(tool_name, tool_args):
                            if "[Tool" in update and "still running" in update:
                                # This is a progress update
                                yield update
                            else:
                                # This is the final result
                                result_text = update
                        logger.info(f"Tool {tool_name} took {time.time() - start_time} seconds to complete")
                        logger.info(f"Tool result: {result_text}")

                        # Add tool result to next user message
                        tool_result_content.append(
                            ToolResultContent(
                                tool_call_id=content.tool_id, result=result_text
                            )
                        )

            # Add user message with tool results
            if tool_result_content:
                chat_messages.append(
                    ChatMessage(role=MessageRole.TOOL, content=tool_result_content)
                )

        if store_new_messages_callback:
            start_time = time.time()
            await store_new_messages_callback(
                self.conversation.id, chat_messages[messages_history_len - 1:]
            )
            logger.info(f"Store new messages took {time.time() - start_time} seconds to complete")

        logger.info("Streaming query complete")

    async def cleanup(self):
        """Clean up resources for all servers"""
        for server_id in list(self.exit_stacks.keys()):
            try:
                await self.exit_stacks[server_id].aclose()
            except Exception as e:
                logger.error(
                    f"Error cleaning up resources for server {server_id}: {str(e)}"
                )

    def get_message_split_token(self) -> str:
        """
        Get the message split token from the LLM client

        Returns:
            Platform-specific message split token
        """
        return self.llm_client.get_message_split_token()

    async def list_all_resources(self) -> List[Dict[str, Any]]:
        """
        List all available resources from all connected servers

        Returns:
            List of resources provided by the server
        """
        resources = []
        try:
            for server_id in self.sessions.keys():
                session = self.sessions[server_id]
                response = await session.list_resources()

                # Handle direct resources
                if hasattr(response, "resources"):
                    resources.extend([
                        {
                            "uri": resource.uri,
                            "name": resource.name,
                            "description": resource.description if hasattr(resource, "description") else None,
                            "mimeType": resource.mimeType if hasattr(resource, "mimeType") else None,
                            "server_id": server_id,
                        }
                        for resource in response.resources
                    ])
                # TODO: Handle resource templates
            return resources
        except Exception as e:
            logger.error(f"Error listing resources from server {server_id}: {str(e)}")
            return []

    async def read_resource(self, server_id: str, uri: str) -> List[Dict[str, Any]]:
        """
        Read a specific resource by its URI from a server

        Args:
            server_id: The ID of the server to read the resource from
            uri: URI of the resource to read

        Returns:
            List of resource contents
        """
        if server_id not in self.sessions:
            logger.error(f"Cannot read resource: Server {server_id} not found")
            return []

        try:
            session = self.sessions[server_id]
            response = await session.read_resource(uri)

            # Process the resource contents
            contents = []

            for content in response.contents:
                content_data = {
                    "uri": content.uri,
                    "mimeType": content.mimeType if hasattr(content, "mimeType") else None,
                }

                # Handle text or binary content
                if hasattr(content, "text") and content.text is not None:
                    content_data["text"] = content.text
                elif hasattr(content, "blob") and content.blob is not None:
                    # Handle binary content
                    if content.mimeType and "application/pdf" in content.mimeType.lower():
                        # Convert base64 blob to bytes
                        pdf_bytes = base64.b64decode(content.blob)
                        # Use markitdown to convert PDF to markdown text
                        markdown_text = markitdown.markitdown(pdf_bytes)
                        content_data["text"] = markdown_text
                    else:
                        pass

                contents.append(content_data)

            logger.info(f"Successfully read resource {uri} from server {server_id}")
            return contents

        except Exception as e:
            logger.error(f"Error reading resource {uri} from server {server_id}: {str(e)}")
            return []
