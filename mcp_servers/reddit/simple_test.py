#!/usr/bin/env python3
"""
Simple test script for Reddit MCP Server
Run this from the mcp_servers/reddit directory
"""

import os
import sys
import json
from dotenv import load_dotenv

def main():
    print("🧪 Simple Reddit MCP Server Test")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("❌ main.py not found!")
        print("Please run this script from the mcp_servers/reddit directory")
        print("Current directory:", os.getcwd())
        return False
    
    # Load environment variables
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please make sure you have a .env file with your Reddit credentials")
        return False
    
    load_dotenv()
    print("✅ Environment file loaded")
    
    # Test 1: Check required environment variables
    required_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("your_"):
            missing_vars.append(var)
        else:
            # Show masked version
            masked_value = value[:4] + "*" * (len(value) - 4)
            print(f"✅ {var}: {masked_value}")
    
    if missing_vars:
        print(f"❌ Missing or unconfigured variables: {missing_vars}")
        return False
    
    # Test 2: Import and test basic functionality
    try:
        print("\n🔧 Testing imports...")
        from main import RedditConfig, RedditClient
        print("✅ Successfully imported Reddit components")
        
        # Test configuration
        config = RedditConfig()
        print("✅ Configuration created successfully")
        
        # Test client creation
        client = RedditClient(config)
        print("✅ Reddit client created successfully")
        
    except Exception as e:
        print(f"❌ Import/setup failed: {e}")
        return False
    
    # Test 3: Test a simple API call
    try:
        print("\n🌐 Testing Reddit API connection...")
        
        # Test getting subreddit posts
        posts = client.get_subreddit_posts("test", limit=2)
        if posts:
            print(f"✅ API call successful - retrieved {len(posts)} posts")
            print(f"   Sample post: '{posts[0]['title'][:30]}...'")
        else:
            print("⚠️  API call returned no posts (might be normal for r/test)")
        
        # Test subreddit info
        info = client.get_subreddit_info("python")
        if info and 'name' in info:
            print(f"✅ Subreddit info: r/{info['name']} ({info.get('subscribers', 'N/A')} subscribers)")
        else:
            print("⚠️  Could not get subreddit info")
        
    except Exception as e:
        print(f"❌ Reddit API test failed: {e}")
        print("   This might be due to:")
        print("   - Incorrect Reddit credentials")
        print("   - Reddit API being temporarily unavailable")
        print("   - Network connectivity issues")
        return False
    
    # Test 4: Test MCP server components
    try:
        print("\n⚙️  Testing MCP server components...")
        
        # Import server components
        from main import server
        print("✅ MCP server imported successfully")
        
        # This is a basic test - for full MCP testing, we'd need to run async functions
        print("✅ MCP server components appear to be working")
        
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False
    
    print("\n🎉 All basic tests passed!")
    print("\nNext steps:")
    print("1. Start the server: python main.py")
    print("2. In another terminal, test with curl or a client")
    print("3. Or integrate with Klavis AI")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("- Make sure you're in the mcp_servers/reddit directory")
        print("- Check that your .env file has correct Reddit credentials")
        print("- Verify your Reddit app is configured as 'script' type")
        print("- Try: pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("\n✅ Your Reddit MCP server is ready to use!")
        sys.exit(0)