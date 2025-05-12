# Klavis AI Python SDK

[![PyPI version](https://badge.fury.io/py/klavis.svg)](https://badge.fury.io/py/klavis)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Klavis AI - Open Source MCP Integrations for AI Applications. This Python package provides a convenient way to interact with the Klavis AI API (https://www.klavis.ai).

## Installation

You can install the Klavis AI Python SDK using pip:

```bash
pip install klavis
```

## Getting Started

To use the SDK, you need to obtain an API key from Klavis AI.

Here's a basic example of how to configure the client and make an API call:

```python
import os
from pprint import pprint

from klavis import ApiClient, Configuration
from klavis.api import McpServerApi
from klavis.models import CreateServerRequest, ServerName, CallToolRequest

# Replace 'YOUR_API_KEY' with your actual Klavis API key
# You can also set the KLAVIS_API_KEY environment variable
api_key = os.environ.get("KLAVIS_API_KEY", "YOUR_API_KEY") 
if api_key == "YOUR_API_KEY":
    print("Warning: API Key not configured. Please set the KLAVIS_API_KEY environment variable or replace 'YOUR_API_KEY'.")
    # exit(1) # Consider exiting if the key is required for all operations

config = Configuration(
    host="https://api.klavis.ai", # Default production server
    api_key=api_key,
)

# Create an API client instance
api_client = ApiClient(config)

# Example: Using the MCP Server API
mcp_api = McpServerApi(api_client)

try:
    # 1. Create a server instance for a specific MCP (e.g., GitHub)
    print("\n--- Creating a server instance ---")
    create_request = CreateServerRequest(
        server_name=ServerName.GITHUB, 
        user_id="example_user_id",        # Replace with a relevant user identifier
        platform_name="example_platform"  # Replace with your platform name
    )
    instance = mcp_api.create_server_instance(create_request)
    instance_id = instance.instance_id
    server_url = instance.server_url
    print("Instance created:")
    pprint(instance.to_dict())

    # (Optional) Check instance details
    print("\n--- Getting instance details ---")
    instance_details = mcp_api.get_server_instance(instance_id)
    print("Instance details:")
    pprint(instance_details.to_dict())
    
    # (Optional) If the server requires authentication (e.g., PAT for GitHub), 
    # you might need to set it after the OAuth flow or manually.
    # See OAuth endpoints and set_instance_auth_token. 
    # For GitHub, you'd typically complete the OAuth flow first.
    # The server_url obtained above includes the instance_id and handles routing.

    # 2. Call a tool on the created instance
    # Ensure the instance is properly authenticated if required by the tool.
    print("\n--- Calling a tool (GitHub Search Repositories) ---")
    call_request = CallToolRequest(
        server_url=server_url,                # Use the URL from the create step
        tool_name="github_search_repositories", # Tool name for the specific MCP
        tool_args={"query": "klavis ai"}      # Arguments required by the tool
    )
    tool_result = mcp_api.call_server_tool(call_request)
    print("Tool call result:")
    pprint(tool_result.to_dict())

    # 3. Clean up: Delete the instance when done
    print("\n--- Deleting instance ---")
    delete_result = mcp_api.delete_server_instance(instance_id)
    print("Deletion result:")
    pprint(delete_result.to_dict())

except Exception as e:
    print(f"An API error occurred: {e}")

```

## Available APIs

This SDK provides access to the following Klavis AI API functionalities:

*   **MCP Server API (`klavis.api.McpServerApi`)**: Manage MCP server instances, list and call tools on connected MCPs (like Slack, GitHub, Jira, etc.).
*   **OAuth APIs** (e.g., `klavis.api.SlackOauthApi`, `klavis.api.GithubOauthApi`, etc.): Handle OAuth flows for different services to authenticate MCP instances.
*   **White Labeling API (`klavis.api.WhiteLabelingApi`)**: Manage OAuth white labeling configurations.

Please refer to the `docs` and directories or the official Klavis AI API documentation for details on all available methods and models.

## Authentication

Authentication is handled via an API key passed as a Bearer token in the `Authorization` header. The `Configuration` object manages this automatically when you provide your `api_key`.

```python
from klavis import Configuration

config = Configuration(
    api_key="YOUR_API_KEY", 
)
```

## Documentation

For more detailed information on the API endpoints and models, please refer to the [Klavis AI API Documentation](https://docs.klavis.ai/).

## Contributing

Contributions are welcome! Please refer to the main repository's contribution guidelines.

## License

This SDK is distributed under the terms of the [LICENSE](./LICENSE) file.
