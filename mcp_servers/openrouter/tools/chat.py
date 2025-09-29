"""
Chat completion tools for OpenRouter MCP Server.
"""

import logging
from typing import Dict, Any, Optional, List
from .base import (
    get_client, 
    validate_required_params, 
    validate_model_id, 
    validate_messages,
    OpenRouterToolExecutionError,
)

logger = logging.getLogger(__name__)


async def create_chat_completion(
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stream: bool = False,
    stop: Optional[List[str]] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a chat completion using OpenRouter.
    
    Args:
        model: The model to use for completion
        messages: List of message objects with 'role' and 'content'
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (0.0 to 2.0)
        top_p: Nucleus sampling parameter (0.0 to 1.0)
        n: Number of completions to generate (1 to 10)
        stream: Whether to stream the response
        stop: Stop sequences
        presence_penalty: Presence penalty (-2.0 to 2.0)
        frequency_penalty: Frequency penalty (-2.0 to 2.0)
        logit_bias: Logit bias dictionary
        user: User identifier
        
    Returns:
        Dictionary containing the completion response
    """
    try:
        validate_required_params({"model": model, "messages": messages}, ["model", "messages"])
        validate_model_id(model)
        validate_messages(messages)
        
        if temperature is not None and (temperature < 0.0 or temperature > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid temperature parameter",
                additional_prompt_content="Temperature must be between 0.0 and 2.0.",
                developer_message=f"Invalid temperature: {temperature}",
            )
        
        if top_p is not None and (top_p < 0.0 or top_p > 1.0):
            raise OpenRouterToolExecutionError(
                "Invalid top_p parameter",
                additional_prompt_content="Top_p must be between 0.0 and 1.0.",
                developer_message=f"Invalid top_p: {top_p}",
            )
        
        if n is not None and (n < 1 or n > 10):
            raise OpenRouterToolExecutionError(
                "Invalid n parameter",
                additional_prompt_content="N must be between 1 and 10.",
                developer_message=f"Invalid n: {n}",
            )
        
        if presence_penalty is not None and (presence_penalty < -2.0 or presence_penalty > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid presence_penalty parameter",
                additional_prompt_content="Presence penalty must be between -2.0 and 2.0.",
                developer_message=f"Invalid presence_penalty: {presence_penalty}",
            )
        
        if frequency_penalty is not None and (frequency_penalty < -2.0 or frequency_penalty > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid frequency_penalty parameter",
                additional_prompt_content="Frequency penalty must be between -2.0 and 2.0.",
                developer_message=f"Invalid frequency_penalty: {frequency_penalty}",
            )
        
        client = get_client()
        
        request_data = {
            "model": model,
            "messages": messages,
        }
        
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
        if temperature is not None:
            request_data["temperature"] = temperature
        if top_p is not None:
            request_data["top_p"] = top_p
        if n is not None:
            request_data["n"] = n
        if stream:
            request_data["stream"] = stream
        if stop:
            request_data["stop"] = stop
        if presence_penalty is not None:
            request_data["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            request_data["frequency_penalty"] = frequency_penalty
        if logit_bias:
            request_data["logit_bias"] = logit_bias
        if user:
            request_data["user"] = user
        
        response = await client.post("/chat/completions", request_data)
        
        logger.info(f"Successfully created chat completion with model: {model}")
        
        return {
            "success": True,
            "data": response,
            "model": model,
            "usage": response.get("usage", {}),
            "choices": response.get("choices", []),
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error creating chat completion: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to create chat completion: {str(e)}",
            additional_prompt_content="There was an error creating the chat completion. Please check your parameters and try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def create_chat_completion_stream(
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    stop: Optional[List[str]] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a streaming chat completion using OpenRouter.
    
    Args:
        model: The model to use for completion
        messages: List of message objects with 'role' and 'content'
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (0.0 to 2.0)
        top_p: Nucleus sampling parameter (0.0 to 1.0)
        stop: Stop sequences
        presence_penalty: Presence penalty (-2.0 to 2.0)
        frequency_penalty: Frequency penalty (-2.0 to 2.0)
        logit_bias: Logit bias dictionary
        user: User identifier
        
    Returns:
        Dictionary containing the streaming completion response
    """
    try:
        validate_required_params({"model": model, "messages": messages}, ["model", "messages"])
        validate_model_id(model)
        validate_messages(messages)
        
        if temperature is not None and (temperature < 0.0 or temperature > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid temperature parameter",
                additional_prompt_content="Temperature must be between 0.0 and 2.0.",
                developer_message=f"Invalid temperature: {temperature}",
            )
        
        if top_p is not None and (top_p < 0.0 or top_p > 1.0):
            raise OpenRouterToolExecutionError(
                "Invalid top_p parameter",
                additional_prompt_content="Top_p must be between 0.0 and 1.0.",
                developer_message=f"Invalid top_p: {top_p}",
            )
        
        if presence_penalty is not None and (presence_penalty < -2.0 or presence_penalty > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid presence_penalty parameter",
                additional_prompt_content="Presence penalty must be between -2.0 and 2.0.",
                developer_message=f"Invalid presence_penalty: {presence_penalty}",
            )
        
        if frequency_penalty is not None and (frequency_penalty < -2.0 or frequency_penalty > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid frequency_penalty parameter",
                additional_prompt_content="Frequency penalty must be between -2.0 and 2.0.",
                developer_message=f"Invalid frequency_penalty: {frequency_penalty}",
            )
        
        client = get_client()
        
        request_data = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
        if temperature is not None:
            request_data["temperature"] = temperature
        if top_p is not None:
            request_data["top_p"] = top_p
        if stop:
            request_data["stop"] = stop
        if presence_penalty is not None:
            request_data["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            request_data["frequency_penalty"] = frequency_penalty
        if logit_bias:
            request_data["logit_bias"] = logit_bias
        if user:
            request_data["user"] = user
        
        response = await client.post("/chat/completions", request_data)
        
        logger.info(f"Successfully created streaming chat completion with model: {model}")
        
        if response.get("stream"):
            logger.info("Returning streaming generator to caller...")
            
            # Get the stream generator and return it directly
            generator = response.get("generator")
            if generator:
                return {
                    "success": True,
                    "data": {
                        "stream": True,
                        "generator": generator,
                        "message": "Stream generator ready for processing"
                    },
                    "model": model,
                    "stream": True,
                    "usage": None,
                    "choices": [],
                }
            else:
                return {
                    "success": True,
                    "data": response,
                    "model": model,
                    "stream": True,
                    "usage": response.get("usage", {}),
                    "choices": response.get("choices", []),
                }
        else:
            return {
                "success": True,
                "data": response,
                "model": model,
                "stream": True,
                "usage": response.get("usage", {}),
                "choices": response.get("choices", []),
            }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error creating streaming chat completion: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to create streaming chat completion: {str(e)}",
            additional_prompt_content="There was an error creating the streaming chat completion. Please check your parameters and try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def create_completion(
    model: str,
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    n: Optional[int] = None,
    stream: bool = False,
    stop: Optional[List[str]] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    logit_bias: Optional[Dict[str, float]] = None,
    user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a text completion using OpenRouter (legacy completion endpoint).
    
    Args:
        model: The model to use for completion
        prompt: The text prompt to complete
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (0.0 to 2.0)
        top_p: Nucleus sampling parameter (0.0 to 1.0)
        n: Number of completions to generate (1 to 10)
        stream: Whether to stream the response
        stop: Stop sequences
        presence_penalty: Presence penalty (-2.0 to 2.0)
        frequency_penalty: Frequency penalty (-2.0 to 2.0)
        logit_bias: Logit bias dictionary
        user: User identifier
        
    Returns:
        Dictionary containing the completion response
    """
    try:
        validate_required_params({"model": model, "prompt": prompt}, ["model", "prompt"])
        validate_model_id(model)
        
        if not prompt or not isinstance(prompt, str):
            raise OpenRouterToolExecutionError(
                "Invalid prompt parameter",
                additional_prompt_content="Prompt must be a non-empty string.",
                developer_message="Prompt must be a non-empty string",
            )
        
        if temperature is not None and (temperature < 0.0 or temperature > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid temperature parameter",
                additional_prompt_content="Temperature must be between 0.0 and 2.0.",
                developer_message=f"Invalid temperature: {temperature}",
            )
        
        if top_p is not None and (top_p < 0.0 or top_p > 1.0):
            raise OpenRouterToolExecutionError(
                "Invalid top_p parameter",
                additional_prompt_content="Top_p must be between 0.0 and 1.0.",
                developer_message=f"Invalid top_p: {top_p}",
            )
        
        if n is not None and (n < 1 or n > 10):
            raise OpenRouterToolExecutionError(
                "Invalid n parameter",
                additional_prompt_content="N must be between 1 and 10.",
                developer_message=f"Invalid n: {n}",
            )
        
        if presence_penalty is not None and (presence_penalty < -2.0 or presence_penalty > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid presence_penalty parameter",
                additional_prompt_content="Presence penalty must be between -2.0 and 2.0.",
                developer_message=f"Invalid presence_penalty: {presence_penalty}",
            )
        
        if frequency_penalty is not None and (frequency_penalty < -2.0 or frequency_penalty > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid frequency_penalty parameter",
                additional_prompt_content="Frequency penalty must be between -2.0 and 2.0.",
                developer_message=f"Invalid frequency_penalty: {frequency_penalty}",
            )
        
        client = get_client()
        
        request_data = {
            "model": model,
            "prompt": prompt,
        }
        
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
        if temperature is not None:
            request_data["temperature"] = temperature
        if top_p is not None:
            request_data["top_p"] = top_p
        if n is not None:
            request_data["n"] = n
        if stream:
            request_data["stream"] = stream
        if stop:
            request_data["stop"] = stop
        if presence_penalty is not None:
            request_data["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            request_data["frequency_penalty"] = frequency_penalty
        if logit_bias:
            request_data["logit_bias"] = logit_bias
        if user:
            request_data["user"] = user
        
        response = await client.post("/completions", request_data)
        
        logger.info(f"Successfully created completion with model: {model}")
        
        return {
            "success": True,
            "data": response,
            "model": model,
            "usage": response.get("usage", {}),
            "choices": response.get("choices", []),
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error creating completion: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to create completion: {str(e)}",
            additional_prompt_content="There was an error creating the completion. Please check your parameters and try again.",
            developer_message=f"Unexpected error: {str(e)}",
        ) 