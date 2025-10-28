import json
import logging
import uuid
from typing import Optional, Dict, Any, AsyncGenerator, List

from anthropic import AsyncAnthropic

from mcp_clients.llms.base import (
    BaseLLM,
    LLMMessageFormat,
    ChatMessage,
    MessageRole,
    TextContent,
    ToolCallContent,
    ToolResultContent,
    ContentType,
)

# Configure logging
logger = logging.getLogger("anthropic_client")


class Anthropic(BaseLLM):
    """
    Client for interacting with the Anthropic Claude API.
    Handles streaming responses and tool calls processing.
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize the LLM client"""
        super().__init__(message_format=LLMMessageFormat.ANTHROPIC)
        self.anthropic_client = AsyncAnthropic()
        self.model = model or "claude-3-5-sonnet-20241022"  # Default model
        self.max_tokens = self.config.max_tokens  # Default max tokens
        self._extracted_system_message = ""  # Store system messages extracted from chat history

    async def create_streaming_generator(
            self, messages: list, available_tools: list, resources: list = None
    ) -> AsyncGenerator[str, None]:
        """
        Create a streaming generator with the given messages and tools

        Args:
            messages: Message history
            available_tools: List of available tools
            resources: List of available resources
        Yields:
            Text chunks from the streaming response
        """
        logger.info(f"Creating streaming request to Claude with model: {self.model}")

        # Prepare request parameters
        system_message = ""

        # Add extracted system message from chat history
        if self._extracted_system_message:
            system_message = self._extracted_system_message
        elif hasattr(Anthropic, '_last_extracted_system_message') and Anthropic._last_extracted_system_message:
            # Use the system message extracted by from_chat_messages
            system_message = Anthropic._last_extracted_system_message
            # Store it in the instance for future use
            self._extracted_system_message = Anthropic._last_extracted_system_message

        # Add system message if operating in a specific platform context
        if self.platform and self.platform_config.get("system_message"):
            if system_message:
                system_message += "\n\n" + self.platform_config["system_message"]
            else:
                system_message = self.platform_config["system_message"]
        
        if resources:
            system_message += (
                    "\n\nThere are some resources that may be relevant to the conversation. You can use them to answer the user's question.\n\n"
                    + "\n\n".join(resources)
            )

        # Create request parameters
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
            "tools": available_tools,
            "stream": True,
        }

        # Add system message as a separate parameter if defined
        if system_message:
            request_params["system"] = system_message

        try:
            stream = await self.anthropic_client.messages.create(**request_params)

            # Process streaming response and handle tool calls
            message = {"role": "assistant", "content": []}
            current_text = ""
            current_tool_calls = {}  # Store tool calls by index

            # Get the message split token for the current platform
            message_split_token = self.get_message_split_token()

            async for chunk in stream:
                logger.debug(f"Received chunk: {chunk}")

                # Handle different event types
                if chunk.type == "message_start":
                    # Reset state for new message
                    current_text = ""
                    current_tool_calls = {}

                elif chunk.type == "content_block_start":
                    block = chunk.content_block
                    block_index = chunk.index

                    if block.type == "tool_use":
                        # Initialize tool call data structure
                        current_tool_calls[block_index] = {
                            "type": "tool_use",
                            "id": getattr(block, "id", None),
                            "name": block.name,
                            "input": getattr(block, "input", {}),
                            "partial_json": "",
                        }

                elif chunk.type == "content_block_delta":
                    delta = chunk.delta
                    block_index = chunk.index

                    if delta.type == "text_delta":
                        # Add text to current accumulation
                        current_text += delta.text
                        yield delta.text
                    elif (
                            delta.type == "input_json_delta"
                            and block_index in current_tool_calls
                    ):
                        # Accumulate JSON for tool input
                        current_tool_calls[block_index][
                            "partial_json"
                        ] += delta.partial_json

                elif chunk.type == "content_block_stop":
                    block_index = chunk.index
                    if current_text:
                        message["content"].append(
                            {"type": "text", "text": current_text}
                        )
                        current_text = ""
                        yield f"{message_split_token}\n"

                    # Process completed tool call if this was a tool_use block
                    if block_index in current_tool_calls:
                        tool_call = current_tool_calls[block_index]

                        # Try to parse accumulated JSON
                        if tool_call.get("partial_json"):
                            try:
                                # The partial_json might be complete JSON or fragments that need to be combined
                                parsed_json = json.loads(tool_call["partial_json"])
                                # Update the input with parsed JSON
                                tool_call["input"].update(parsed_json)
                                del tool_call["partial_json"]
                            except json.JSONDecodeError as e:
                                logger.warning(
                                    f"Failed to parse tool input JSON: {e}. Raw JSON: {tool_call.get('partial_json', '')}"
                                )

                        message["content"].append(tool_call)

                elif chunk.type == "message_delta":
                    # Handle message delta (contains stop_reason, etc.)
                    if hasattr(chunk, "delta") and hasattr(chunk.delta, "stop_reason"):
                        logger.info(
                            f"Message delta received with stop_reason: {chunk.delta.stop_reason}"
                        )

                elif chunk.type == "message_stop":
                    logger.info("Message complete")
                    # If there's any remaining text, yield it
                    if current_text:
                        yield current_text + "\n"

            messages.append(message)

        except Exception as e:
            logger.error(f"Error in streaming process: {str(e)}", exc_info=True)
            yield f"\n[Error in streaming process: {str(e)}]\n"

    async def non_streaming_response(
            self, messages: list, available_tools: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Get a non-streaming response from the LLM

        Args:
            messages: Message history
            available_tools: Optional list of available tools

        Returns:
            The complete message response
        """
        logger.info("Sending non-streaming request to Claude")

        # Prepare request parameters
        system_message = ""
        request_messages = (
            messages.copy()
        )  # Make a copy to avoid modifying the original

        # Add extracted system message from chat history
        if self._extracted_system_message:
            system_message = self._extracted_system_message
        elif hasattr(Anthropic, '_last_extracted_system_message') and Anthropic._last_extracted_system_message:
            # Use the system message extracted by from_chat_messages
            system_message = Anthropic._last_extracted_system_message
            # Store it in the instance for future use
            self._extracted_system_message = Anthropic._last_extracted_system_message

        # Add system message if operating in a specific platform context
        if self.platform and self.platform_config.get("system_message"):
            if system_message:
                system_message += "\n\n" + self.platform_config["system_message"]
            else:
                system_message = self.platform_config["system_message"]

        # Create request parameters
        kwargs = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": request_messages,
        }

        # Add system message as a separate parameter if defined
        if system_message:
            kwargs["system"] = system_message

        # Add tools if provided
        if available_tools:
            kwargs["tools"] = available_tools

        # Make the API call
        try:
            response = await self.anthropic_client.messages.create(**kwargs)
            return response
        except Exception as e:
            logger.error(f"Error in non-streaming request: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def to_chat_messages(raw_messages: List[Dict[str, Any]]) -> List[ChatMessage]:
        """
        Convert a list of Anthropic format messages to ChatMessage format

        Args:
            raw_messages: List of messages in Anthropic format

        Returns:
            List of ChatMessages
        """
        chat_messages = []

        for anthropic_message in raw_messages:
            # Map Anthropic role to our MessageRole
            # Note: Anthropic doesn't have "system" or "tool" in messages
            role_map = {
                "user": MessageRole.USER,
                "assistant": MessageRole.ASSISTANT,
            }

            role = role_map.get(anthropic_message.get("role", "user"), MessageRole.USER)
            content_list = []

            # Handle content based on structure
            anthropic_content = anthropic_message.get("content", [])

            # If content is a string (text-only message)
            if isinstance(anthropic_content, str):
                content_list.append(TextContent(text=anthropic_content))

            # If content is a list (can contain text, tool_use, and tool_result)
            elif isinstance(anthropic_content, list):
                for content_item in anthropic_content:
                    # Handle text content
                    if isinstance(content_item, str):
                        content_list.append(TextContent(text=content_item))

                    # Handle object content types
                    elif isinstance(content_item, dict):
                        content_type = content_item.get("type")

                        # Handle tool use (function call)
                        if content_type == "tool_use":
                            content_list.append(
                                ToolCallContent(
                                    tool_id=content_item.get("id", str(uuid.uuid4())),
                                    name=content_item.get("name", ""),
                                    arguments=content_item.get("input", {}),
                                )
                            )

                        # Handle tool result
                        elif content_type == "tool_result":
                            content_list.append(
                                ToolResultContent(
                                    tool_call_id=content_item.get("tool_use_id", ""),
                                    result=content_item.get("content", ""),
                                )
                            )

                        # Handle plain text content in object format
                        elif content_type == "text":
                            content_list.append(
                                TextContent(text=content_item.get("text", ""))
                            )

            chat_messages.append(
                ChatMessage(
                    role=role,
                    content=content_list,
                    id=anthropic_message.get("id", str(uuid.uuid4())),
                )
            )

        return chat_messages

    @staticmethod
    def from_chat_messages(chat_messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """
        Convert a list of ChatMessages to Anthropic format

        Args:
            chat_messages: List of ChatMessages to convert

        Returns:
            List of messages in Anthropic format
        """
        anthropic_messages = []
        
        # Extract and combine system messages
        system_message_parts = []
        non_system_messages = []
        
        for chat_message in chat_messages:
            if chat_message.role == MessageRole.SYSTEM:
                # Extract text content from system messages
                for content in chat_message.content:
                    if content.type == ContentType.TEXT and content.text:
                        system_message_parts.append(content.text)
            else:
                # Keep non-system messages for processing
                non_system_messages.append(chat_message)
        
        # Store the combined system message in a class variable that can be accessed by instance methods
        # Note: Using a simple approach since this is a static method
        combined_system_message = "\n\n".join(system_message_parts) if system_message_parts else ""
        
        # Store in a module-level variable that instances can access
        # This is a temporary solution since we can't modify the method signature
        if hasattr(Anthropic, '_last_extracted_system_message'):
            Anthropic._last_extracted_system_message = combined_system_message
        else:
            setattr(Anthropic, '_last_extracted_system_message', combined_system_message)

        # Process non-system messages
        for chat_message in non_system_messages:
            # Map MessageRole to Anthropic role
            # Note: Anthropic doesn't support system or tool as message roles
            role_map = {
                MessageRole.USER: "user",
                MessageRole.ASSISTANT: "assistant",
                MessageRole.TOOL: "user",  # Map tool to user with special handling
            }

            anthropic_message = {
                "role": role_map.get(chat_message.role, "user"),
                "content": [],
            }

            for content in chat_message.content:
                if content.type == ContentType.TEXT and content.text:
                    anthropic_message["content"].append(
                        {"type": "text", "text": content.text}
                    )
                if content.type == ContentType.TOOL_CALL and content.name:
                    anthropic_message["content"].append(
                        {
                            "type": "tool_use",
                            "id": content.tool_id,
                            "name": content.name,
                            "input": content.arguments,
                        }
                    )
                if content.type == ContentType.TOOL_RESULT and content.result:
                    anthropic_message["content"].append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content.tool_call_id,
                            "content": content.result,
                        }
                    )
                if content.type == ContentType.FILE:
                    text = f'\nUser uploaded a file as attachment. The url is "{content.url}".'
                    if content.auth_token:
                        text += f'The auth token is "{content.auth_token}".'
                    anthropic_message["content"].append(
                        {
                            "type": "text",
                            "text": text,
                        }
                    )

            anthropic_messages.append(anthropic_message)

        return anthropic_messages
