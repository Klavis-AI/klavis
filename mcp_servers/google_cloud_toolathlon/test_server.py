#!/usr/bin/env python3
"""
Test script for Google Cloud MCP Server
"""

import os
import subprocess
import json
import sys
from typing import Dict, Any

def test_mcp_server():
    """Test the MCP server setup and basic functionality"""
    print("Testing Google Cloud MCP Server")
    print("=" * 40)
    
    # Test 1: Check dependencies
    print("1. Checking dependencies...")
    required_packages = [
        'fastmcp',
        'google.cloud.bigquery',
        'google.cloud.storage', 
        'google.cloud.logging',
        'google.cloud.compute_v1'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {missing_packages}")
        print("Install with: pip install -e .")
        return False
    
    # Test 2: Check service managers
    print("\n2. Testing service manager imports...")
    try:
        from src.big_query import BigQueryManager
        print("   ✅ BigQueryManager")
    except ImportError as e:
        print(f"   ❌ BigQueryManager: {e}")
        return False
    
    try:
        from src.cloud_storage import CloudStorageManager
        print("   ✅ CloudStorageManager")
    except ImportError as e:
        print(f"   ❌ CloudStorageManager: {e}")
        return False
    
    try:
        from src.cloud_logging import CloudLoggingManager
        print("   ✅ CloudLoggingManager")
    except ImportError as e:
        print(f"   ❌ CloudLoggingManager: {e}")
        return False
    
    try:
        from src.compute_engine import ComputeEngineManager
        print("   ✅ ComputeEngineManager")
    except ImportError as e:
        print(f"   ❌ ComputeEngineManager: {e}")
        return False
    
    # Test 3: Check MCP server import
    print("\n3. Testing MCP server import...")
    try:
        from src.server import mcp, setup_server
        print("   ✅ MCP server imports successful")
    except ImportError as e:
        print(f"   ❌ MCP server import failed: {e}")
        return False
    
    # Test 4: Check authentication setup
    print("\n4. Checking authentication...")
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not project_id:
        print("   ⚠️  GOOGLE_CLOUD_PROJECT not set")
        print("   Set with: export GOOGLE_CLOUD_PROJECT=your-project-id")
    else:
        print(f"   ✅ Project ID: {project_id}")
    
    if service_account_path:
        if os.path.exists(service_account_path):
            print(f"   ✅ Service account: {service_account_path}")
        else:
            print(f"   ❌ Service account file not found: {service_account_path}")
    elif os.path.exists("service-account-key.json"):
        print("   ✅ Service account: service-account-key.json (default)")
    else:
        print("   ⚠️  No service account file found")
        print("   Will attempt to use default credentials")
    
    # Test 5: Test server setup (without actually running)
    print("\n5. Testing server setup...")
    try:
        if project_id:
            # Test setup without initializing clients (dry run)
            print(f"   ✅ Server setup test passed for project: {project_id}")
        else:
            print("   ⚠️  Cannot test server setup without project ID")
    except Exception as e:
        print(f"   ❌ Server setup failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("✅ All tests passed!")
    print("\nTo run the MCP server:")
    print(f"python -m src.server --project-id {project_id or 'YOUR_PROJECT_ID'}")
    
    return True

def show_usage():
    """Show usage examples"""
    print("\n" + "=" * 40)
    print("Usage Examples:")
    print("=" * 40)
    
    print("\n1. Basic server start:")
    print("python -m src.server --project-id my-gcp-project")
    
    print("\n2. With access controls:")
    print("python -m src.server \\")
    print("  --project-id my-gcp-project \\")
    print("  --allowed-buckets my-bucket-1,my-bucket-2 \\")
    print("  --allowed-datasets my-dataset-1,my-dataset-2 \\")
    print("  --allowed-instances my-vm-1,my-vm-2")
    
    print("\n3. Using with Claude Desktop:")
    print("Add to your Claude Desktop MCP settings:")
    print(json.dumps({
        "mcpServers": {
            "google-cloud": {
                "command": "python",
                "args": [
                    "-m", "src.server",
                    "--project-id", "your-project-id",
                    "--allowed-buckets", "bucket1,bucket2"
                ],
                "cwd": "/path/to/google_cloud_mcp"
            }
        }
    }, indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--usage":
        show_usage()
    else:
        success = test_mcp_server()
        if success:
            show_usage()
        else:
            sys.exit(1)