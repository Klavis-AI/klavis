#!/usr/bin/env python

import os
from pprint import pprint

from klavis.api.mcp_server_api import McpServerApi
from klavis.api_client import ApiClient, Configuration
from klavis.models.create_server_request import CreateServerRequest
from klavis.models.call_tool_request import CallToolRequest
from klavis.models.set_auth_token_request import SetAuthTokenRequest
from klavis.models.server_name import ServerName

def main():
    # Setup configuration
    api_key = "UKVQ2UfFVH1Ndyw2eROnFRzNEeRtKSuOieV42ZXwxjE="
    config = Configuration(
        api_key=api_key,
    )
    
    # Create API client
    api_client = ApiClient(config)
    mcp_api = McpServerApi(api_client)
    
    # Example 1: Get all MCP servers
    # print("\n--- Getting all MCP servers ---")
    # try:
    #     all_servers = mcp_api.get_all_mcp_servers()
    #     pprint(all_servers.to_dict())
    # except Exception as e:
    #     print(f"Error getting servers: {e}")
    
    # # Example 2: Get tools for a specific server
    # print("\n--- Getting tools for a server ---")
    # try:
    #     server_name = ServerName.GITHUB
    #     tools = mcp_api.get_server_tools(server_name)
    #     pprint(tools.to_dict())
    # except Exception as e:
    #     print(f"Error getting tools: {e}")
    
    # Example 3: Create a server instance
    print("\n--- Creating a server instance ---")
    try:
        create_request = CreateServerRequest(
            server_name=ServerName.GITHUB,
            user_id="test_user_123",
            platform_name="test_platform_123"
        )
        instance = mcp_api.create_server_instance(create_request)
        instance_id = instance.instance_id
        server_url = instance.server_url
        pprint(instance.to_dict())
        
        # Example 4: Get details of the created instance
        print("\n--- Getting instance details ---")
        instance_details = mcp_api.get_server_instance(instance_id)
        pprint(instance_details.to_dict())
        
        # Example 5: Set auth token for the instance
        # print("\n--- Setting auth token ---")
        # auth_request = SetAuthTokenRequest(
        #     instance_id=instance_id,
        #     auth_token="github_pat_example_token",
        # )
        # auth_result = mcp_api.set_instance_auth_token(auth_request)
        # pprint(auth_result.to_dict())
        
        # Example 6: List tools available on the server
        # print("\n--- Listing tools on server ---")
        # if server_url:
        #     tools_list = mcp_api.list_server_tools(server_url)
        #     pprint(tools_list.to_dict())
        
        # # Example 7: Call a tool on the server
        print("\n--- Calling a tool ---")
        call_request = CallToolRequest(
            server_url=server_url,
            tool_name="github_search_repositories",
            tool_args={"query": "python"}
        )
        tool_result = mcp_api.call_server_tool(call_request)
        pprint(tool_result.to_dict())
        
        # Example 8: Delete authentication data
        print("\n--- Deleting authentication data ---")
        delete_auth_result = mcp_api.delete_instance_auth(instance_id)
        pprint(delete_auth_result.to_dict())
        
        # Example 9: Delete the instance
        print("\n--- Deleting instance ---")
        delete_result = mcp_api.delete_server_instance(instance_id)
        pprint(delete_result.to_dict())
        
    except Exception as e:
        print(f"Error in API operations: {e}")

if __name__ == "__main__":
    main() 