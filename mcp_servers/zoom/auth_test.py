#!/usr/bin/env python3
"""
Test script for Zoom Device Flow OAuth Authentication
This script demonstrates how to use the device flow authentication.
"""

import asyncio
import json
from tools.auth import authenticate_with_device_flow

async def test_device_flow_auth():
    """Test the device flow authentication."""
    print("🚀 Testing Zoom Device Flow OAuth Authentication")
    print("=" * 60)
    
    try:
        # You can optionally provide your Zoom App Client ID
        # client_id = "your_zoom_client_id_here"
        client_id = None  # Will use default from config
        
        print("Starting device flow authentication...")
        access_token = await authenticate_with_device_flow(client_id)
        
        print(f"\n✅ Authentication successful!")
        print(f"Access Token: {access_token[:20]}...{access_token[-20:]}")
        print(f"Token Length: {len(access_token)} characters")
        
        # Save token to file for testing
        with open("zoom_access_token.txt", "w") as f:
            f.write(access_token)
        print("Token saved to zoom_access_token.txt")
        
        return access_token
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

async def main():
    """Main function."""
    print("This script will help you authenticate with Zoom using device flow OAuth.")
    print("You'll need to visit a URL and enter a code to complete authentication.")
    print()
    
    # Check if user wants to proceed
    response = input("Do you want to proceed with authentication? (y/n): ")
    if response.lower() != 'y':
        print("Authentication cancelled.")
        return
    
    token = await test_device_flow_auth()
    
    if token:
        print("\n🎉 Authentication completed successfully!")
        print("You can now use this access token with the Zoom MCP server.")
        print("\nTo use with the MCP server:")
        print("1. Start the server: python server.py")
        print("2. Use the access token in your MCP client headers")
        print("3. Or use the zoom_authenticate_device_flow tool directly")
    else:
        print("\n❌ Authentication failed. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
