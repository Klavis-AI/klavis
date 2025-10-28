"""
Model comparison and analysis tools for OpenRouter MCP Server.
"""

import logging
from typing import Dict, Any, List, Optional
from .base import get_client, validate_required_params, validate_model_id, OpenRouterToolExecutionError

logger = logging.getLogger(__name__)


async def compare_models(
    models: List[str],
    test_prompt: str,
    max_tokens: Optional[int] = 100,
    temperature: Optional[float] = 0.7,
) -> Dict[str, Any]:
    """
    Compare multiple models by running the same prompt through each.
    
    Args:
        models: List of model IDs to compare
        test_prompt: The prompt to test with all models
        max_tokens: Maximum tokens to generate (default 100)
        temperature: Sampling temperature (default 0.7)
        
    Returns:
        Dictionary containing comparison results
    """
    try:
        validate_required_params({"models": models, "test_prompt": test_prompt}, ["models", "test_prompt"])
        
        if not models or not isinstance(models, list):
            raise OpenRouterToolExecutionError(
                "Invalid models parameter",
                additional_prompt_content="Models must be a non-empty list of model IDs.",
                developer_message="Models must be a non-empty list",
            )
        
        if len(models) < 2:
            raise OpenRouterToolExecutionError(
                "At least 2 models required for comparison",
                additional_prompt_content="Please provide at least 2 models to compare.",
                developer_message="Need at least 2 models for comparison",
            )
        
        if len(models) > 5:
            raise OpenRouterToolExecutionError(
                "Too many models for comparison",
                additional_prompt_content="Please provide no more than 5 models to compare.",
                developer_message="Too many models for comparison",
            )
        
        for model_id in models:
            validate_model_id(model_id)
        
        if not test_prompt or not isinstance(test_prompt, str):
            raise OpenRouterToolExecutionError(
                "Invalid test_prompt parameter",
                additional_prompt_content="Test prompt must be a non-empty string.",
                developer_message="Test prompt must be a non-empty string",
            )
        
        if temperature is not None and (temperature < 0.0 or temperature > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid temperature parameter",
                additional_prompt_content="Temperature must be between 0.0 and 2.0.",
                developer_message=f"Invalid temperature: {temperature}",
            )
        
        client = get_client()
        
        messages = [{"role": "user", "content": test_prompt}]
        
        results = []
        for model_id in models:
            try:
                request_data = {
                    "model": model_id,
                    "messages": messages,
                    "max_tokens": max_tokens or 100,
                    "temperature": temperature or 0.7,
                }
                
                response = await client.post("/chat/completions", request_data)
                
                choices = response.get("choices", [])
                content = choices[0].get("message", {}).get("content", "") if choices else ""
                usage = response.get("usage", {})
                
                results.append({
                    "model": model_id,
                    "success": True,
                    "response": content,
                    "usage": {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    "error": None,
                })
                
                logger.info(f"Successfully tested model: {model_id}")
                
            except Exception as e:
                logger.warning(f"Error testing model {model_id}: {e}")
                results.append({
                    "model": model_id,
                    "success": False,
                    "response": None,
                    "usage": None,
                    "error": str(e),
                })
        
        successful_results = [r for r in results if r["success"]]
        
        comparison_summary = {
            "total_models": len(models),
            "successful_tests": len(successful_results),
            "failed_tests": len(results) - len(successful_results),
            "test_prompt": test_prompt,
            "parameters": {
                "max_tokens": max_tokens or 100,
                "temperature": temperature or 0.7,
            },
        }
        
        if successful_results:
            total_tokens = [r["usage"]["total_tokens"] for r in successful_results]
            completion_tokens = [r["usage"]["completion_tokens"] for r in successful_results]
            
            comparison_summary["token_usage"] = {
                "min_total_tokens": min(total_tokens),
                "max_total_tokens": max(total_tokens),
                "avg_total_tokens": sum(total_tokens) / len(total_tokens),
                "min_completion_tokens": min(completion_tokens),
                "max_completion_tokens": max(completion_tokens),
                "avg_completion_tokens": sum(completion_tokens) / len(completion_tokens),
            }
        
        logger.info(f"Successfully compared {len(successful_results)} models")
        
        return {
            "success": True,
            "comparison_summary": comparison_summary,
            "results": results,
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error comparing models: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to compare models: {str(e)}",
            additional_prompt_content="There was an error comparing the models. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def analyze_model_performance(
    model: str,
    test_prompts: List[str],
    max_tokens: Optional[int] = 100,
    temperature: Optional[float] = 0.7,
) -> Dict[str, Any]:
    """
    Analyze the performance of a single model across multiple test prompts.
    
    Args:
        model: The model ID to analyze
        test_prompts: List of test prompts to use
        max_tokens: Maximum tokens to generate (default 100)
        temperature: Sampling temperature (default 0.7)
        
    Returns:
        Dictionary containing performance analysis
    """
    try:
        validate_required_params({"model": model, "test_prompts": test_prompts}, ["model", "test_prompts"])
        validate_model_id(model)
        
        if not test_prompts or not isinstance(test_prompts, list):
            raise OpenRouterToolExecutionError(
                "Invalid test_prompts parameter",
                additional_prompt_content="Test prompts must be a non-empty list of strings.",
                developer_message="Test prompts must be a non-empty list",
            )
        
        if len(test_prompts) > 10:
            raise OpenRouterToolExecutionError(
                "Too many test prompts",
                additional_prompt_content="Please provide no more than 10 test prompts.",
                developer_message="Too many test prompts",
            )
        
        for i, prompt in enumerate(test_prompts):
            if not prompt or not isinstance(prompt, str):
                raise OpenRouterToolExecutionError(
                    f"Invalid prompt at index {i}",
                    additional_prompt_content=f"Prompt at index {i} must be a non-empty string.",
                    developer_message=f"Invalid prompt at index {i}",
                )
        
        if temperature is not None and (temperature < 0.0 or temperature > 2.0):
            raise OpenRouterToolExecutionError(
                "Invalid temperature parameter",
                additional_prompt_content="Temperature must be between 0.0 and 2.0.",
                developer_message=f"Invalid temperature: {temperature}",
            )
        
        client = get_client()
        
        results = []
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_total_tokens = 0
        
        for i, prompt in enumerate(test_prompts):
            try:
                messages = [{"role": "user", "content": prompt}]
                
                request_data = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens or 100,
                    "temperature": temperature or 0.7,
                }
                
                response = await client.post("/chat/completions", request_data)
                
                choices = response.get("choices", [])
                content = choices[0].get("message", {}).get("content", "") if choices else ""
                usage = response.get("usage", {})
                
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                
                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens
                total_total_tokens += total_tokens
                
                results.append({
                    "prompt_index": i,
                    "prompt": prompt,
                    "success": True,
                    "response": content,
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    },
                    "error": None,
                })
                
                logger.info(f"Successfully tested prompt {i+1}/{len(test_prompts)} with model: {model}")
                
            except Exception as e:
                logger.warning(f"Error testing prompt {i} with model {model}: {e}")
                results.append({
                    "prompt_index": i,
                    "prompt": prompt,
                    "success": False,
                    "response": None,
                    "usage": None,
                    "error": str(e),
                })
        
        successful_results = [r for r in results if r["success"]]
        
        performance_summary = {
            "model": model,
            "total_prompts": len(test_prompts),
            "successful_tests": len(successful_results),
            "failed_tests": len(results) - len(successful_results),
            "success_rate": len(successful_results) / len(test_prompts) if test_prompts else 0,
            "parameters": {
                "max_tokens": max_tokens or 100,
                "temperature": temperature or 0.7,
            },
            "total_usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_total_tokens,
            },
        }
        
        if successful_results:
            avg_prompt_tokens = total_prompt_tokens / len(successful_results)
            avg_completion_tokens = total_completion_tokens / len(successful_results)
            avg_total_tokens = total_total_tokens / len(successful_results)
            
            performance_summary["average_usage"] = {
                "prompt_tokens": avg_prompt_tokens,
                "completion_tokens": avg_completion_tokens,
                "total_tokens": avg_total_tokens,
            }
        
        logger.info(f"Successfully analyzed model {model} performance across {len(successful_results)} prompts")
        
        return {
            "success": True,
            "performance_summary": performance_summary,
            "results": results,
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error analyzing model performance: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to analyze model performance: {str(e)}",
            additional_prompt_content="There was an error analyzing the model performance. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        )


async def get_model_recommendations(
    use_case: str,
    budget_constraint: Optional[str] = None,
    performance_priority: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get model recommendations based on use case and constraints.
    
    Args:
        use_case: Description of the intended use case
        budget_constraint: Budget constraint ('low', 'medium', 'high', 'unlimited')
        performance_priority: Performance priority ('speed', 'quality', 'balanced')
        
    Returns:
        Dictionary containing model recommendations
    """
    try:
        validate_required_params({"use_case": use_case}, ["use_case"])
        
        if not use_case or not isinstance(use_case, str):
            raise OpenRouterToolExecutionError(
                "Invalid use_case parameter",
                additional_prompt_content="Use case must be a non-empty string describing your needs.",
                developer_message="Use case must be a non-empty string",
            )
        
        valid_budgets = ["low", "medium", "high", "unlimited"]
        if budget_constraint and budget_constraint not in valid_budgets:
            raise OpenRouterToolExecutionError(
                "Invalid budget_constraint parameter",
                additional_prompt_content=f"Budget constraint must be one of: {', '.join(valid_budgets)}.",
                developer_message=f"Invalid budget_constraint: {budget_constraint}",
            )
        
        valid_priorities = ["speed", "quality", "balanced"]
        if performance_priority and performance_priority not in valid_priorities:
            raise OpenRouterToolExecutionError(
                "Invalid performance_priority parameter",
                additional_prompt_content=f"Performance priority must be one of: {', '.join(valid_priorities)}.",
                developer_message=f"Invalid performance_priority: {performance_priority}",
            )
        
        client = get_client()
        
        models_response = await client.get("/models")
        all_models = models_response.get("data", [])
        
        recommendations = []
        
        for model in all_models:
            model_id = model.get("id", "")
            pricing = model.get("pricing", {})
            input_cost = pricing.get("input", 0)
            output_cost = pricing.get("output", 0)
            total_cost = input_cost + output_cost
            
            if budget_constraint:
                if budget_constraint == "low" and total_cost > 0.001:
                    continue
                elif budget_constraint == "medium" and total_cost > 0.01:
                    continue
                elif budget_constraint == "high" and total_cost > 0.1:
                    continue
            
            if performance_priority:
                model_name = model_id.lower()
                if performance_priority == "speed" and "gpt-4" in model_name:
                    continue
                elif performance_priority == "quality" and "gpt-3.5" in model_name:
                    continue
            
            recommendations.append({
                "model_id": model_id,
                "name": model.get("name", model_id),
                "description": model.get("description", ""),
                "pricing": {
                    "input_cost_per_1k": input_cost,
                    "output_cost_per_1k": output_cost,
                    "total_cost_per_1k": total_cost,
                },
                "context_length": model.get("context_length", 0),
                "category": model.get("category", ""),
            })
        
        recommendations.sort(key=lambda x: x["pricing"]["total_cost_per_1k"])
        
        recommendations = recommendations[:10]
        
        logger.info(f"Generated {len(recommendations)} model recommendations for use case: {use_case}")
        
        return {
            "success": True,
            "use_case": use_case,
            "budget_constraint": budget_constraint,
            "performance_priority": performance_priority,
            "recommendations": recommendations,
            "total_models_considered": len(all_models),
        }
        
    except OpenRouterToolExecutionError:
        raise
    except Exception as e:
        logger.exception(f"Error getting model recommendations: {e}")
        raise OpenRouterToolExecutionError(
            f"Failed to get model recommendations: {str(e)}",
            additional_prompt_content="There was an error generating model recommendations. Please try again.",
            developer_message=f"Unexpected error: {str(e)}",
        ) 