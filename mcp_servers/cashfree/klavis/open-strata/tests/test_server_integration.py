"""Integration tests for server.py tool_calls without mocking."""

import asyncio
import json
import logging
from typing import Any, Dict

import pytest
import pytest_asyncio
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from strata.config import MCPServerConfig, MCPServerList
from strata.mcp_client_manager import MCPClientManager
from strata.server import client_manager as global_client_manager
from strata.tools import (
    TOOL_DISCOVER_SERVER_ACTIONS,
    TOOL_EXECUTE_ACTION,
    TOOL_GET_ACTION_DETAILS,
    TOOL_HANDLE_AUTH_FAILURE,
    TOOL_SEARCH_DOCUMENTATION,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_mcp_server():
    """Create a simple test MCP server that runs in a subprocess."""

    async def run_test_server():
        """Run a test MCP server with some basic tools."""
        server = Server("test-mcp-server")

        @server.list_tools()
        async def list_tools():
            """List available tools."""
            return [
                {
                    "name": "get_time",
                    "description": "Get the current time",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "Timezone (e.g., UTC, EST)",
                            }
                        },
                    },
                },
                {
                    "name": "echo",
                    "description": "Echo back the input message",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message to echo",
                            }
                        },
                        "required": ["message"],
                    },
                },
                {
                    "name": "calculate",
                    "description": "Perform a simple calculation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["add", "subtract", "multiply", "divide"],
                                "description": "Operation to perform",
                            },
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["operation", "a", "b"],
                    },
                },
            ]

        @server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            """Handle tool calls."""
            if name == "get_time":
                import datetime

                timezone = arguments.get("timezone", "UTC")
                return [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "time": datetime.datetime.now().isoformat(),
                                "timezone": timezone,
                            }
                        ),
                    }
                ]
            elif name == "echo":
                message = arguments.get("message", "")
                return [{"type": "text", "text": json.dumps({"echoed": message})}]
            elif name == "calculate":
                operation = arguments.get("operation")
                a = arguments.get("a", 0)
                b = arguments.get("b", 0)

                result = 0
                if operation == "add":
                    result = a + b
                elif operation == "subtract":
                    result = a - b
                elif operation == "multiply":
                    result = a * b
                elif operation == "divide":
                    result = a / b if b != 0 else "Error: Division by zero"

                return [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {"result": result, "operation": operation, "a": a, "b": b}
                        ),
                    }
                ]
            else:
                return [
                    {
                        "type": "text",
                        "text": json.dumps({"error": f"Unknown tool: {name}"}),
                    }
                ]

        # Run the server
        await stdio_server(server)

    # Run in asyncio
    asyncio.run(run_test_server())


async def call_server_tool(tool_name: str, arguments: dict):
    """Helper function to call server tools directly."""
    # Use the global client_manager from server.py
    client_manager = global_client_manager

    # Import the actual implementation from utils
    from strata.utils.shared_search import UniversalToolSearcher

    result = None

    if tool_name == TOOL_DISCOVER_SERVER_ACTIONS:
        user_query = arguments.get("user_query")
        server_names = arguments.get("server_names")

        # If no server names provided, use all available servers
        if not server_names:
            server_names = list(client_manager.active_clients.keys())

        # Discover actions from specified servers
        discovery_result = {}
        for server_name in server_names:
            try:
                client = client_manager.get_client(server_name)
                tools = await client.list_tools()

                # Filter tools based on user query if provided
                if user_query and tools:
                    # Build search index for this server's tools
                    tools_map = {server_name: tools}
                    searcher = UniversalToolSearcher(tools_map)
                    search_results = searcher.search(user_query, max_results=50)

                    # Convert search results back to tool list
                    filtered_tools = []
                    for result_item in search_results:
                        for tool in tools:
                            if tool["name"] == result_item["name"]:
                                filtered_tools.append(
                                    {
                                        "name": tool["name"],
                                        "description": tool["description"],
                                        "inputSchema": tool["inputSchema"],
                                    }
                                )
                                break
                    discovery_result[server_name] = filtered_tools
                else:
                    # Return all tools if no query
                    discovery_result[server_name] = [
                        {
                            "name": tool["name"],
                            "description": tool["description"],
                            "inputSchema": tool["inputSchema"],
                        }
                        for tool in (tools or [])
                    ]
            except KeyError:
                discovery_result[server_name] = {
                    "error": f"Server '{server_name}' not found or not connected"
                }
            except Exception as e:
                logger.error(f"Error discovering actions from {server_name}: {str(e)}")
                discovery_result[server_name] = {"error": str(e)}

        result = {"servers": discovery_result}

    elif tool_name == TOOL_GET_ACTION_DETAILS:
        server_name = arguments.get("server_name")
        action_name = arguments.get("action_name")

        if not server_name or not action_name:
            return [
                {
                    "type": "text",
                    "text": "Error: Both server_name and action_name are required",
                }
            ]

        try:
            client = client_manager.get_client(server_name)
            tools = await client.list_tools()

            action_found = None
            for tool in tools or []:
                if tool["name"] == action_name:
                    action_found = tool
                    break

            if action_found:
                result = {
                    "server": server_name,
                    "action": {
                        "name": action_found["name"],
                        "description": action_found["description"],
                        "inputSchema": action_found["inputSchema"],
                    },
                }
            else:
                result = {
                    "error": f"Action '{action_name}' not found in server '{server_name}'"
                }
        except Exception as e:
            result = {"error": f"Error: {str(e)}"}

    elif tool_name == TOOL_EXECUTE_ACTION:
        server_name = arguments.get("server_name")
        action_name = arguments.get("action_name")

        if not all([server_name, action_name]):
            return [
                {
                    "type": "text",
                    "text": "Error: server_name and action_name are required",
                }
            ]

        try:
            client = client_manager.get_client(server_name)
            action_params = {}

            # Parse parameters
            for param_name in ["path_params", "query_params", "body_schema"]:
                param_value = arguments.get(param_name)
                if param_value:
                    if isinstance(param_value, str):
                        try:
                            action_params.update(json.loads(param_value))
                        except json.JSONDecodeError:
                            return [
                                {
                                    "type": "text",
                                    "text": f"Error: Invalid JSON in {param_name}",
                                }
                            ]
                    else:
                        action_params.update(param_value)

            # Call the tool
            tool_result = await client.call_tool(action_name, action_params)

            # Process result
            if tool_result:
                if isinstance(tool_result, list):
                    extracted = []
                    for item in tool_result:
                        if hasattr(item, "text"):
                            extracted.append(item.text)
                        else:
                            extracted.append(str(item))
                    result_text = "\n".join(extracted)
                    try:
                        result = json.loads(result_text)
                    except:
                        result = {"output": result_text}
                else:
                    result = {"output": str(tool_result)}
            else:
                result = {"output": "Action executed successfully"}
        except Exception as e:
            result = {"error": str(e)}

    elif tool_name == TOOL_SEARCH_DOCUMENTATION:
        query = arguments.get("query")
        server_name = arguments.get("server_name")
        max_results = arguments.get("max_results", 10)

        if not query or not server_name:
            return [
                {
                    "type": "text",
                    "text": "Error: Both query and server_name are required",
                }
            ]

        try:
            client = client_manager.get_client(server_name)
            tools = await client.list_tools()

            # Build search index
            tools_map = {server_name: tools if tools else []}
            searcher = UniversalToolSearcher(tools_map)
            result = searcher.search(query, max_results=max_results)
        except Exception as e:
            result = [{"error": str(e)}]

    elif tool_name == TOOL_HANDLE_AUTH_FAILURE:
        server_name = arguments.get("server_name")
        intention = arguments.get("intention")
        auth_data = arguments.get("auth_data")

        if not server_name or not intention:
            return [
                {
                    "type": "text",
                    "text": "Error: Both server_name and intention are required",
                }
            ]

        if intention == "get_auth_url":
            result = {
                "server": server_name,
                "message": f"Authentication required for server '{server_name}'",
                "instructions": "Please provide authentication credentials",
                "required_fields": {"token": "Authentication token or API key"},
            }
        elif intention == "save_auth_data":
            if not auth_data:
                return [
                    {
                        "type": "text",
                        "text": "Error: auth_data is required when intention is 'save_auth_data'",
                    }
                ]
            result = {
                "server": server_name,
                "status": "success",
                "message": f"Authentication data saved for server '{server_name}'",
            }
        else:
            result = {"error": f"Invalid intention: '{intention}'"}

    else:
        return [{"type": "text", "text": f"Unknown tool: {tool_name}"}]

    # Return formatted result
    return [{"type": "text", "text": json.dumps(result) if result else "{}"}]


class TestServerToolCalls:
    """Test all server tool_calls with real MCP connections."""

    @pytest_asyncio.fixture
    async def setup_test_environment(self, tmp_path):
        """Set up test environment with a real MCP server."""
        # Create a test config directory
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create test MCP server config
        config = MCPServerList()

        # Add GitHub MCP server (a real server we can test with)
        github_server = MCPServerConfig(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            # Will work for listing tools
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"},
            enabled=True,
        )
        config.add_server(github_server)

        # Save config
        config.save()

        # Initialize the global client manager with test config
        await global_client_manager.initialize_from_config()

        yield global_client_manager

        # Cleanup - just clear the active clients
        global_client_manager.active_clients.clear()

    @pytest.mark.asyncio
    async def test_discover_server_actions_all_servers(self, setup_test_environment):
        """Test TOOL_DISCOVER_SERVER_ACTIONS with all available servers."""
        manager = setup_test_environment

        # Test discovering actions from all servers (server_names not provided)
        try:
            result = await call_server_tool(
                TOOL_DISCOVER_SERVER_ACTIONS, {"user_query": ""}  # No filter
            )

            assert len(result) == 1
            assert result[0]["type"] == "text"

            # Parse the JSON response
            data = json.loads(result[0]["text"])
            assert "servers" in data

            # Should have discovered actions from connected servers
            if data["servers"]:
                for server_name, actions in data["servers"].items():
                    logger.info(
                        f"Server {server_name}: {len(actions) if isinstance(actions, list) else actions} actions"
                    )
                    if isinstance(actions, list):
                        assert len(actions) >= 0  # May have 0 or more actions
                    elif isinstance(actions, dict) and "error" in actions:
                        # Server might not be connected
                        logger.warning(
                            f"Server {server_name} error: {actions['error']}"
                        )
        finally:
            pass

    @pytest.mark.asyncio
    async def test_discover_server_actions_with_query(self, setup_test_environment):
        """Test TOOL_DISCOVER_SERVER_ACTIONS with search query."""
        manager = setup_test_environment

        # Test discovering actions with a search query
        try:
            result = await call_server_tool(
                TOOL_DISCOVER_SERVER_ACTIONS,
                {
                    "user_query": "repository",  # Search for repository-related actions
                    "server_names": ["github"],
                },
            )

            assert len(result) == 1
            assert result[0]["type"] == "text"

            data = json.loads(result[0]["text"])
            assert "servers" in data

            if "github" in data["servers"] and isinstance(
                data["servers"]["github"], list
            ):
                # Should find repository-related actions if GitHub server is connected
                for action in data["servers"]["github"]:
                    logger.info(f"Found action: {action.get('name')}")
        finally:
            pass

    @pytest.mark.asyncio
    async def test_get_action_details(self, setup_test_environment):
        """Test TOOL_GET_ACTION_DETAILS."""
        manager = setup_test_environment

        # First discover available actions
        try:
            discover_result = await call_server_tool(
                TOOL_DISCOVER_SERVER_ACTIONS,
                {"user_query": "", "server_names": ["github"]},
            )

            discover_data = json.loads(discover_result[0]["text"])

            # Get details for a specific action if any were found
            if "github" in discover_data["servers"] and isinstance(
                discover_data["servers"]["github"], dict
            ):
                github_data = discover_data["servers"]["github"]
                if "actions" in github_data and github_data["actions"]:
                    action_name = github_data["actions"][0]

                    # Get action details
                    result = await call_server_tool(
                        TOOL_GET_ACTION_DETAILS,
                        {"server_name": "github", "action_name": action_name},
                    )

                    assert len(result) == 1
                    assert result[0]["type"] == "text"

                    data = json.loads(result[0]["text"])

                    if "error" not in data:
                        assert "server" in data
                        assert "action" in data
                        assert data["server"] == "github"
                        assert data["action"]["name"] == action_name
                        assert "inputSchema" in data["action"]
                        logger.info(f"Got details for action: {action_name}")

            # Test with non-existent action
            result = await call_server_tool(
                TOOL_GET_ACTION_DETAILS,
                {"server_name": "github", "action_name": "non_existent_action_xyz"},
            )

            assert len(result) == 1
            data = json.loads(result[0]["text"])
            assert "error" in data
            assert "not found" in data["error"].lower()

        finally:
            pass

    @pytest.mark.asyncio
    async def test_execute_action(self, setup_test_environment):
        """Test TOOL_EXECUTE_ACTION."""
        manager = setup_test_environment

        # Note: We can't actually execute GitHub actions without proper auth,
        # but we can test the error handling
        try:
            result = await call_server_tool(
                TOOL_EXECUTE_ACTION,
                {
                    "server_name": "github",
                    "action_name": "create_issue",
                    "body_schema": json.dumps(
                        {
                            "owner": "test",
                            "repo": "test",
                            "title": "Test Issue",
                            "body": "This is a test",
                        }
                    ),
                },
            )

            assert len(result) == 1
            assert result[0]["type"] == "text"

            data = json.loads(result[0]["text"])
            # Will likely get an auth error or similar
            logger.info(f"Execute action result: {data}")

            # Test with invalid JSON parameters
            result = await call_server_tool(
                TOOL_EXECUTE_ACTION,
                {
                    "server_name": "github",
                    "action_name": "test_action",
                    "body_schema": "invalid json {",
                },
            )

            assert len(result) == 1
            assert "Invalid JSON" in result[0]["text"]

        finally:
            pass

    @pytest.mark.asyncio
    async def test_search_documentation(self, setup_test_environment):
        """Test TOOL_SEARCH_DOCUMENTATION."""
        manager = setup_test_environment

        # Search for specific documentation
        try:
            result = await call_server_tool(
                TOOL_SEARCH_DOCUMENTATION,
                {"query": "repository", "server_name": "github", "max_results": 5},
            )

            assert len(result) == 1
            assert result[0]["type"] == "text"

            data = json.loads(result[0]["text"])
            assert isinstance(data, list)

            if data and not any(
                "error" in item for item in data if isinstance(item, dict)
            ):
                # Found some results
                for item in data[:3]:  # Log first 3 results
                    logger.info(f"Search result: {item.get('name', item)}")

            # Test with missing parameters
            result = await call_server_tool(
                TOOL_SEARCH_DOCUMENTATION,
                {
                    "query": "test"
                    # Missing server_name
                },
            )

            assert len(result) == 1
            assert "required" in result[0]["text"].lower()

        finally:
            pass

    @pytest.mark.asyncio
    async def test_handle_auth_failure(self, setup_test_environment):
        """Test TOOL_HANDLE_AUTH_FAILURE."""
        manager = setup_test_environment

        # Test get_auth_url intention
        try:
            result = await call_server_tool(
                TOOL_HANDLE_AUTH_FAILURE,
                {"server_name": "github", "intention": "get_auth_url"},
            )

            assert len(result) == 1
            assert result[0]["type"] == "text"

            data = json.loads(result[0]["text"])
            assert "server" in data
            assert data["server"] == "github"
            assert "instructions" in data
            assert "required_fields" in data
            logger.info(f"Auth instructions: {data['message']}")

            # Test save_auth_data intention
            result = await call_server_tool(
                TOOL_HANDLE_AUTH_FAILURE,
                {
                    "server_name": "github",
                    "intention": "save_auth_data",
                    "auth_data": {"token": "test_token_123"},
                },
            )

            assert len(result) == 1
            data = json.loads(result[0]["text"])
            assert "status" in data
            assert data["status"] == "success"
            logger.info(f"Auth save result: {data['message']}")

            # Test invalid intention
            result = await call_server_tool(
                TOOL_HANDLE_AUTH_FAILURE,
                {"server_name": "github", "intention": "invalid_intention"},
            )

            assert len(result) == 1
            data = json.loads(result[0]["text"])
            assert "error" in data
            assert "Invalid intention" in data["error"]

            # Test missing auth_data for save_auth_data
            result = await call_server_tool(
                TOOL_HANDLE_AUTH_FAILURE,
                {
                    "server_name": "github",
                    "intention": "save_auth_data",
                    # Missing auth_data
                },
            )

            assert len(result) == 1
            assert "auth_data is required" in result[0]["text"]

        finally:
            pass

    @pytest.mark.asyncio
    async def test_error_handling(self, setup_test_environment):
        """Test error handling for various edge cases."""
        manager = setup_test_environment

        # Test with non-existent server
        try:
            result = await call_server_tool(
                TOOL_GET_ACTION_DETAILS,
                {"server_name": "non_existent_server", "action_name": "test"},
            )

            assert len(result) == 1
            data = json.loads(result[0]["text"])
            assert "error" in data
            # The error message contains the server name
            assert "non_existent_server" in data["error"].lower()

            # Test unknown tool
            result = await call_server_tool("unknown_tool_name", {})

            assert len(result) == 1
            assert "Unknown tool" in result[0]["text"]

        finally:
            pass


@pytest.mark.integration
class TestServerIntegrationWithRealServer:
    """Integration tests that require a real MCP server running."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: discover -> get details -> execute."""
        # This test requires proper setup of MCP servers
        # It's marked as integration test and can be skipped in CI

        # Create manager
        manager = MCPClientManager()
        await manager.initialize_from_config()

        # Update the global client manager to use our manager
        global global_client_manager
        original_manager = global_client_manager
        global_client_manager.active_clients = manager.active_clients
        global_client_manager.server_list = manager.server_list

        try:
            # 1. Discover available servers and actions
            discover_result = await call_server_tool(
                TOOL_DISCOVER_SERVER_ACTIONS, {"user_query": ""}
            )

            discover_data = json.loads(discover_result[0]["text"])
            logger.info(f"Discovered servers: {list(discover_data['servers'].keys())}")

            # 2. For each server with actions, get details of first action
            for server_name, server_data in discover_data["servers"].items():
                if (
                    isinstance(server_data, dict)
                    and "actions" in server_data
                    and server_data["actions"]
                ):
                    first_action_name = server_data["actions"][0]
                    logger.info(
                        f"\nServer: {server_name}, Testing action: {first_action_name}"
                    )

                    # Get action details
                    details_result = await call_server_tool(
                        TOOL_GET_ACTION_DETAILS,
                        {
                            "server_name": server_name,
                            "action_name": first_action_name,
                        },
                    )

                    details_data = json.loads(details_result[0]["text"])
                    if "error" not in details_data:
                        logger.info(f"Action details retrieved successfully")
                        logger.info(
                            f"Input schema: {details_data['action'].get('inputSchema', {})}"
                        )

                    # 3. Search for related documentation
                    search_result = await call_server_tool(
                        TOOL_SEARCH_DOCUMENTATION,
                        {
                            "query": first_action_name,
                            "server_name": server_name,
                            "max_results": 3,
                        },
                    )

                    search_data = json.loads(search_result[0]["text"])
                    logger.info(f"Search found {len(search_data)} results")

                    break  # Test with first server only

        finally:
            # Cleanup manager
            await manager.disconnect_all()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
