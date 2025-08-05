#!/usr/bin/env python3
"""
Test script for OpenRouter MCP Server
"""

import asyncio
import json
import os
import logging
import dotenv
from typing import Dict, Any

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "http://localhost:8000"


async def test_list_models() -> Dict[str, Any]:
    """Test the list_models tool."""
    logger.info("Testing list_models...")
        
    from tools.models import list_models
    from tools.base import auth_token_context
    
    token = auth_token_context.set(TEST_API_KEY)
    try:
        result = await list_models(limit=5)
        logger.info(f"List models result: {json.dumps(result, indent=2)}")
        return result
    finally:
        auth_token_context.reset(token)

async def test_chat_completion() -> Dict[str, Any]:
    """Test the create_chat_completion tool."""
    logger.info("Testing create_chat_completion...")
    
    from tools.chat import create_chat_completion
    from tools.base import auth_token_context
    
    token = auth_token_context.set(TEST_API_KEY)
    try:
        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        result = await create_chat_completion(
            model="anthropic/claude-3-opus",
            messages=messages,
            max_tokens=50,
            temperature=0.7
        )
        logger.info(f"Chat completion result: {json.dumps(result, indent=2)}")
        return result
    finally:
        auth_token_context.reset(token)


async def test_user_profile() -> Dict[str, Any]:
    """Test the get_user_profile tool."""
    logger.info("Testing get_user_profile...")
    
    from tools.usage import get_user_profile
    from tools.base import auth_token_context
    
    token = auth_token_context.set(TEST_API_KEY)
    try:
        result = await get_user_profile()
        logger.info(f"User profile result: {json.dumps(result, indent=2)}")
        return result
    finally:
        auth_token_context.reset(token)


async def test_get_credits() -> Dict[str, Any]:
    """Test the get_credits tool."""
    logger.info("Testing get_credits...")
    
    from tools.usage import get_credits
    from tools.base import auth_token_context
    
    token = auth_token_context.set(TEST_API_KEY)
    try:
        result = await get_credits()
        logger.info(f"Credits result: {json.dumps(result, indent=2)}")
        return result
    finally:
        auth_token_context.reset(token)


async def test_model_comparison() -> Dict[str, Any]:
    """Test the compare_models tool."""
    logger.info("Testing compare_models...")
    
    from tools.comparison import compare_models
    from tools.base import auth_token_context
    
    token = auth_token_context.set(TEST_API_KEY)
    try:
        models = ["anthropic/claude-3-opus", "openai/gpt-4"]
        result = await compare_models(
            models=models,
            test_prompt="Explain quantum computing in simple terms",
            max_tokens=100,
            temperature=0.7
        )
        logger.info(f"Model comparison result: {json.dumps(result, indent=2)}")
        return result
    finally:
        auth_token_context.reset(token)


async def test_model_recommendations() -> Dict[str, Any]:
    """Test the get_model_recommendations tool."""
    logger.info("Testing get_model_recommendations...")
    
    from tools.comparison import get_model_recommendations
    from tools.base import auth_token_context
    
    token = auth_token_context.set(TEST_API_KEY)
    try:
        result = await get_model_recommendations(
            use_case="Text generation for a chatbot",
            budget_constraint="medium",
            performance_priority="balanced"
        )
        logger.info(f"Model recommendations result: {json.dumps(result, indent=2)}")
        return result
    finally:
        auth_token_context.reset(token)


async def run_all_tests():
    """Run all tests."""
    logger.info("Starting OpenRouter MCP Server tests...")
    
    tests = [
        ("List Models", test_list_models),
        ("Chat Completion", test_chat_completion),
        ("User Profile", test_user_profile),
        ("Get Credits", test_get_credits),
        ("Model Comparison", test_model_comparison),
        ("Model Recommendations", test_model_recommendations),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running test: {test_name}")
            logger.info(f"{'='*50}")
            
            result = await test_func()
            results[test_name] = {"status": "PASSED", "result": result}
            
        except Exception as e:
            logger.error(f"Test {test_name} FAILED: {str(e)}")
            results[test_name] = {"status": "FAILED", "error": str(e)}
    
    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = result["status"]
        if status == "PASSED":
            passed += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            failed += 1
            logger.error(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
    
    logger.info(f"\nTotal: {passed + failed}, Passed: {passed}, Failed: {failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed!")
    else:
        logger.error(f"💥 {failed} test(s) failed!")
    
    return results


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests()) 