#!/usr/bin/env python3
"""
Test Reddit MCP Server with Klavis AI integration
"""

import os
import json
import time
import subprocess
import signal
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_reddit_server():
    """Start the Reddit MCP server in background."""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_py_path = os.path.join(script_dir, "main.py")
        
        # Check if main.py exists
        if not os.path.exists(main_py_path):
            print(f"main.py not found at: {main_py_path}")
            return None
        
        # Debug the directory structure
        print(f"Script directory: {script_dir}")
        parent_dir = os.path.dirname(os.path.dirname(script_dir))  # Move up two levels to 'klavis'
        print(f"Parent directory: {parent_dir}")
        venv_python = os.path.join(parent_dir, "venv", "Scripts", "python.exe")
        print(f"Checking Python at: {venv_python}")
        
        if not os.path.exists(venv_python):
            print(f"Virtual environment Python not found at: {venv_python}")
            return None
        
        # Start server process from the correct directory
        process = subprocess.Popen(
            [venv_python, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=script_dir  # Set working directory to where main.py is located
        )
        
        # Wait a moment for server to start
        time.sleep(5)  # Increased from 3 to 5 seconds for reliability
        
        # Check if process is still running
        if process.poll() is None:
            print("Reddit MCP server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"Server failed to start:")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None

def test_klavis_integration():
    """Test integration with Klavis AI against a locally running MCP server."""
    print("🧪 Testing Klavis AI Integration...")
    print("=" * 40)

    # Import SDK
    try:
        from klavis import Klavis
        print("Klavis AI SDK available")
    except ImportError:
        print("Klavis AI SDK not installed")
        print("   Install with: pip install klavis")
        return False

    # API key
    klavis_api_key = os.getenv("KLAVIS_API_KEY")
    if not klavis_api_key:
        print("KLAVIS_API_KEY not found in .env")
        print("   Get your API key from: https://www.klavis.ai/home/api-keys")
        return False

    # Your local MCP endpoint (FastAPI transport), note the /mcp/ suffix
    server_url = os.getenv("REDDIT_MCP_URL", "http://127.0.0.1:8000/mcp/")

    try:
        # Init client
        klavis_client = Klavis(api_key=klavis_api_key)
        print("Klavis client initialized")

        # 1) List tools directly from the running server
        print(f"🔎 Listing tools from {server_url} ...")
        tools = klavis_client.mcp_server.list_tools(server_url=server_url, format="openai")

        tool_names = [t["function"]["name"] for t in tools.tools]

        print(f"Retrieved {len(tool_names)} tools: {', '.join(tool_names) or '—'}")
        if "search_subreddits" not in tool_names:
            print(" 'search_subreddits' not found; available tools differ from expectations.")
            # continue anyway

        # 2) Call a real tool
        print("\n Calling tool: search_subreddits ...")
        result = klavis_client.mcp_server.call_tools(
            server_url=server_url,
            tool_name="search_subreddits",
            tool_args={"query": "python"}
        )

        # 3) Show result
        print("Tool call returned:")
        if isinstance(result, str):
            try:
                print(json.dumps(json.loads(result), indent=2))
            except Exception:
                print(result)
        else:
            print(json.dumps(result, indent=2))

        return True

    except Exception as e:
        print(f"Klavis integration test failed: {e}")
        # If the SDK attached a response, show it
        if getattr(e, "response", None) is not None:
            try:
                print("Error response:", e.response.text)
            except Exception:
                pass
        return False

def main():
    """Run complete integration test."""
    print("Reddit MCP Server - Complete Integration Test")
    print("=" * 60)
    
    # Start the Reddit server
    print("Starting Reddit MCP server...")
    server_process = start_reddit_server()
    
    if not server_process:
        print("Failed to start server. Cannot proceed with integration tests.")
        return False
    
    try:
        # Test Klavis integration
        success = test_klavis_integration()
        
        if success:
            print("\nComplete integration test successful!")
            print("\nYour Reddit MCP server is fully functional and ready for production use.")
        else:
            print("\nIntegration test had some issues.")
            print("Server is running but Klavis integration needs attention.")
        
        return success
        
    finally:
        # Clean up: stop the server
        if server_process:
            print("\nStopping Reddit MCP server...")
            server_process.terminate()
            server_process.wait(timeout=5)
            print("Server stopped")

if __name__ == "__main__":
    # Check for required environment variables
    required_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        print("Please check your .env file")
        exit(1)
    
    success = main()
    exit(0 if success else 1)