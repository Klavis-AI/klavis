"""
Usage tracking and user profile tools for OpenRouter MCP Server.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, date
from .base import get_client, validate_required_params, OpenRouterToolExecutionError

logger = logging.getLogger(__name__)


async def get_usage(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 100,
) -> Dict[str, Any]:
    """
    Get usage statistics for the authenticated user.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        limit: Maximum number of records to return (1-1000, default 100)
        
    Returns:
        Dictionary containing usage statistics
    """
    try:
        if limit is not None and (limit < 1 or limit > 1000):
            raise OpenRouterToolExecutionError(
                "Invalid limit parameter",
                additional_prompt_content="Limit must be between 1 and 1000.",
                developer_message=f"Invalid limit: {limit}",
            )
        
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise OpenRouterToolExecutionError(
                    "Invalid start_date format",
                    additional_prompt_content="Start date must be in YYYY-MM-DD format.",
                    developer_message=f"Invalid start_date format: {start_date}",
                )
        
        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise OpenRouterToolExecutionError(
                    "Invalid end_date format",
                    additional_prompt_content="End date must be in YYYY-MM-DD format.",
                    developer_message=f"Invalid end_date format: {end_date}",
                )
        
        client = get_client()
        
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        
        response = await client.get("/auth/key", params=params)
        
        logger.info(f"Successfully retrieved usage statistics")
        
        return {
            "success": True,
            "data": response,
            "start_date": start_date,
            "end_date": end_date,
            "usage_summary": {
                "total_requests": response.get("total_requests", 0),
                "total_tokens": response.get("total_tokens", 0),
                "total_cost": response.get("total_cost", 0),
                "currency": "USD",
            },
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error getting usage statistics: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to get usage statistics: {str(e)}",
            additional_prompt_content="There was an error retrieving usage statistics. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def get_user_profile() -> Dict[str, Any]:
    """
    Get the current user's profile information.
    
    Returns:
        Dictionary containing user profile information
    """
    try:
        client = get_client()
        
        response = await client.get("/auth/key")
        
        logger.info("Successfully retrieved user profile")
        
        return {
            "success": True,
            "data": response,
            "user_info": {
                "user_id": response.get("user_id"),
                "email": response.get("email"),
                "name": response.get("name"),
                "credits": response.get("credits", 0),
                "plan": response.get("plan", "free"),
                "created_at": response.get("created_at"),
            },
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error getting user profile: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to get user profile: {str(e)}",
            additional_prompt_content="There was an error retrieving your profile information. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def get_credits() -> Dict[str, Any]:
    """
    Get the current user's credit balance.
    
    Returns:
        Dictionary containing credit information with total_credits and total_usage
    """
    try:
        client = get_client()
        
        # Use the correct endpoint as per OpenRouter API documentation
        response = await client.get("/credits")
        
        # Extract data from response according to API spec
        data = response.get("data", {})
        total_credits = data.get("total_credits", 0)
        total_usage = data.get("total_usage", 0)
        
        logger.info(f"Successfully retrieved credit balance: {total_credits} credits, {total_usage} used")
        
        return {
            "success": True,
            "total_credits": total_credits,
            "total_usage": total_usage,
            "available_credits": total_credits - total_usage,
            "currency": "USD",
            "data": response,
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error getting credits: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to get credits: {str(e)}",
            additional_prompt_content="There was an error retrieving your credit balance. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def get_api_key_info() -> Dict[str, Any]:
    """
    Get information about the current API key.
    
    Returns:
        Dictionary containing API key information
    """
    try:
        client = get_client()
        
        response = await client.get("/auth/key")
        
        logger.info("Successfully retrieved API key information")
        
        return {
            "success": True,
            "data": response,
            "key_info": {
                "key_id": response.get("id"),
                "name": response.get("name"),
                "created_at": response.get("created_at"),
                "last_used": response.get("last_used"),
                "permissions": response.get("permissions", []),
                "is_active": response.get("is_active", True),
            },
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error getting API key info: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to get API key information: {str(e)}",
            additional_prompt_content="There was an error retrieving API key information. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def get_cost_estimate(
    model: str,
    input_tokens: int,
    output_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Estimate the cost for a specific model and token usage.
    
    Args:
        model: The model ID to estimate costs for
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens (optional, defaults to 0)
        
    Returns:
        Dictionary containing cost estimate
    """
    try:
        validate_required_params({"model": model, "input_tokens": input_tokens}, ["model", "input_tokens"])
        
        if input_tokens < 0:
            raise OpenRouterToolExecutionError(
                "Invalid input_tokens parameter",
                additional_prompt_content="Input tokens must be a non-negative number.",
                developer_message=f"Invalid input_tokens: {input_tokens}",
            )
        
        if output_tokens is not None and output_tokens < 0:
            raise OpenRouterToolExecutionError(
                "Invalid output_tokens parameter",
                additional_prompt_content="Output tokens must be a non-negative number.",
                developer_message=f"Invalid output_tokens: {output_tokens}",
            )
        
        client = get_client()
        
        model_response = await client.get(f"/models/{model}")
        pricing = model_response.get("pricing", {})
        
        input_cost_per_1k = pricing.get("input", 0)
        output_cost_per_1k = pricing.get("output", 0)
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens or 0) / 1000 * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        logger.info(f"Cost estimate for {model}: ${total_cost:.6f}")
        
        return {
            "success": True,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens or 0,
            "cost_breakdown": {
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total_cost,
            },
            "pricing": {
                "input_cost_per_1k_tokens": input_cost_per_1k,
                "output_cost_per_1k_tokens": output_cost_per_1k,
                "currency": "USD",
            },
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error estimating cost: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to estimate cost: {str(e)}",
            additional_prompt_content="There was an error estimating the cost. Please check the model ID and try again.",
            developer_message=f"Unexpected error: {str(e)}",
        ) 