import logging
import uuid
from typing import Optional, Dict, Any, AsyncGenerator, List

import time
from openai import AsyncOpenAI

from mcp_clients.llms.base import (
    BaseLLM,
    ChatMessage,
    MessageRole,
    TextContent,
    ToolCallContent,
    ToolResultContent,
    ContentType,
)

# Configure logging
logger = logging.getLogger("openai_client")


class OpenAI(BaseLLM):
    """
    Client for interacting with the OpenAI API.
    Handles streaming responses and tool calls processing.
    """

    def __init__(
            self,
            api_key: Optional[str] = None,
            model: Optional[str] = None,
            base_url: Optional[str] = None,
    ):
        """
        Initialize the OpenAI client

        Args:
            api_key: Optional configuration for OpenAI
            model: Optional model of GenAI
            base_url: Optional url to connect to given api_key GenAI
        """
        super().__init__()
        self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model or "gpt-4o-mini"
        self.max_tokens = self.config.max_tokens

    async def create_streaming_generator(
            self, messages: list, available_tools: list, resources: list = None
    ) -> AsyncGenerator[str, None]:
        """
        Create an OpenAI streaming generator with the given messages and tools.

        Args:
            messages: Message history (mutable, will be updated with assistant response).
            available_tools: List of available tools in OpenAI format.
            resources: List of resources to be used in the conversation.
        Yields:
            Text chunks from the streaming response.
        """
        logger.info("Creating OpenAI streaming request")

        # Prepare request parameters for OpenAI
        request_params = {
            "model": self.model,  # Ensure this is an OpenAI model name (e.g., "gpt-4o")
            "max_tokens": self.max_tokens,
            "messages": messages,
            "stream": True,
        }

        system_message_content = self.platform_config.get("system_message")
        if resources:
            system_message_content += "\n\nThere are some resources that may be relevant to the conversation. You can use them to answer the user's question.\n\n" + "\n\n".join(
                resources)
        if system_message_content and not messages[0].get("role") == "system":
            request_params["messages"].insert(
                0, {"role": "system", "content": system_message_content}
            )

        # Add tools if provided (OpenAI format expects 'tools' and 'tool_choice' potentially)
        if available_tools:
            request_params["tools"] = available_tools
            # request_params["tool_choice"] = "auto"

        try:
            start_time = time.time()
            stream = await self.openai_client.chat.completions.create(**request_params)
            logger.info(f"OpenAI stream creation took {time.time() - start_time} seconds to complete")

            full_response_content = ""
            # Use dict to accumulate tool calls by index, storing the full tool call object structure
            accumulated_tool_calls = {}

            start_time = time.time()
            async for chunk in stream:
                if not chunk.choices:  # Handle potential empty chunks
                    continue

                delta = chunk.choices[0].delta

                # --- Handle Text Content ---
                if delta and delta.content:
                    text_chunk = delta.content
                    full_response_content += text_chunk
                    yield text_chunk  # Yield text chunks as they arrive

                # --- Handle Tool Calls ---
                if delta and delta.tool_calls:
                    for tool_call_chunk in delta.tool_calls:
                        index = tool_call_chunk.index

                        if index is None:
                            # The index might be None for Gemini. In this case, it will return the complete tool call object.
                            tool_call_id = tool_call_chunk.id or str(uuid.uuid4())
                            accumulated_tool_calls[tool_call_id] = {
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tool_call_chunk.function.name,
                                    "arguments": tool_call_chunk.function.arguments,
                                },
                            }
                            continue

                        # Initialize tool call structure if it's the first chunk for this index
                        if index not in accumulated_tool_calls:
                            # Store the initial structure, ensure function name/id are captured
                            accumulated_tool_calls[index] = {
                                "id": tool_call_chunk.id or str(uuid.uuid4()),
                                "type": "function",
                                "function": {
                                    "name": tool_call_chunk.function.name,
                                    "arguments": "",
                                },
                            }
                        # Accumulate arguments string
                        if (
                                tool_call_chunk.function
                                and tool_call_chunk.function.arguments
                        ):
                            accumulated_tool_calls[index]["function"][
                                "arguments"
                            ] += tool_call_chunk.function.arguments
            logger.info(f"OpenAI for chunk took {time.time() - start_time} seconds to complete")

            # --- Construct and Append Assistant Message ---
            assistant_message = {"role": "assistant"}  # Initialize

            # Add accumulated text content if any
            if full_response_content:
                assistant_message["content"] = full_response_content

            # Add accumulated tool calls if any
            if accumulated_tool_calls:
                # Convert the accumulated dict to the list format expected in messages
                final_tool_calls = [tc for tc in accumulated_tool_calls.values()]
                assistant_message["tool_calls"] = final_tool_calls
                logger.info(f"Accumulated {len(final_tool_calls)} tool calls.")

            # Append the complete assistant message to the original history
            # Only append if there's content or tool calls to avoid empty messages
            if assistant_message.get("content") or assistant_message.get("tool_calls"):
                messages.append(assistant_message)
            else:
                logger.warning(
                    "OpenAI stream finished without generating content or tool calls."
                )

        except Exception as e:
            logger.error(f"Error in OpenAI streaming process: {str(e)}", exc_info=True)
            yield f"\n[Error in OpenAI streaming process: {str(e)}]\n"

    async def non_streaming_response(
            self, messages: list, available_tools: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Get a non-streaming response from OpenAI LLM.

        Args:
            messages: Message history.
            available_tools: Optional list of available tools in OpenAI format.

        Returns:
            The complete OpenAI response object (ChatCompletion).
        """
        logger.info("Sending non-streaming OpenAI request")

        request_messages = messages.copy()

        # Handle system message for OpenAI (prepend to messages list)
        system_message_content = self.platform_config.get("system_message")
        if self.platform and system_message_content:
            if not request_messages or request_messages[0].get("role") != "system":
                request_messages.insert(
                    0, {"role": "system", "content": system_message_content}
                )
                logger.info("Prepended system message for OpenAI request.")
            else:
                logger.warning(
                    "System message provided but message history already starts with one. Using existing."
                )

        # Prepare request parameters for OpenAI
        kwargs = {
            "model": self.model,  # Ensure this is an OpenAI model name
            "max_tokens": self.max_tokens,
            "messages": request_messages,
        }

        # Add tools if provided
        if available_tools:
            kwargs["tools"] = available_tools
            # kwargs["tool_choice"] = "auto" # Or specify if needed

        # Make the API call
        try:
            response = await self.openai_client.chat.completions.create(**kwargs)
            # The response object itself is the result (openai.types.chat.ChatCompletion)
            return response
        except Exception as e:
            logger.error(
                f"Error in non-streaming OpenAI request: {str(e)}", exc_info=True
            )
            raise

    @staticmethod
    def to_chat_messages(raw_messages: List[Dict[str, Any]]) -> List[ChatMessage]:
        """
        Convert a list of OpenAI format messages to ChatMessage format

        Args:
            raw_messages: List of messages in OpenAI format

        Returns:
            List of ChatMessages
        """
        chat_messages = []

        for openai_message in raw_messages:
            role = MessageRole(openai_message.get("role"))
            content_list = []

            # Handle text content
            if isinstance(openai_message.get("content"), str):
                content_list.append(TextContent(text=openai_message["content"]))

            # Handle tool calls
            if openai_message.get("tool_calls"):
                for tool_call in openai_message["tool_calls"]:
                    if tool_call.get("type") == "function":
                        # Parse arguments if they are a string (JSON)
                        arguments = tool_call["function"]["arguments"]
                        parsed_arguments = {}

                        if isinstance(arguments, str):
                            import json
                            try:
                                parsed_arguments = json.loads(arguments)
                            except json.JSONDecodeError as e:
                                logger.error(
                                    f"Error parsing tool arguments {arguments} JSON: {e}"
                                )
                                # If JSON parsing fails, create an empty dict to avoid validation errors
                                parsed_arguments = {}
                        else:
                            parsed_arguments = arguments

                        content_list.append(
                            ToolCallContent(
                                tool_id=tool_call.get("id", str(uuid.uuid4())),
                                name=tool_call["function"]["name"],
                                arguments=parsed_arguments,
                            )
                        )

            # Handle tool results
            if (
                    role == MessageRole.TOOL
                    and openai_message.get("content")
                    and openai_message.get("tool_call_id")
            ):
                content_list.append(
                    ToolResultContent(
                        tool_call_id=openai_message["tool_call_id"],
                        result=openai_message["content"],
                    )
                )

            chat_messages.append(
                ChatMessage(
                    role=role,
                    content=content_list,
                    id=openai_message.get("id", str(uuid.uuid4())),
                )
            )
        return chat_messages

    @staticmethod
    def from_chat_messages(chat_messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """
        Convert a list of ChatMessages to OpenAI format

        Args:
            chat_messages: List of ChatMessages to convert

        Returns:
            List of messages in OpenAI format
        """
        openai_messages = []

        for chat_message in chat_messages:

            if chat_message.role == MessageRole.SYSTEM:
                openai_messages.append(
                    {
                        "role": chat_message.role.value,
                        "content": "".join(
                            [content.text for content in chat_message.content]
                        ),
                    }
                )

            if chat_message.role == MessageRole.USER:
                str_content = ""
                for content in chat_message.content:
                    if content.type == ContentType.TEXT:
                        str_content += content.text
                    if content.type == ContentType.FILE:
                        str_content += f"\nUser uploaded a file as attachment. The url is \"{content.url}\"."
                        if content.auth_token:
                            str_content += f"\nThe auth token is \"{content.auth_token}\"."
                openai_messages.append(
                    {"role": chat_message.role.value, "content": str_content}
                )

            if chat_message.role == MessageRole.TOOL:
                for content in chat_message.content:
                    openai_messages.append(
                        {
                            "role": chat_message.role.value,
                            "content": content.result,
                            "tool_call_id": content.tool_call_id,
                        }
                    )

            if chat_message.role == MessageRole.ASSISTANT:
                for content in chat_message.content:
                    if content.type == ContentType.TEXT and content.text:
                        openai_messages.append(
                            {"role": chat_message.role.value, "content": content.text}
                        )
                    if content.type == ContentType.TOOL_CALL and content.name:
                        # An assistant message with 'tool_calls' must be followed by tool messages.
                        # So we need to ignore any other text content after the tool calls.
                        break

                tool_calls = []
                for content in chat_message.content:
                    if content.type == ContentType.TOOL_CALL and content.name:
                        tool_calls.append(
                            {
                                "type": "function",
                                "id": content.tool_id,
                                "function": {
                                    "name": content.name,
                                    "arguments": str(content.arguments),
                                },
                            }
                        )
                if tool_calls:
                    openai_messages.append(
                        {
                            "role": chat_message.role.value,
                            "tool_calls": tool_calls,
                        }
                    )
        return openai_messages
