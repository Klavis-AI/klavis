#!/usr/bin/env python3
"""
Test script for Zoom MCP Server
This script tests the basic functionality of the Zoom MCP server tools.
"""

import asyncio
import json
import httpx
from typing import Dict, Any

# Test configuration - Replace with your actual Zoom OAuth access token
TEST_ACCESS_TOKEN = ""

async def test_zoom_api_direct():
    """Test Zoom API directly to verify OAuth access token."""
    print("Testing Zoom OAuth Access Token...")
    print("=" * 50)
    
    if TEST_ACCESS_TOKEN == "your_zoom_oauth_access_token_here":
        print("⚠️  Please update TEST_ACCESS_TOKEN with your actual Zoom OAuth access token")
        print("   You can get this by completing the OAuth flow with Zoom")
        return False
    
    try:
        # Test the access token by making a direct API call
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Test API call to get user info
            response = await client.get(
                "https://api.zoom.us/v2/users/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Access token valid! Connected as: {user_data.get('first_name', 'Unknown')} {user_data.get('last_name', 'Unknown')}")
                print(f"   Email: {user_data.get('email', 'Unknown')}")
                print(f"   Account ID: {user_data.get('account_id', 'Unknown')}")
                return True
            else:
                print(f"❌ API call failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing access token: {e}")
        return False

async def test_mcp_server_endpoints():
    """Test the MCP server endpoints."""
    print("\nTesting MCP Server Endpoints...")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test SSE endpoint
    print("\n1. Testing SSE endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/sse",
                headers={"x-zoom-access-token": TEST_ACCESS_TOKEN}
            )
            if response.status_code == 200:
                print("✅ SSE endpoint accessible")
            else:
                print(f"❌ SSE endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ SSE endpoint error: {e}")
    
    # Test StreamableHTTP endpoint
    print("\n2. Testing StreamableHTTP endpoint...")
    try:
        test_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/mcp",
                headers={"x-zoom-access-token": TEST_ACCESS_TOKEN, "Content-Type": "application/json"},
                json=test_request
            )
            
            if response.status_code == 200:
                print("✅ StreamableHTTP endpoint accessible")
                try:
                    result = response.json()
                    print(f"   Response: {json.dumps(result, indent=2)}")
                except:
                    print(f"   Raw response: {response.text}")
            else:
                print(f"❌ StreamableHTTP endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ StreamableHTTP endpoint error: {e}")

async def test_zoom_api_operations():
    """Test various Zoom API operations using the access token."""
    print("\nTesting Zoom API Operations...")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Test 1: Get user information
            print("\n1. Testing user information...")
            response = await client.get("https://api.zoom.us/v2/users/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ User info retrieved: {user_data.get('first_name')} {user_data.get('last_name')}")
            else:
                print(f"❌ Failed to get user info: {response.status_code}")
            
            # Test 2: List meetings
            print("\n2. Testing meeting list...")
            response = await client.get("https://api.zoom.us/v2/users/me/meetings", headers=headers)
            if response.status_code == 200:
                meetings_data = response.json()
                meeting_count = len(meetings_data.get('meetings', []))
                print(f"✅ Meetings retrieved: {meeting_count} meetings found")
            else:
                print(f"❌ Failed to get meetings: {response.status_code}")
            
            # Test 3: List users (if admin)
            print("\n3. Testing user list...")
            response = await client.get("https://api.zoom.us/v2/users", headers=headers)
            if response.status_code == 200:
                users_data = response.json()
                user_count = len(users_data.get('users', []))
                print(f"✅ Users retrieved: {user_count} users found")
            else:
                print(f"❌ Failed to get users: {response.status_code} (may not have admin permissions)")
                
    except Exception as e:
        print(f"❌ Error testing API operations: {e}")

async def main():
    """Main test function."""
    print("🚀 Zoom MCP Server Test Suite (OAuth)")
    print("=" * 60)
    
    # First test the access token
    token_valid = await test_zoom_api_direct()
    
    if not token_valid:
        print("\n⚠️  Please fix your OAuth access token before continuing with other tests")
        print("\nTo get an OAuth access token:")
        print("1. Create a Zoom App in the Zoom App Marketplace")
        print("2. Configure OAuth settings with appropriate scopes")
        print("3. Complete the OAuth flow to get an access token")
        print("4. Update TEST_ACCESS_TOKEN in this script")
        return
    
    # Test MCP server endpoints
    await test_mcp_server_endpoints()
    
    # Test Zoom API operations
    await test_zoom_api_operations()
    
    print("\n✅ Test suite completed!")
    print("\nTo run the server:")
    print("  python server.py")
    print("\nTo test with real API calls:")
    print("  python test_server.py")

if __name__ == "__main__":
    asyncio.run(main())
