from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import database.database as db
from enum import Enum
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Setup router for tool operations
tool_router = APIRouter()

# Set up Bearer authentication scheme
security_scheme = HTTPBearer(
    description="Your Klavis AI API key."
)

logger = logging.getLogger(__name__)


# Connection type enum
class ConnectionType(str, Enum):
    SSE = "SSE"
    STREAMABLE_HTTP = "StreamableHttp"


# Tool format enum for different AI models
class ToolFormat(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"  
    GEMINI = "gemini"
    MCP_NATIVE = "mcp_native"


# Helper to get API key from header
async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str:
    return credentials.credentials


# ===== CALL TOOL MODELS AND ENDPOINT =====

class CallToolRequest(BaseModel):
    serverUrl: str = Field(
        ...,
        description="The full URL for connecting to the MCP server",
    )
    toolName: str = Field(..., description="The name of the tool to call")
    toolArgs: Dict[str, Any] = Field(
        default_factory=dict, description="The input parameters for the tool"
    )
    connectionType: ConnectionType = Field(
        ConnectionType.SSE, description="The connection type to use for the MCP server. Default is SSE."
    )


class CallToolResult(BaseModel):
    """The server's response to a tool call."""
    content: list[Any] = Field(..., description="The content of the tool call")
    isError: bool = Field(False, description="Whether the tool call was successful")


class CallToolResponse(BaseModel):
    success: bool = Field(..., description="Whether the API call was successful")
    result: Optional[CallToolResult] = Field(
        None, description="The result of the tool call, if successful"
    )
    error: Optional[str] = Field(
        None, description="Error message, if the tool call failed"
    )


@tool_router.post("/call-tool", response_model=CallToolResponse,
    operation_id="callServerTool"
)
async def call_tool(
    request: Request, body: CallToolRequest, api_key: str = Depends(get_api_key)
):
    """
    Calls a tool on a specific remote MCP server, used for function calling. Eliminates the need for manual MCP code implementation.
    Under the hood, Klavis will instantiates an MCP client and establishes a connection with the remote MCP server to call the tool.
    """
    ctx = {"name": "api.mcp.call-tool", "toolName": body.toolName}
    logger.info(f"{ctx} Received tool call request")

    try:
        # Validate API key first
        if not await db.validate_api_key(api_key):
            logger.error(f"{ctx} Invalid API key")
            return CallToolResponse(success=False, error="Invalid API key")

        # Call the tool using the provided server URL
        try:
            if body.connectionType == ConnectionType.STREAMABLE_HTTP:
                async with streamablehttp_client(body.serverUrl) as (
                    read_stream,
                    write_stream,
                    _,
                ):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.call_tool(body.toolName, body.toolArgs)
            else:
                async with sse_client(body.serverUrl) as streams:
                    read_stream, write_stream = streams
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.call_tool(body.toolName, body.toolArgs)

            logger.info(f"{ctx} Tool call successful")
            return CallToolResponse(success=True, result=result.model_dump())
        except Exception as e:
            logger.error(f"{ctx} Error calling tool: {str(e)}")
            return CallToolResponse(
                success=False, error=f"Error calling tool: {str(e)}"
            )

    except Exception as e:
        logger.error(f"{ctx} Unhandled error in tool call: {str(e)}")
        return CallToolResponse(success=False, error=str(e))


# ===== LIST TOOLS MODELS AND ENDPOINT =====

class ListToolsRequest(BaseModel):
    serverUrl: str = Field(
        ...,
        description="The full URL for connecting to the MCP server",
    )
    connectionType: ConnectionType = Field(
        ConnectionType.SSE, 
        description="The connection type to use for the MCP server. Default is SSE."
    )
    format: ToolFormat = Field(
        ToolFormat.MCP_NATIVE,
        description="The format to return tools in. Default is MCP Native format for maximum compatibility."
    )


# OpenAI format tool models
class OpenAIFunctionParameters(BaseModel):
    type: str = Field(default="object", description="Parameter schema type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Parameter properties")
    required: Optional[List[str]] = Field(default_factory=list, description="Required parameters")


class OpenAIFunction(BaseModel):
    name: str = Field(..., description="Function name")
    description: str = Field(..., description="Function description")
    parameters: OpenAIFunctionParameters = Field(..., description="Function parameters schema")


class OpenAITool(BaseModel):
    type: str = Field(default="function", description="Tool type")
    function: OpenAIFunction = Field(..., description="Function definition")


# Anthropic format tool models
class AnthropicInputSchema(BaseModel):
    type: str = Field(default="object", description="Input schema type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Input properties")
    required: Optional[List[str]] = Field(default_factory=list, description="Required parameters")


class AnthropicTool(BaseModel):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: AnthropicInputSchema = Field(..., description="Tool input schema")


# Gemini format tool models
class GeminiParameterSchema(BaseModel):
    type: str = Field(..., description="Parameter type")
    description: Optional[str] = Field(None, description="Parameter description")
    items: Optional['GeminiParameterSchema'] = Field(default=None, description="Schema for items if type is array")


class GeminiFunctionParameters(BaseModel):
    type: str = Field(default="object", description="Parameters type")
    properties: Dict[str, GeminiParameterSchema] = Field(default_factory=dict, description="Parameter definitions")
    required: Optional[List[str]] = Field(default_factory=list, description="Required parameters")


class GeminiFunctionDeclaration(BaseModel):
    name: str = Field(..., description="Function name")
    description: str = Field(..., description="Function description")
    parameters: GeminiFunctionParameters = Field(..., description="Function parameters")


class GeminiTool(BaseModel):
    function_declarations: List[GeminiFunctionDeclaration] = Field(..., description="Function declarations")


# MCP Native format (original format from MCP server)
class McpNativeTool(BaseModel):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Optional[Dict[str, Any]] = Field(None, description="Tool input schema")


class ListToolsResponse(BaseModel):
    success: bool = Field(..., description="Whether the list tools request was successful")
    tools: Optional[List[Any]] = Field(None, description="List of tools in the requested format")
    format: ToolFormat = Field(..., description="The format of the returned tools")
    error: Optional[str] = Field(None, description="Error message, if the request failed")


def convert_mcp_tools_to_format(mcp_tools: List[Dict[str, Any]], target_format: ToolFormat) -> List[Any]:
    """Convert MCP tools to the specified format."""
    if target_format == ToolFormat.MCP_NATIVE:
        return [McpNativeTool(**tool) for tool in mcp_tools]
    
    elif target_format == ToolFormat.OPENAI:
        openai_tools = []
        for tool in mcp_tools:
            input_schema = tool.get("inputSchema", {})
            openai_tool = OpenAITool(
                type="function",
                function=OpenAIFunction(
                    name=tool.get("name", ""),
                    description=tool.get("description", ""),
                    parameters=OpenAIFunctionParameters(
                        type=input_schema.get("type", "object"),
                        properties=input_schema.get("properties", {}),
                        required=input_schema.get("required", [])
                    )
                )
            )
            openai_tools.append(openai_tool)
        return openai_tools
    
    elif target_format == ToolFormat.ANTHROPIC:
        anthropic_tools = []
        for tool in mcp_tools:
            input_schema = tool.get("inputSchema", {})
            anthropic_tool = AnthropicTool(
                name=tool.get("name", ""),
                description=tool.get("description", ""),
                input_schema=AnthropicInputSchema(
                    type=input_schema.get("type", "object"),
                    properties=input_schema.get("properties", {}),
                    required=input_schema.get("required", [])
                )
            )
            anthropic_tools.append(anthropic_tool)
        return anthropic_tools
    
    elif target_format == ToolFormat.GEMINI:
        function_declarations = []
        for tool in mcp_tools:
            input_schema = tool.get("inputSchema", {})
            properties = input_schema.get("properties", {})
            
            # Convert properties to Gemini format
            gemini_properties = {}
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type")
                
                if prop_type == "array":
                    items_schema_info = prop_info.get("items", {})
                    items_schema = GeminiParameterSchema(
                        type=items_schema_info.get("type", "string"),
                        description=items_schema_info.get("description")
                    )
                    gemini_properties[prop_name] = GeminiParameterSchema(
                        type=prop_type,
                        description=prop_info.get("description", ""),
                        items=items_schema
                    )
                else:
                    gemini_properties[prop_name] = GeminiParameterSchema(
                        type=prop_info.get("type", "string"),
                        description=prop_info.get("description", "")
                    )
            
            function_declarations.append(
                GeminiFunctionDeclaration(
                    name=tool.get("name", ""),
                    description=tool.get("description", ""),
                    parameters=GeminiFunctionParameters(
                        type="object",
                        properties=gemini_properties,
                        required=input_schema.get("required", [])
                    )
                )
            )
        
        return [GeminiTool(function_declarations=function_declarations)]
    
    else:
        # Default to MCP native if unknown format
        return [McpNativeTool(**tool) for tool in mcp_tools]


@tool_router.post("/list-tools", response_model=ListToolsResponse,
    operation_id="listServerTools"
)
async def list_tools(
    request: Request, 
    body: ListToolsRequest, 
    api_key: str = Depends(get_api_key)
):
    """
    Lists all tools available for a specific remote MCP server in various AI model formats.
    
    This eliminates the need for manual MCP code implementation and format conversion.
    Under the hood, Klavis instantiates an MCP client and establishes a connection 
    with the remote MCP server to retrieve available tools.
    """
    ctx = {"name": "api.mcp.list-tools", "format": body.format}
    logger.info(f"{ctx} Received list tools request")

    try:
        # Validate API key first
        if not await db.validate_api_key(api_key):
            logger.error(f"{ctx} Invalid API key")
            return ListToolsResponse(
                success=False, 
                format=body.format,
                error="Invalid API key"
            )

        # Connect to MCP server and retrieve tools
        try:
            if body.connectionType == ConnectionType.STREAMABLE_HTTP:
                async with streamablehttp_client(body.serverUrl) as (
                    read_stream,
                    write_stream,
                    _,
                ):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.list_tools()
            else:
                async with sse_client(body.serverUrl) as streams:
                    read_stream, write_stream = streams
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.list_tools()

            # Convert MCP tools to requested format
            mcp_tools = [tool.model_dump() for tool in result.tools]
            formatted_tools = convert_mcp_tools_to_format(mcp_tools, body.format)

            logger.info(f"{ctx} List tools successful, converted {len(mcp_tools)} tools to {body.format} format")
            return ListToolsResponse(
                success=True, 
                tools=formatted_tools,
                format=body.format
            )
            
        except Exception as e:
            logger.error(f"{ctx} Error listing tools: {str(e)}")
            return ListToolsResponse(
                success=False, 
                format=body.format,
                error=f"Error listing tools: {str(e)}"
            )

    except Exception as e:
        logger.error(f"{ctx} Unhandled error in list tools: {str(e)}")
        return ListToolsResponse(
            success=False, 
            format=body.format,
            error=str(e)
        ) 