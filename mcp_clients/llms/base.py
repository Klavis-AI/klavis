from typing import Any, Dict, List, Literal, Optional, Union, AsyncGenerator
from pydantic import BaseModel, Field, model_validator
from abc import ABC, abstractmethod
import logging
from enum import Enum

from typing import List, Optional, Union, Dict, Any, Literal
from datetime import datetime
import uuid


logger = logging.getLogger("llm_client")

# Platform-specific configurations
PLATFORM_CONFIGS = {
    "discord": {
        "message_split_token": "<discord:new_message>",
        "max_message_length": 1500,
        "system_message": """You're Klavis AI, a helpful AI assistant communicating through Discord. Users can choose to connect a variety of tools to help fulfill their requests. 
Most importantly, Discord has a 1500 character limit per message. When appropriate, split your response into multiple messages using the <discord:new_message> token. 
Place these tokens at natural breaking points in your response. Never exceed this limit when splitting your response. 

Key things to remember:
1. Never explain these tokens or formatting instructions to users.
2. Keep responses direct and concise for the chat environment.
3. For urls, do not use markdown. Directly return the url in the response.""",
    },
    "slack": {
        "message_split_token": "<slack:new_message>",
        "max_message_length": 4000,
        "system_message": """You're Klavis AI, a helpful AI assistant communicating through Slack. Users can choose to connect a variety of tools to help fulfill their requests. 
Most importantly, Slack has a 4000 character limit per message. When appropriate, split your response into multiple messages using the <slack:new_message> token. 
Place these tokens at natural breaking points in your response. Never exceed this limit when splitting your response. 

                    
Key things to remember:
1. Never explain these tokens or formatting instructions to users.
2. Keep responses direct and concise for the chat environment.""",
    },
    # Default configuration for unknown platforms
    "default": {
        "message_split_token": "<new_message>",
        "max_message_length": 2000,
        "system_message": """You're Klavis AI, a helpful AI assistant. You have access to a variety of tools to help fulfill user requests.

Key things to remember:
1. Analyze user requests to determine if a tool call is necessary to perform an action or retrieve information.
2. Call tools when needed to complete the user's request effectively.
3. When appropriate, split your response into multiple messages using the <new_message> token.""",
    },
}


class BaseLLMConfig(BaseModel):
    """
    Pydantic model for LLM configuration.
    """

    model: Optional[str] = Field(
        default=None, description="The name of the model to use."
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for the LLM provider."
    )
    temperature: float = Field(
        default=0, ge=0, le=2, description="Randomness in generation (0 to 2)."
    )
    max_tokens: int = Field(
        default=3000, gt=0, description="The maximum number of tokens to generate."
    )


# Core message domain models
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ContentType(str, Enum):
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FILE = "file"


class TextContent(BaseModel):
    type: Literal[ContentType.TEXT] = Field(
        default=ContentType.TEXT,
        description="The type of content, set to TEXT for text-based messages.",
    )
    text: str = Field(description="The actual text content of the message.")


class ToolCallContent(BaseModel):
    type: Literal[ContentType.TOOL_CALL] = Field(
        default=ContentType.TOOL_CALL,
        description="The type of content, set to TOOL_CALL for tool invocations.",
    )
    tool_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the tool call.",
    )
    name: str = Field(description="Name of the tool being called.")
    arguments: Dict[str, Any] = Field(description="Arguments to be passed to the tool.")


class ToolResultContent(BaseModel):
    type: Literal[ContentType.TOOL_RESULT] = Field(
        default=ContentType.TOOL_RESULT,
        description="The type of content, set to TOOL_RESULT for tool execution results.",
    )
    tool_call_id: str = Field(
        description="ID of the tool call this result corresponds to."
    )
    result: str = Field(description="The result returned from the tool execution.")


class FileContent(BaseModel):
    type: Literal[ContentType.FILE] = Field(
        default=ContentType.FILE,
        description="The type of content, set to FILE for file-based messages.",
    )
    filename: str = Field(description="Name of the file.")
    extension: str = Field(description="Extension of the file.")
    url: str = Field(description="URL of the file.")
    auth_token: str = Field(
        default=None, description="Authentication token for the file."
    )


# Unified message model
class ChatMessage(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the message.",
    )
    role: MessageRole = Field(
        description="Role of the message sender (system, user, assistant, or tool)."
    )
    content: List[
        Union[TextContent, ToolCallContent, ToolResultContent, FileContent]
    ] = Field(
        description="List of content items in the message, can be text, file, tool calls, or tool results."
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the message was created.",
    )

    @model_validator(mode="after")
    def validate_role_content(self):
        """
        Validate the role and content of the message.
        """
        if self.role == MessageRole.TOOL:
            for item in self.content:
                if not isinstance(item, ToolResultContent):
                    raise ValueError(
                        "When role is 'tool', content can only contain ToolResultContent objects"
                    )
        elif self.role == MessageRole.USER:
            for item in self.content:
                if not isinstance(item, (TextContent, FileContent)):
                    raise ValueError(
                        f"When role is '{self.role}', content can only contain TextContent or FileContent objects"
                    )
        elif self.role in MessageRole.SYSTEM:
            for item in self.content:
                if not isinstance(item, TextContent):
                    raise ValueError(
                        f"When role is '{self.role}', content can only contain TextContent objects"
                    )
        elif self.role == MessageRole.ASSISTANT:
            for item in self.content:
                if not isinstance(item, (TextContent, ToolCallContent)):
                    raise ValueError(
                        "When role is 'assistant', content can only contain TextContent or ToolCallContent objects"
                    )
        return self


# Conversation model to group messages
class Conversation(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the conversation.",
    )
    messages: List[ChatMessage] = Field(
        default=[], description="List of messages in the conversation."
    )
    channel_id: Optional[str] = Field(
        default=None,
        description="Optional ID of the channel this conversation belongs to.",
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Optional ID of the thread this conversation belongs to.",
    )
    metadata: Dict[str, Any] = Field(
        default={}, description="Additional metadata associated with the conversation."
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the conversation was created.",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the conversation was last updated.",
    )


class LLMMessageFormat(Enum):
    """
    Enum to store the message format for LLM.
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMBase(ABC):
    """
    Base class for LLMs with Pydantic configuration.

    :param config: Pydantic model containing LLM configuration or dictionary.
    """

    def __init__(self, config: Optional[Union[BaseLLMConfig, Dict[str, Any]]] = None):
        if isinstance(config, dict):
            self.config = BaseLLMConfig(**config)
        elif config is None:
            self.config = BaseLLMConfig()
        else:
            self.config = config


class BaseLLM(ABC):
    """
    Base client for interacting with various LLM APIs.
    Defines the interface that all model-specific clients should implement.
    """

    def __init__(
        self,
        config: Optional[BaseLLMConfig] = None,
        message_format: Optional[LLMMessageFormat] = LLMMessageFormat.OPENAI,
    ):
        """
        Initialize the base LLM client

        Args:
            config: Optional configuration for the LLM
        """
        self.config = config if config else BaseLLMConfig()
        self.platform = None
        self.platform_config = PLATFORM_CONFIGS["default"]
        self.message_format = message_format

    def set_model(self, model: str):
        """Change the LLM model"""
        if self.config:
            self.config.model = model

    def set_max_tokens(self, max_tokens: int):
        """Change the max tokens value"""
        if self.config:
            self.config.max_tokens = max_tokens

    def set_platform(self, platform: str):
        """Set the platform context for responses"""
        self.platform = platform

        # Set platform-specific configuration
        if platform and platform.lower() in PLATFORM_CONFIGS:
            self.platform_config = PLATFORM_CONFIGS[platform.lower()]
            logger.info(f"Using {platform} platform configuration")
        else:
            self.platform_config = PLATFORM_CONFIGS["default"]
            logger.info(
                f"Platform '{platform}' not recognized, using default configuration"
            )

    def get_message_split_token(self) -> str:
        """Get the message split token for the current platform"""
        return self.platform_config["message_split_token"]

    def get_message_format(self) -> str:
        """Get the message format for LLM"""
        return self.message_format

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @staticmethod
    @abstractmethod
    def to_chat_messages(raw_messages: List[Dict[str, Any]]) -> List[ChatMessage]:
        """
        Convert a list of raw messages to ChatMessage format

        Args:
            raw_messages: List of messages in the raw message format

        Returns:
            List of ChatMessages
        """
        pass

    @staticmethod
    @abstractmethod
    def from_chat_messages(chat_messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """
        Convert a list of ChatMessages to the raw message format
        """
        pass
