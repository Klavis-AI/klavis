import asyncio
from contextlib import AsyncExitStack
from typing import Dict, List, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, Tool

class MultiServerMCPClient:
    def __init__(self, server_configs: Dict[str, StdioServerParameters]):
        """
        Initialize with a dictionary of server_name -> connection_params.
        """
        self.server_configs = server_configs
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.tool_registry: Dict[str, str] = {} # Maps tool_name -> server_name

    async def __aenter__(self):
        """
        Connect to all servers in parallel.
        """
        # We use AsyncExitStack to manage multiple context managers (connections) dynamically
        for name, config in self.server_configs.items():
            try:
                # 1. Start the subprocess (stdio transport)
                read, write = await self.exit_stack.enter_async_context(
                    stdio_client(config)
                )
                
                # 2. Start the MCP Session on top of the transport
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                
                # 3. Initialize the protocol
                await session.initialize()
                
                self.sessions[name] = session
                print(f"✅ Connected to server: {name}")
                
            except Exception as e:
                print(f"❌ Failed to connect to {name}: {e}")
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Cleanly close all connections.
        """
        await self.exit_stack.aclose()

    async def get_all_tools(self) -> List[Tool]:
        """
        Query all connected servers for their tools and aggregate them.
        """
        all_tools = []
        self.tool_registry.clear()
        
        for server_name, session in self.sessions.items():
            try:
                # Fetch tools from this specific server
                response = await session.list_tools()
                
                for tool in response.tools:
                    # Register which server owns this tool
                    self.tool_registry[tool.name] = server_name
                    all_tools.append(tool)
                    
            except Exception as e:
                print(f"⚠️ Error fetching tools from {server_name}: {e}")
        
        return all_tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        Route the tool execution to the correct server.
        """
        server_name = self.tool_registry.get(tool_name)
        
        if not server_name:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
            
        session = self.sessions[server_name]
        
        result: CallToolResult = await session.call_tool(tool_name, arguments)
        return result

