"""
Main entry point for Exa MCP Server - Debug Version
"""

import asyncio
import sys
import os
from typing import Dict, Any, List

# Add debug prints
print("DEBUG: Starting Exa MCP Server", file=sys.stderr)
print(f"DEBUG: Python version: {sys.version}", file=sys.stderr)
print(f"DEBUG: Working directory: {os.getcwd()}", file=sys.stderr)
print(f"DEBUG: EXA_API_KEY set: {'EXA_API_KEY' in os.environ}", file=sys.stderr)

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    ListToolsRequest,
    CallToolRequest,
    Tool,
    TextContent,
)

try:
    from mcp.server.models import ServerCapabilities
    from mcp.types import ToolsCapability
    HAS_NEW_MCP = True
    print("DEBUG: Using new MCP version", file=sys.stderr)
except ImportError:
    HAS_NEW_MCP = False
    print("DEBUG: Using old MCP version", file=sys.stderr)

try:
    from .client.exa_client import ExaClient
    from .tools.search import SearchWebTool, SearchRecentContentTool, SearchAcademicContentTool
    from .tools.content import GetPageContentsTool
    from .tools.discovery import FindSimilarContentTool
    from .utils.config import get_config, validate_config
    from .utils.logging import setup_logging, get_logger
    print("DEBUG: All imports successful", file=sys.stderr)
except ImportError as e:
    print(f"DEBUG: Import error: {e}", file=sys.stderr)
    raise

# Initialize logging
logger = setup_logging()

# Global client instance
exa_client: ExaClient = None
tools_registry: Dict[str, Any] = {}


async def initialize_server():
    """Initialize the MCP server and all components"""
    global exa_client, tools_registry
    
    print("DEBUG: Initializing server components", file=sys.stderr)
    logger.info("Initializing Exa MCP Server")
    
    # Validate configuration
    if not validate_config():
        print("DEBUG: Configuration validation failed", file=sys.stderr)
        raise RuntimeError("Configuration validation failed")
    
    print("DEBUG: Configuration validated", file=sys.stderr)
    
    # Initialize Exa client
    exa_client = ExaClient()
    logger.info("Exa client initialized")
    print("DEBUG: Exa client created", file=sys.stderr)
    
    # Initialize tools
    tools_registry = {
        "search_web": SearchWebTool(exa_client),
        "get_page_contents": GetPageContentsTool(exa_client),
        "find_similar_content": FindSimilarContentTool(exa_client),
        "search_recent_content": SearchRecentContentTool(exa_client),
        "search_academic_content": SearchAcademicContentTool(exa_client),
    }
    
    logger.info(f"Initialized {len(tools_registry)} tools: {list(tools_registry.keys())}")
    print(f"DEBUG: Tools initialized: {list(tools_registry.keys())}", file=sys.stderr)


# Create the MCP server
config = get_config()
server = Server(config.server_name)
print(f"DEBUG: Server created with name: {config.server_name}", file=sys.stderr)


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools"""
    print("DEBUG: list_tools called", file=sys.stderr)
    if not tools_registry:
        await initialize_server()
    
    tool_definitions = []
    for tool in tools_registry.values():
        tool_definitions.append(tool.get_tool_definition())
    
    logger.info(f"Listed {len(tool_definitions)} tools")
    print(f"DEBUG: Returning {len(tool_definitions)} tools", file=sys.stderr)
    return tool_definitions


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool execution requests"""
    print(f"DEBUG: call_tool called with: {name}", file=sys.stderr)
    if not tools_registry:
        await initialize_server()
    
    if name not in tools_registry:
        error_msg = f"Unknown tool '{name}'. Available tools: {list(tools_registry.keys())}"
        logger.error(error_msg)
        print(f"DEBUG: Unknown tool error: {error_msg}", file=sys.stderr)
        return [TextContent(type="text", text=f"Error: {error_msg}")]
    
    try:
        tool = tools_registry[name]
        logger.info(f"Executing tool: {name}")
        print(f"DEBUG: Executing tool {name} with args: {arguments}", file=sys.stderr)
        
        result = await tool.execute(arguments)
        logger.info(f"Tool {name} executed successfully")
        print(f"DEBUG: Tool {name} completed successfully", file=sys.stderr)
        return result
        
    except Exception as e:
        error_msg = f"Tool execution failed for {name}: {str(e)}"
        logger.error(error_msg)
        print(f"DEBUG: Tool execution error: {error_msg}", file=sys.stderr)
        return [TextContent(type="text", text=f"Error: {error_msg}")]


async def run_server():
    """Run the MCP server"""
    try:
        print("DEBUG: Starting server run", file=sys.stderr)
        logger.info("Starting Exa MCP Server")
        
        # Initialize server components
        await initialize_server()
        print("DEBUG: Server initialization complete", file=sys.stderr)
        
        # Run the server
        print("DEBUG: Starting stdio server", file=sys.stderr)
        async with stdio_server() as (read_stream, write_stream):
            print("DEBUG: stdio server started", file=sys.stderr)
            
            # Handle different MCP library versions
            if HAS_NEW_MCP:
                capabilities = ServerCapabilities(
                    tools=ToolsCapability(listChanged=False)
                )
            else:
                try:
                    capabilities = server.get_capabilities()
                except TypeError:
                    # Fallback for different MCP versions
                    capabilities = server.get_capabilities(None, None)
            
            print("DEBUG: About to start server.run", file=sys.stderr)
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=config.server_name,
                    server_version=config.server_version,
                    capabilities=capabilities,
                ),
            )
            
    except KeyboardInterrupt:
        print("DEBUG: Server shutdown by user", file=sys.stderr)
        logger.info("Server shutdown requested by user")
    except Exception as e:
        print(f"DEBUG: Server error: {str(e)}", file=sys.stderr)
        logger.error(f"Server error: {str(e)}")
        raise
    finally:
        # Clean up resources
        if exa_client:
            await exa_client.close()
            logger.info("Server cleanup completed")
            print("DEBUG: Server cleanup completed", file=sys.stderr)


def main():
    """Main entry point"""
    print("DEBUG: main() called", file=sys.stderr)
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("DEBUG: main() interrupted by user", file=sys.stderr)
        logger.info("Server stopped by user")
    except Exception as e:
        print(f"DEBUG: main() fatal error: {str(e)}", file=sys.stderr)
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    print("DEBUG: __main__ entry point", file=sys.stderr)
    main()