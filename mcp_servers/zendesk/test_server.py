#!/usr/bin/env python3
"""
Test script for the Zendesk MCP Server
"""

import asyncio
import json
import logging
import os
import dotenv
from typing import Dict, Any

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load test credentials from environment
TEST_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
TEST_EMAIL = os.getenv("ZENDESK_EMAIL")
TEST_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN", "your-subdomain")

async def test_comprehensive_ticket_tools() -> Dict[str, Any]:
    """Test all ticket management tools comprehensively."""
    logger.info("Testing comprehensive ticket management tools...")
    
    from tools.tickets import (
        list_tickets, get_ticket, create_ticket, update_ticket, delete_ticket,
        add_ticket_comment, get_ticket_comments, assign_ticket, change_ticket_status,
        search_tickets
    )
    from tools.base import auth_token_context, auth_email_context
    
    # Set authentication context
    token = auth_token_context.set(TEST_API_TOKEN)
    email = auth_email_context.set(TEST_EMAIL)
    
    try:
        results = {}
        
        # Test list_tickets
        logger.info("Testing list_tickets...")
        list_result = await list_tickets(status="open", per_page=5)
        results["list_tickets"] = list_result
        
        # Test search_tickets
        logger.info("Testing search_tickets...")
        search_result = await search_tickets("status:open", per_page=3)
        results["search_tickets"] = search_result
        
        # Test create_ticket (create a test ticket)
        logger.info("Testing create_ticket...")
        create_result = await create_ticket(
            subject="Test Ticket for Testing",
            description="This is a test ticket created during testing",
            priority="normal",
            tags=["test", "automated"]
        )
        results["create_ticket"] = create_result
        
        if create_result.get("ticket"):
            test_ticket_id = create_result["ticket"]["id"]
            logger.info(f"Created test ticket with ID: {test_ticket_id}")
            
            # Wait a moment for Zendesk to process the creation
            await asyncio.sleep(2)
            
            # Test get_ticket with retry logic
            logger.info("Testing get_ticket...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    get_result = await get_ticket(test_ticket_id)
                    results["get_ticket"] = get_result
                    break
                except Exception as e:
                    if "RecordNotFound" in str(e) and attempt < max_retries - 1:
                        logger.info(f"Record not found, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(2)
                    else:
                        raise
            
            # Test update_ticket
            logger.info("Testing update_ticket...")
            update_result = await update_ticket(
                test_ticket_id,
                subject="Updated Test Ticket",
                priority="high",
                tags=["test", "automated", "updated"]
            )
            results["update_ticket"] = update_result
            
            # Test add_ticket_comment
            logger.info("Testing add_ticket_comment...")
            comment_result = await add_ticket_comment(
                test_ticket_id,
                "This is a test comment added during testing",
                public=True
            )
            results["add_ticket_comment"] = comment_result
            
            # Test get_ticket_comments
            logger.info("Testing get_ticket_comments...")
            comments_result = await get_ticket_comments(test_ticket_id)
            results["get_ticket_comments"] = comments_result
            
            # Test assign_ticket (assign to current user if possible)
            logger.info("Testing assign_ticket...")
            try:
                assign_result = await assign_ticket(test_ticket_id, 1)  # Assuming user ID 1 exists
                results["assign_ticket"] = assign_result
            except Exception as e:
                logger.warning(f"assign_ticket failed (expected if user ID 1 doesn't exist): {e}")
                results["assign_ticket"] = {"error": str(e)}
            
            # Test change_ticket_status
            logger.info("Testing change_ticket_status...")
            status_result = await change_ticket_status(test_ticket_id, "pending")
            results["change_ticket_status"] = status_result
            
            # Test delete_ticket (clean up test ticket)
            logger.info("Testing delete_ticket...")
            delete_result = await delete_ticket(test_ticket_id)
            results["delete_ticket"] = delete_result
        
        logger.info(f"Results for ticket management tools: {results}")
        logger.info("✓ Comprehensive ticket management tools test completed")
        return results
        
    finally:
        auth_token_context.reset(token)
        auth_email_context.reset(email)


async def test_comprehensive_user_tools() -> Dict[str, Any]:
    """Test all user management tools comprehensively."""
    logger.info("Testing comprehensive user management tools...")
    
    from tools.users import (
        list_users, get_user, create_user, update_user, delete_user, search_users,
        get_user_tickets, get_user_organizations, suspend_user, reactivate_user, get_current_user
    )
    from tools.base import auth_token_context, auth_email_context
    
    # Set authentication context
    token = auth_token_context.set(TEST_API_TOKEN)
    email = auth_email_context.set(TEST_EMAIL)
    
    try:
        results = {}
        
        # Test get_current_user
        logger.info("Testing get_current_user...")
        current_user_result = await get_current_user()
        results["get_current_user"] = current_user_result
        
        # Test list_users
        logger.info("Testing list_users...")
        list_result = await list_users(role="agent", per_page=5)
        results["list_users"] = list_result
        
        # Test search_users
        logger.info("Testing search_users...")
        search_result = await search_users("role:agent", per_page=3)
        results["search_users"] = search_result
        
        # Test create_user (create a test user)
        logger.info("Testing create_user...")
        test_email = f"test.user.{int(asyncio.get_event_loop().time())}@example.com"
        create_result = await create_user(
            name="Test User",
            email=test_email,
            role="end-user",
            tags=["test", "automated"]
        )
        results["create_user"] = create_result
        
        if create_result.get("user"):
            test_user_id = create_result["user"]["id"]
            logger.info(f"Created test user with ID: {test_user_id}")
            
            # Wait a moment for Zendesk to process the creation
            await asyncio.sleep(2)
            
            # Test get_user with retry logic
            logger.info("Testing get_user...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    get_result = await get_user(test_user_id)
                    results["get_user"] = get_result
                    break
                except Exception as e:
                    if "RecordNotFound" in str(e) and attempt < max_retries - 1:
                        logger.info(f"Record not found, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(2)
                    else:
                        raise
            
            # Test update_user
            logger.info("Testing update_user...")
            update_result = await update_user(
                test_user_id,
                name="Updated Test User",
                tags=["test", "automated", "updated"]
            )
            results["update_user"] = update_result
            
            # Test get_user_organizations
            logger.info("Testing get_user_organizations...")
            orgs_result = await get_user_organizations(test_user_id)
            results["get_user_organizations"] = orgs_result
            
            # Test get_user_tickets
            logger.info("Testing get_user_tickets...")
            tickets_result = await get_user_tickets(test_user_id)
            results["get_user_tickets"] = tickets_result
            
            # Test suspend_user
            logger.info("Testing suspend_user...")
            suspend_result = await suspend_user(test_user_id)
            results["suspend_user"] = suspend_result
            
            # Test reactivate_user
            logger.info("Testing reactivate_user...")
            reactivate_result = await reactivate_user(test_user_id)
            results["reactivate_user"] = reactivate_result
            
            # Test delete_user (clean up test user)
            logger.info("Testing delete_user...")
            delete_result = await delete_user(test_user_id)
            results["delete_user"] = delete_result

        logger.info(f"Results for user management tools: {results}")
        logger.info("✓ Comprehensive user management tools test completed")
        return results
        
    finally:
        auth_token_context.reset(token)
        auth_email_context.reset(email)

async def test_comprehensive_organization_tools() -> Dict[str, Any]:
    """Test all organization management tools comprehensively."""
    logger.info("Testing comprehensive organization management tools...")
    
    from tools.organizations import (
        list_organizations, get_organization, create_organization, update_organization,
        delete_organization, search_organizations, get_organization_tickets, get_organization_users
    )
    from tools.base import auth_token_context, auth_email_context
    
    # Set authentication context
    token = auth_token_context.set(TEST_API_TOKEN)
    email = auth_email_context.set(TEST_EMAIL)
    
    try:
        results = {}
        
        # Test list_organizations
        logger.info("Testing list_organizations...")
        list_result = await list_organizations(per_page=5)
        results["list_organizations"] = list_result
        
        # Test search_organizations
        logger.info("Testing search_organizations...")
        search_result = await search_organizations("name:*", per_page=3)
        results["search_organizations"] = search_result
        
        # Test create_organization (create a test organization)
        logger.info("Testing create_organization...")
        test_org_name = f"Test Org {int(asyncio.get_event_loop().time())}"
        create_result = await create_organization(
            name=test_org_name,
            domain="test.example.com",
            tags=["test", "automated"]
        )
        results["create_organization"] = create_result
        
        if create_result.get("organization"):
            test_org_id = create_result["organization"]["id"]
            logger.info(f"Created test organization with ID: {test_org_id}")
            
            # Wait a moment for Zendesk to process the creation
            await asyncio.sleep(2)
            
            # Test get_organization with retry logic
            logger.info("Testing get_organization...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    get_result = await get_organization(test_org_id)
                    results["get_organization"] = get_result
                    break
                except Exception as e:
                    if "RecordNotFound" in str(e) and attempt < max_retries - 1:
                        logger.info(f"Record not found, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(2)
                    else:
                        raise
            
            # Test update_organization
            logger.info("Testing update_organization...")
            update_result = await update_organization(
                test_org_id,
                name=f"Updated {test_org_name}",
                tags=["test", "automated", "updated"]
            )
            results["update_organization"] = update_result
            
            # Test get_organization_users
            logger.info("Testing get_organization_users...")
            users_result = await get_organization_users(test_org_id)
            results["get_organization_users"] = users_result
            
            # Test get_organization_tickets
            logger.info("Testing get_organization_tickets...")
            tickets_result = await get_organization_tickets(test_org_id)
            results["get_organization_tickets"] = tickets_result
            
            # Test delete_organization (clean up test organization)
            logger.info("Testing delete_organization...")
            delete_result = await delete_organization(test_org_id)
            results["delete_organization"] = delete_result
            
        logger.info(f"Results for organization management tools: {results}")
        logger.info("✓ Comprehensive organization management tools test completed")
        return results
        
    finally:
        auth_token_context.reset(token)
        auth_email_context.reset(email)

async def test_error_handling() -> Dict[str, Any]:
    """Test error handling."""
    logger.info("Testing error handling...")
    
    from tools.base import ZendeskToolExecutionError, validate_pagination_params
    
    # Test pagination validation
    try:
        validate_pagination_params(page=0)
        assert False, "Should have raised an error for page 0"
    except ZendeskToolExecutionError:
        logger.info("✓ pagination validation test passed")
    
    try:
        validate_pagination_params(per_page=150)
        assert False, "Should have raised an error for per_page > 100"
    except ZendeskToolExecutionError:
        logger.info("✓ per_page validation test passed")

    logger.info("✓ Error handling test completed")
    return {"status": "passed"}

async def test_authentication_context() -> Dict[str, Any]:
    """Test authentication context management."""
    logger.info("Testing authentication context...")
    
    from tools.base import auth_token_context, auth_email_context
    
    # Test context setting and resetting
    original_token = auth_token_context.get()
    original_email = auth_email_context.get()
    
    token = auth_token_context.set("test-token")
    email = auth_email_context.set("test@example.com")
    
    assert auth_token_context.get() == "test-token"
    assert auth_email_context.get() == "test@example.com"
    
    auth_token_context.reset(token)
    auth_email_context.reset(email)
    
    assert auth_token_context.get() == original_token
    assert auth_email_context.get() == original_email
    
    logger.info("✓ Authentication context test passed")
    return {"status": "passed"}

async def run_all_tests():
    """Run all tests."""
    logger.info("Starting Zendesk MCP Server tests...")
    
    # Check if we have the required credentials
    if not TEST_API_TOKEN or not TEST_EMAIL:
        logger.error("❌ Missing required environment variables:")
        logger.error("   - ZENDESK_API_TOKEN")
        logger.error("   - ZENDESK_EMAIL")
        logger.error("   - ZENDESK_SUBDOMAIN (optional, defaults to 'your-subdomain')")
        logger.error("\nPlease set these variables and try again.")
        return {"status": "failed", "error": "Missing credentials"}
    
    tests = [
        ("Authentication Context", test_authentication_context),
        ("Error Handling", test_error_handling),
        ("Comprehensive Ticket Management", test_comprehensive_ticket_tools),
        ("Comprehensive User Management", test_comprehensive_user_tools),
        ("Comprehensive Organization Management", test_comprehensive_organization_tools),
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
