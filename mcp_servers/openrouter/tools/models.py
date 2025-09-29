"""
Model management tools for OpenRouter MCP Server.
"""

import logging
from typing import Dict, Any, Optional
from .base import get_client, validate_required_params, validate_model_id, OpenRouterToolExecutionError

logger = logging.getLogger(__name__)


async def list_models(limit: Optional[int] = 50, next_page_token: Optional[str] = None) -> Dict[str, Any]:
    """
    List available models on OpenRouter.
    
    Args:
        limit: Maximum number of models to return (1-100, default 50)
        next_page_token: Token for pagination
        
    Returns:
        Dictionary containing models and pagination info
    """
    try:
        if limit is not None and (limit < 1 or limit > 100):
            raise OpenRouterToolExecutionError(
                "Invalid limit parameter",
                additional_prompt_content="Limit must be between 1 and 100.",
                developer_message=f"Invalid limit: {limit}",
            )
        
        client = get_client()
        
        params = {}
        if limit is not None:
            params["limit"] = limit
        if next_page_token:
            params["after"] = next_page_token
        
        response = await client.get("/models", params=params)
        
        logger.info(f"Successfully retrieved {len(response.get('data', []))} models")
        
        return {
            "success": True,
            "data": response.get("data", []),
            "pagination": response.get("pagination", {}),
            "total_count": len(response.get("data", [])),
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error listing models: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to list models: {str(e)}",
            additional_prompt_content="There was an error retrieving the models. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )

async def search_models(
    query: str,
    limit: Optional[int] = 20,
    category: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search for models based on various criteria.
    
    Args:
        query: Search query string
        limit: Maximum number of models to return (1-100, default 20)
        category: Filter by model category (e.g., 'chat', 'completion', 'embedding')
        provider: Filter by provider (e.g., 'anthropic', 'openai', 'meta-llama')
        
    Returns:
        Dictionary containing matching models
    """
    try:
        validate_required_params({"query": query}, ["query"])
        
        if limit is not None and (limit < 1 or limit > 100):
            raise OpenRouterToolExecutionError(
                "Invalid limit parameter",
                additional_prompt_content="Limit must be between 1 and 100.",
                developer_message=f"Invalid limit: {limit}",
            )
        
        client = get_client()
        
        all_models_response = await client.get("/models")
        all_models = all_models_response.get("data", [])
        
        filtered_models = []
        query_lower = query.lower()
        
        for model in all_models:
            model_name = model.get("id", "").lower()
            model_description = model.get("description", "").lower()
            
            if query_lower in model_name or query_lower in model_description:
                if category and model.get("category") != category:
                    continue
                if provider and not model.get("id", "").startswith(f"{provider}/"):
                    continue
                
                filtered_models.append(model)
                    
                if limit and len(filtered_models) >= limit:
                    break
        
        logger.info(f"Found {len(filtered_models)} models matching query: {query}")
        
        return {
            "success": True,
            "data": filtered_models,
            "query": query,
            "category": category,
            "provider": provider,
            "total_count": len(filtered_models),
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error searching models: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to search models: {str(e)}",
            additional_prompt_content="There was an error searching for models. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def get_model_pricing(model_id: str) -> Dict[str, Any]:
    """
    Get pricing information for a specific model.
    
    Args:
        model_id: The ID of the model to get pricing for
        
    Returns:
        Dictionary containing pricing information
    """
    try:
        validate_required_params({"model_id": model_id}, ["model_id"])
        validate_model_id(model_id)
        
        client = get_client()
        
        response = await client.get(f"/models/{model_id}")
        
        pricing = response.get("pricing", {})
        
        logger.info(f"Successfully retrieved pricing for model: {model_id}")
        
        return {
            "success": True,
            "model_id": model_id,
            "pricing": pricing,
            "input_cost_per_1k_tokens": pricing.get("input", 0),
            "output_cost_per_1k_tokens": pricing.get("output", 0),
            "currency": "USD",
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error getting pricing for model {model_id}: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to get pricing for model {model_id}: {str(e)}",
            additional_prompt_content=f"There was an error retrieving pricing for model {model_id}. Please check the model ID and try again.",
            developer_message=f"Unexpected error getting pricing for model {model_id}: {str(e)}",
        ) 