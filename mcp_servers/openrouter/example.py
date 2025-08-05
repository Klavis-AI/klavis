#!/usr/bin/env python3
"""
Example usage of OpenRouter MCP Server
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example API key (replace with your actual OpenRouter API key)
EXAMPLE_API_KEY = "your_openrouter_api_key_here"


async def example_list_models():
    """Example: List available models."""
    logger.info("=== Example: List Available Models ===")
    
    from tools.models import list_models
    from tools.base import auth_token_context
    
    token = auth_token_context.set(EXAMPLE_API_KEY)
    try:
        result = await list_models(limit=10)
        logger.info(f"Found {result['total_count']} models")
        
        # Print first few models
        for i, model in enumerate(result['data'][:3]):
            logger.info(f"{i+1}. {model.get('id', 'Unknown')} - {model.get('name', 'No name')}")
            
    finally:
        auth_token_context.reset(token)


async def example_chat_completion():
    """Example: Create a chat completion."""
    logger.info("\n=== Example: Chat Completion ===")
    
    from tools.chat import create_chat_completion
    from tools.base import auth_token_context
    
    token = auth_token_context.set(EXAMPLE_API_KEY)
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a short poem about artificial intelligence."}
        ]
        
        result = await create_chat_completion(
            model="anthropic/claude-3-opus",
            messages=messages,
            max_tokens=150,
            temperature=0.8
        )
        
        if result['success']:
            choices = result['data'].get('choices', [])
            if choices:
                content = choices[0].get('message', {}).get('content', '')
                logger.info(f"AI Response:\n{content}")
                
                usage = result['usage']
                logger.info(f"Token usage: {usage.get('total_tokens', 0)} tokens")
        else:
            logger.error("Chat completion failed")
            
    finally:
        auth_token_context.reset(token)


async def example_model_comparison():
    """Example: Compare different models."""
    logger.info("\n=== Example: Model Comparison ===")
    
    from tools.comparison import compare_models
    from tools.base import auth_token_context
    
    token = auth_token_context.set(EXAMPLE_API_KEY)
    try:
        models = ["anthropic/claude-3-opus", "openai/gpt-4", "meta-llama/llama-3.1-8b-instruct"]
        test_prompt = "Explain the concept of machine learning in one sentence."
        
        result = await compare_models(
            models=models,
            test_prompt=test_prompt,
            max_tokens=50,
            temperature=0.7
        )
        
        if result['success']:
            logger.info(f"Compared {result['comparison_summary']['total_models']} models")
            logger.info(f"Successful tests: {result['comparison_summary']['successful_tests']}")
            
            for model_result in result['results']:
                model = model_result['model']
                success = model_result['success']
                if success:
                    response = model_result['response']
                    tokens = model_result['usage']['total_tokens']
                    logger.info(f"\n{model}: {tokens} tokens")
                    logger.info(f"Response: {response[:100]}...")
                else:
                    logger.error(f"{model}: Failed - {model_result['error']}")
        else:
            logger.error("Model comparison failed")
            
    finally:
        auth_token_context.reset(token)


async def example_cost_estimation():
    """Example: Estimate costs for different models."""
    logger.info("\n=== Example: Cost Estimation ===")
    
    from tools.usage import get_cost_estimate
    from tools.base import auth_token_context
    
    token = auth_token_context.set(EXAMPLE_API_KEY)
    try:
        models = ["anthropic/claude-3-opus", "openai/gpt-4", "meta-llama/llama-3.1-8b-instruct"]
        input_tokens = 1000
        output_tokens = 500
        
        for model in models:
            try:
                result = await get_cost_estimate(
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens
                )
                
                if result['success']:
                    cost = result['cost_breakdown']['total_cost']
                    logger.info(f"{model}: ${cost:.6f} for {input_tokens} input + {output_tokens} output tokens")
                else:
                    logger.error(f"{model}: Failed to estimate cost")
                    
            except Exception as e:
                logger.error(f"{model}: Error - {str(e)}")
                
    finally:
        auth_token_context.reset(token)


async def example_model_recommendations():
    """Example: Get model recommendations."""
    logger.info("\n=== Example: Model Recommendations ===")
    
    from tools.comparison import get_model_recommendations
    from tools.base import auth_token_context
    
    token = auth_token_context.set(EXAMPLE_API_KEY)
    try:
        result = await get_model_recommendations(
            use_case="Building a customer support chatbot that needs to be fast and cost-effective",
            budget_constraint="low",
            performance_priority="speed"
        )
        
        if result['success']:
            logger.info(f"Found {len(result['recommendations'])} recommendations")
            logger.info(f"Use case: {result['use_case']}")
            
            for i, rec in enumerate(result['recommendations'][:3]):
                model_id = rec['model_id']
                cost = rec['pricing']['total_cost_per_1k']
                logger.info(f"{i+1}. {model_id} - ${cost:.6f}/1k tokens")
        else:
            logger.error("Failed to get recommendations")
            
    finally:
        auth_token_context.reset(token)


async def example_usage_tracking():
    """Example: Track usage and get user profile."""
    logger.info("\n=== Example: Usage Tracking ===")
    
    from tools.usage import get_usage, get_user_profile, get_credits
    from tools.base import auth_token_context
    
    token = auth_token_context.set(EXAMPLE_API_KEY)
    try:
        # Get user profile
        profile_result = await get_user_profile()
        if profile_result['success']:
            user_info = profile_result['user_info']
            logger.info(f"User: {user_info.get('name', 'Unknown')}")
            logger.info(f"Email: {user_info.get('email', 'Unknown')}")
            logger.info(f"Plan: {user_info.get('plan', 'Unknown')}")
        
        # Get credits
        credits_result = await get_credits()
        if credits_result['success']:
            total_credits = credits_result['total_credits']
            total_usage = credits_result['total_usage']
            available_credits = credits_result['available_credits']
            logger.info(f"Total credits: {total_credits}")
            logger.info(f"Total usage: {total_usage}")
            logger.info(f"Available credits: {available_credits}")
        
        # Get usage statistics
        usage_result = await get_usage(limit=10)
        if usage_result['success']:
            usage_summary = usage_result['usage_summary']
            logger.info(f"Total requests: {usage_summary.get('total_requests', 0)}")
            logger.info(f"Total tokens: {usage_summary.get('total_tokens', 0)}")
            logger.info(f"Total cost: ${usage_summary.get('total_cost', 0):.6f}")
            
    finally:
        auth_token_context.reset(token)


async def run_examples():
    """Run all examples."""
    logger.info("🚀 OpenRouter MCP Server Examples")
    logger.info("=" * 50)
    
    examples = [
        ("List Models", example_list_models),
        ("Chat Completion", example_chat_completion),
        ("Model Comparison", example_model_comparison),
        ("Cost Estimation", example_cost_estimation),
        ("Model Recommendations", example_model_recommendations),
        ("Usage Tracking", example_usage_tracking),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
            logger.info(f"✅ {name} completed successfully")
        except Exception as e:
            logger.error(f"❌ {name} failed: {str(e)}")
        
        logger.info("-" * 50)
    
    logger.info("🎉 All examples completed!")


if __name__ == "__main__":
    # Check if API key is set
    if EXAMPLE_API_KEY == "your_openrouter_api_key_here":
        logger.error("⚠️  Please set your OpenRouter API key in the EXAMPLE_API_KEY variable")
        logger.info("You can get an API key from: https://openrouter.ai")
        exit(1)
    
    # Run examples
    asyncio.run(run_examples()) 