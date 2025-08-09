"""
Base utilities and error handling for OpenRouter MCP Server.
"""

import contextvars
import logging
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)

auth_token_context = contextvars.ContextVar("auth_token", default="")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterToolExecutionError(Exception):
    """Custom exception for OpenRouter tool execution errors."""
    
    def __init__(
        self,
        message: str,
        retry_after_ms: Optional[int] = None,
        additional_prompt_content: Optional[str] = None,
        developer_message: Optional[str] = None,
    ):
        super().__init__(message)
        self.retry_after_ms = retry_after_ms
        self.additional_prompt_content = additional_prompt_content
        self.developer_message = developer_message


class OpenRouterAPIError(Exception):
    """Exception for OpenRouter API errors."""
    
    def __init__(self, status_code: int, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class OpenRouterClient:
    """HTTP client for OpenRouter API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = OPENROUTER_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://klavis.ai",
            "X-Title": "Klavis MCP Server",
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the OpenRouter API."""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                )
                
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_after_ms = int(retry_after) * 1000 if retry_after else 60000
                    raise OpenRouterToolExecutionError(
                        "Rate limit exceeded",
                        retry_after_ms=retry_after_ms,
                        additional_prompt_content="Please wait before making another request.",
                        developer_message=f"Rate limited. Retry after {retry_after_ms}ms",
                    )
                
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    raise OpenRouterAPIError(
                        status_code=response.status_code,
                        message=error_message,
                        details=error_data,
                    )
                
                if data and data.get("stream") and response.status_code == 200:
                    # For streaming responses, return a generator that yields chunks
                    async def stream_generator():
                        try:
                            chunk_count = 0
                            async for chunk in response.aiter_text():
                                lines = chunk.split('\n')
                                for line in lines:
                                    if line.startswith('data: '):
                                        data_line = line[6:]
                                        if data_line.strip() == '[DONE]':
                                            logger.info("Received [DONE] marker - stream complete")
                                            yield {
                                                "chunk": None,
                                                "is_complete": True,
                                                "total_chunks": chunk_count,
                                                "message": "Stream completed"
                                            }
                                            return
                                        try:
                                            json_data = json.loads(data_line)
                                            if 'choices' in json_data and json_data['choices']:
                                                delta = json_data['choices'][0].get('delta', {})
                                                if 'content' in delta:
                                                    chunk_count += 1
                                                    content = delta['content']
                                                    logger.info(f"Yielding chunk {chunk_count}: '{content}'")
                                                    yield {
                                                        "chunk": content,
                                                        "is_complete": False,
                                                        "chunk_number": chunk_count,
                                                        "message": f"Chunk {chunk_count} received"
                                                    }
                                        except json.JSONDecodeError:
                                            continue
                            
                            yield {
                                "chunk": None,
                                "is_complete": True,
                                "total_chunks": chunk_count,
                                "message": "Stream ended without [DONE] marker"
                            }
                            
                        except Exception as e:
                            logger.error(f"Error in stream generator: {e}")
                            yield {
                                "chunk": None,
                                "is_complete": True,
                                "error": str(e),
                                "message": f"Stream error: {str(e)}"
                            }
                    
                    return {
                        "stream": True,
                        "status_code": response.status_code,
                        "generator": stream_generator(),
                        "message": "Stream generator created"
                    }
                
                # Try to parse as JSON, but handle empty responses gracefully
                if response.content:
                    return response.json()
                else:
                    return {"status": "success", "message": "Empty response received"}
                
            except httpx.TimeoutException:
                raise OpenRouterToolExecutionError(
                    "Request timeout",
                    retry_after_ms=5000,
                    additional_prompt_content="The request took too long. Please try again.",
                    developer_message="Request timed out after 30 seconds",
                )
            except httpx.RequestError as e:
                raise OpenRouterToolExecutionError(
                    f"Network error: {str(e)}",
                    retry_after_ms=5000,
                    additional_prompt_content="There was a network error. Please check your connection and try again.",
                    developer_message=f"Network error: {str(e)}",
                )
            except Exception as e:
                if "Expecting value" in str(e) and data and data.get("stream"):
                    return {
                        "stream": True,
                        "status_code": response.status_code,
                        "content": "Streaming response received",
                        "message": "This is a streaming response. Use appropriate streaming client to handle it."
                    }
                raise
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._make_request("POST", endpoint, data=data)


def get_client() -> OpenRouterClient:
    """Get an OpenRouter client with the current auth token."""
    api_key = auth_token_context.get()
    if not api_key:
        raise OpenRouterToolExecutionError(
            "Missing API key",
            additional_prompt_content="Please provide your OpenRouter API key in the x-auth-token header.",
            developer_message="No API key provided in auth_token_context",
        )
    return OpenRouterClient(api_key)


def validate_required_params(params: Dict[str, Any], required: list[str]) -> None:
    """Validate that required parameters are present."""
    missing = [param for param in required if param not in params or params[param] is None]
    if missing:
        raise OpenRouterToolExecutionError(
            f"Missing required parameters: {', '.join(missing)}",
            additional_prompt_content=f"Please provide the following required parameters: {', '.join(missing)}",
            developer_message=f"Missing required parameters: {missing}",
        )


def validate_model_id(model_id: str) -> None:
    """Validate model ID format."""
    if not model_id or not isinstance(model_id, str):
        raise OpenRouterToolExecutionError(
            "Invalid model ID",
            additional_prompt_content="Please provide a valid model ID (e.g., 'anthropic/claude-3-opus').",
            developer_message="Model ID must be a non-empty string",
        )


def validate_messages(messages: list) -> None:
    """Validate chat messages format."""
    if not messages or not isinstance(messages, list):
        raise OpenRouterToolExecutionError(
            "Invalid messages format",
            additional_prompt_content="Messages must be a non-empty list of message objects.",
            developer_message="Messages must be a non-empty list",
        )
    
    for i, message in enumerate(messages):
        if not isinstance(message, dict):
            raise OpenRouterToolExecutionError(
                f"Invalid message format at index {i}",
                additional_prompt_content="Each message must be an object with 'role' and 'content' fields.",
                developer_message=f"Message at index {i} is not a dictionary",
            )
        
        if "role" not in message or "content" not in message:
            raise OpenRouterToolExecutionError(
                f"Missing required fields in message at index {i}",
                additional_prompt_content="Each message must have 'role' and 'content' fields.",
                developer_message=f"Message at index {i} missing required fields",
            )
        
        if message["role"] not in ["system", "user", "assistant"]:
            raise OpenRouterToolExecutionError(
                f"Invalid role '{message['role']}' in message at index {i}",
                additional_prompt_content="Message role must be 'system', 'user', or 'assistant'.",
                developer_message=f"Invalid role: {message['role']}",
            )


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""
    model: str = Field(..., description="The model to use for completion")
    messages: list[ChatMessage] = Field(..., description="The messages to complete")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    n: Optional[int] = Field(None, ge=1, le=10, description="Number of completions to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    stop: Optional[list[str]] = Field(None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Frequency penalty")
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Logit bias")
    user: Optional[str] = Field(None, description="User identifier") 