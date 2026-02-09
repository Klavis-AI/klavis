#!/usr/bin/env python3
"""
Google Cloud MCP Server - Main entry point for testing
"""

import os
import sys
import json
from src.server import main as run_mcp_server

def main():
    """Demo script for Google Cloud MCP Server"""
    print("Google Cloud MCP Server")
    print("=" * 50)
    
    # Check for required environment variables
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not project_id:
        print("❌ Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        print("   Please set it to your Google Cloud Project ID")
        sys.exit(1)
    
    print(f"✅ Project ID: {project_id}")
    
    if service_account_path and os.path.exists(service_account_path):
        print(f"✅ Service Account: {service_account_path}")
    elif os.path.exists("service-account-key.json"):
        print("✅ Service Account: service-account-key.json (default)")
    else:
        print("⚠️  No service account file found, will use default credentials")
    
    print("\nTo run the MCP server:")
    print("=" * 30)
    print("python -m src.server --project-id YOUR_PROJECT_ID")
    print("\nWith access controls:")
    print("python -m src.server \\")
    print("  --project-id YOUR_PROJECT_ID \\")
    print("  --allowed-buckets bucket1,bucket2 \\")
    print("  --allowed-datasets dataset1,dataset2 \\")
    print("  --allowed-instances instance1,instance2")
    
    print("\nAvailable MCP tools:")
    print("=" * 20)
    tools = [
        "bigquery_run_query - Execute BigQuery SQL queries",
        "bigquery_list_datasets - List BigQuery datasets", 
        "bigquery_create_dataset - Create new BigQuery dataset",
        "storage_list_buckets - List Cloud Storage buckets",
        "storage_create_bucket - Create new storage bucket",
        "storage_list_objects - List objects in a bucket",
        "logging_write_log - Write log entries",
        "logging_read_logs - Read recent log entries",
        "compute_list_instances - List VM instances",
        "compute_create_instance - Create new VM instance",
        "compute_delete_instance - Delete VM instance"
    ]
    
    for tool in tools:
        print(f"• {tool}")
    
    print(f"\n🚀 Ready to start MCP server for project: {project_id}")

if __name__ == "__main__":
    main()
