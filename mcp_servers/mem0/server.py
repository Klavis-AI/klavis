import os
import base64
import logging
import contextlib
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, Optional

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    mem0_api_key_context,
    mem0_user_id_context,
    DEFAULT_MCP_USER_ID,
    get_mem0_user_id,
    add_memory,
    get_memories,
    search_memories,
    get_memory,
    update_memory,
    delete_memory,
    delete_all_memories,
    list_entities,
    delete_entities,
)

load_dotenv()


def get_path(data: dict, path: str) -> any:
    """Safe dot-notation access. Returns None if path fails."""
    if not data:
        return None
    current = data
    for key in path.split('.'):
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def normalize(source: dict, mapping: dict[str, any]) -> dict:
    """
    Creates a new clean dictionary based strictly on the mapping rules.
    Excludes fields with None/null values from the output.
    Args:
        source: Raw vendor JSON.
        mapping: Dict of { "TargetFieldName": "Source.Path" OR Lambda_Function }
    """
    clean_data = {}
    for target_key, rule in mapping.items():
        value = None
        if isinstance(rule, str):
            value = get_path(source, rule)
        elif callable(rule):
            try:
                value = rule(source)
            except Exception:
                value = None
        if value is not None:
            clean_data[target_key] = value
    return clean_data


# Mapping Rules for Mem0 Objects

MEMORY_RULES = {
    "memoryId": "id",
    "content": "memory",
    "created": "created_at",
    "updated": "updated_at",
    "userId": "user_id",
    "agentId": "agent_id",
    "appId": "app_id",
    "runId": "run_id",
    "score": "score",
    "metadata": "metadata",
    "categories": "categories",
    "expirationDate": "expiration_date",
    "structuredData": "structured_attributes",
}

MEMORY_LIST_RULES = {
    "items": lambda x: [
        normalize(memory, MEMORY_RULES) for memory in x.get('result', {}).get('results', [])
    ] if x.get('success') and x.get('result', {}).get('results') else None,
    "totalCount": lambda x: len(x.get('result', {}).get('results', [])) if x.get('success') and x.get('result', {}).get('results') else None,
    "success": "success",
    "error": "error",
}

MEMORY_SEARCH_RULES = {
    "results": lambda x: [
        normalize(memory, MEMORY_RULES) for memory in (x.get('result', {}).get('results', []) if x.get('result', {}).get('results') else x.get('result', []))
    ] if x.get('success') and x.get('result') else None,
    "query": lambda x: x.get('query') or getattr(x, '_original_query', None),
    "totalFound": lambda x: len(x.get('result', {}).get('results', []) if x.get('result', {}).get('results') else x.get('result', [])) if x.get('success') and x.get('result') else None,
    "success": "success",
    "error": "error",
}

MEMORY_OPERATION_RULES = {
    "success": "success",
    "memoryId": "result.id",
    "operation": lambda x: x.get('operation', 'unknown'),
    "message": lambda x: x.get('result', {}).get('message') or x.get('error', 'Operation completed'),
    "error": "error",
    "status": "status",
}

ENTITY_LIST_RULES = {
    "entities": lambda x: [
        {
            "name": entity.get('name'),  # 'name' field contains the actual user_id
            "entityType": entity.get('type', 'user'),
            "memoryCount": entity.get('total_memories', 0),
            "created": entity.get('created_at'),
            "updated": entity.get('updated_at'),
            "owner": entity.get('owner'),
            "metadata": entity.get('metadata'),
        } for entity in x.get('result', {}).get('results', [])
    ] if x.get('success') and x.get('result', {}).get('results') else None,
    "totalEntities": lambda x: x.get('result', {}).get('count', 0) if x.get('success') and x.get('result') else None,
    "totalUsers": lambda x: x.get('result', {}).get('total_users', 0) if x.get('success') and x.get('result') else None,
    "totalAgents": lambda x: x.get('result', {}).get('total_agents', 0) if x.get('success') and x.get('result') else None,
    "totalApps": lambda x: x.get('result', {}).get('total_apps', 0) if x.get('success') and x.get('result') else None,
    "totalRuns": lambda x: x.get('result', {}).get('total_runs', 0) if x.get('success') and x.get('result') else None,
    "nextPage": lambda x: x.get('result', {}).get('next') if x.get('success') and x.get('result') else None,
    "previousPage": lambda x: x.get('result', {}).get('previous') if x.get('success') and x.get('result') else None,
    "success": "success",
    "error": "error",
}


def normalize_memory(raw_memory: dict) -> dict:
    """Normalize a single memory and add computed fields."""
    memory = normalize(raw_memory, MEMORY_RULES)
    return memory


def normalize_memory_list(raw_response: dict) -> dict:
    """Normalize a memory list response and add computed fields."""
    response = normalize(raw_response, MEMORY_LIST_RULES)
    return response


def normalize_memory_search(raw_response: dict) -> dict:
    """Normalize a memory search response and add computed fields."""
    response = normalize(raw_response, MEMORY_SEARCH_RULES)
    return response


def normalize_memory_operation(raw_response: dict) -> dict:
    """Normalize a memory operation response (add/update/delete) and add computed fields."""
    response = normalize(raw_response, MEMORY_OPERATION_RULES)
    return response


def normalize_entity_list(raw_response: dict) -> dict:
    """Normalize an entity list response and add computed fields."""
    response = normalize(raw_response, ENTITY_LIST_RULES)
    return response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mem0-mcp-server")

MEM0_MCP_SERVER_PORT = int(os.getenv("MEM0_MCP_SERVER_PORT", "5000"))

def extract_auth_info(request_or_scope) -> tuple[str, str | None]:
    """Extract API key and User ID from headers or environment."""
    api_key = os.getenv("MEM0_API_KEY") or os.getenv("API_KEY")
    user_id = os.getenv("MEM0_DEFAULT_USER_ID", DEFAULT_MCP_USER_ID)
    
    auth_data = None
    # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
    if hasattr(request_or_scope, 'headers'):
        # SSE request object
        auth_data = request_or_scope.headers.get(b'x-auth-data')
        if auth_data and isinstance(auth_data, bytes):
            auth_data = base64.b64decode(auth_data).decode('utf-8')
    elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
        # StreamableHTTP scope object
        headers = dict(request_or_scope.get("headers", []))
        auth_data = headers.get(b'x-auth-data')
        if auth_data:
            auth_data = base64.b64decode(auth_data).decode('utf-8')
    
    if auth_data:
        try:
            # Parse the JSON auth data to extract token and user_id
            auth_json = json.loads(auth_data)
            
            # Extract API key if not already set or if we want to allow override (logic below prefers existing api_key if set, 
            # but usually we might want request to override. The original code preferred env var if set. 
            # Let's stick to original behavior for API key but check for user_id)
            extracted_key = auth_json.get('token') or auth_json.get('api_key')
            if extracted_key and not api_key:
                api_key = extracted_key
                
            # Extract user_id
            extracted_user = auth_json.get('user_id')
            if extracted_user:
                user_id = extracted_user
                
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse auth data JSON: {e}")
    
    return api_key or "", user_id

def _with_default_filters(
    default_user_id: str, filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Ensure filters exist and include the default user_id at the top level."""
    if not filters:
        return {"AND": [{"user_id": default_user_id}]}
    if not any(key in filters for key in ("AND", "OR", "NOT")):
        filters = {"AND": [filters]}
    has_user = json.dumps(filters, sort_keys=True).find('"user_id"') != -1
    if not has_user:
        and_list = filters.setdefault("AND", [])
        if not isinstance(and_list, list):
            raise ValueError("filters['AND'] must be a list when present.")
        and_list.insert(0, {"user_id": default_user_id})
    return filters

@click.command()
@click.option("--port", default=MEM0_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("mem0-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="mem0_add_memory",
                description="Store a new preference, fact, or conversation snippet. Requires at least one: user_id, agent_id, or run_id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Plain sentence summarizing what to store. Required even if `messages` is provided.",
                        },
                        "content": {
                            "type": "string",
                            "description": "Legacy alias of `text`.",
                        },
                        "messages": {
                            "type": "array",
                            "description": "Structured conversation history with `role`/`content`. Use when you have multiple turns.",
                            "items": {
                                "type": "object",
                                "required": ["role", "content"],
                                "properties": {
                                    "role": {"type": "string"},
                                    "content": {"type": "string"},
                                },
                            },
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user. If not specified, the system uses the default user. Do NOT fill with a random value."
                        },
                        "agent_id": {"type": "string", "description": "Optional agent identifier."},
                        "app_id": {"type": "string", "description": "Optional app identifier."},
                        "run_id": {"type": "string", "description": "Optional run identifier."},
                        "metadata": {
                            "type": "object",
                            "description": "Attach arbitrary metadata JSON to the memory.",
                            "additionalProperties": True,
                        },
                        "enable_graph": {
                            "type": "boolean",
                            "description": "Set true only if the caller explicitly wants Mem0 graph memory.",
                        },
                    },
                    "anyOf": [{"required": ["text"]}, {"required": ["content"]}, {"required": ["messages"]}],
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY"})
            ),
            types.Tool(
                name="mem0_get_memories",
                description="""Page through memories using filters instead of search.

        Use filters to list specific memories. Common filter patterns:
        - Single user: {"AND": [{"user_id": "john"}]}
        - Agent memories: {"AND": [{"agent_id": "agent_name"}]}
        - Recent memories: {"AND": [{"user_id": "john"}, {"created_at": {"gte": "2024-01-01"}}]}
        - Multiple users: {"AND": [{"user_id": {"in": ["john", "jane"]}}]}

        Pagination: Use page (1-indexed) and page_size for browsing results.
        user_id is automatically added to filters if not provided.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "object",
                            "description": "Structured filters; user_id injected automatically.",
                            "additionalProperties": True,
                        },
                        "page": {
                            "type": "integer",
                            "description": "1-indexed page number when paginating.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of memories per page (default 10).",
                        },
                        "enable_graph": {
                            "type": "boolean",
                            "description": "Set true only if the caller explicitly wants graph-derived memories.",
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user. If not specified, the system uses the default user. Do NOT fill with a random value.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mem0_search_memories",
                description="""Run a semantic search over existing memories.

        Use filters to narrow results. Common filter patterns:
        - Single user: {"AND": [{"user_id": "john"}]}
        - Agent memories: {"AND": [{"agent_id": "agent_name"}]}
        - Recent memories: {"AND": [{"user_id": "john"}, {"created_at": {"gte": "2024-01-01"}}]}
        - Multiple users: {"AND": [{"user_id": {"in": ["john", "jane"]}}]}
        - Cross-entity: {"OR": [{"user_id": "john"}, {"agent_id": "agent_name"}]}

        user_id is automatically added to filters if not provided.""",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language description of what to find."
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Unique identifier for the user. If not specified, the system uses the default user. Do NOT fill with a random value."
                        },
                        "filters": {
                            "type": "object",
                            "description": "Additional filter clauses (user_id injected automatically).",
                            "additionalProperties": True,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return.",
                            "default": 20
                        },
                        "enable_graph": {
                            "type": "boolean",
                            "description": "Set true only when the user explicitly wants graph-derived memories.",
                        },
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY", "readOnlyHint": True})
            ),
            types.Tool(
                name="mem0_get_memory",
                description="Fetch a single memory once you know its memory_id.",
                inputSchema={
                    "type": "object",
                    "required": ["memory_id"],
                    "properties": {"memory_id": {"type": "string", "description": "Exact memory_id to fetch."}},
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mem0_list_entities",
                description="List which users/agents/apps/runs currently hold memories.",
                inputSchema={"type": "object", "properties": {}},
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mem0_update_memory",
                description="Overwrite an existing memory's text.",
                inputSchema={
                    "type": "object",
                    "required": ["memory_id"],
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "Exact memory_id to overwrite."
                        },
                        "text": {
                            "type": "string",
                            "description": "Replacement text for the memory."
                        },
                        "data": {
                            "type": "string",
                            "description": "Legacy alias of `text`.",
                        },
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY"})
            ),
            types.Tool(
                name="mem0_delete_memory",
                description="Delete one memory after the user confirms its memory_id.",
                inputSchema={
                    "type": "object",
                    "required": ["memory_id"],
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "Exact memory_id to delete."
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY"})
            ),
            types.Tool(
                name="mem0_delete_all_memories",
                description="Delete every memory in the given user/agent/app/run but keep the entity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "Unique identifier for the user. If not specified, the system uses the default user. Do NOT fill with a random value."},
                        "agent_id": {"type": "string", "description": "Optional agent scope to delete."},
                        "app_id": {"type": "string", "description": "Optional app scope to delete."},
                        "run_id": {"type": "string", "description": "Optional run scope to delete."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY"}),
            ),
            types.Tool(
                name="mem0_delete_entities",
                description="Remove a user/agent/app/run record entirely (and cascade-delete its memories).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "Unique identifier for the user to delete. If not specified, the system uses the default user. Do NOT fill with a random value."},
                        "agent_id": {"type": "string", "description": "Delete this agent and its memories."},
                        "app_id": {"type": "string", "description": "Delete this app and its memories."},
                        "run_id": {"type": "string", "description": "Delete this run and its memories."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY"}),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "mem0_add_memory":
            text = arguments.get("text") or arguments.get("content")
            messages = arguments.get("messages")
            user_id = arguments.get("user_id")
            agent_id = arguments.get("agent_id")
            app_id = arguments.get("app_id")
            run_id = arguments.get("run_id")
            metadata = arguments.get("metadata")
            enable_graph = arguments.get("enable_graph")
            if not text and not messages:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: provide at least one of text/content or messages",
                    )
                ]
            if not any([user_id, agent_id, run_id]) and not get_mem0_user_id():
                return [
                    types.TextContent(
                        type="text",
                        text="Error: provide at least one of user_id, agent_id, or run_id (or configure a default user_id)",
                    )
                ]
            try:
                result = await add_memory(
                    text=text or "",
                    messages=messages,
                    user_id=user_id,
                    agent_id=agent_id,
                    app_id=app_id,
                    run_id=run_id,
                    metadata=metadata,
                    enable_graph=enable_graph,
                )
                # Normalize the response
                normalized_result = normalize_memory_operation(result)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(normalized_result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mem0_get_memories":
            filters = arguments.get("filters")
            page = arguments.get("page")
            page_size = arguments.get("page_size")
            enable_graph = arguments.get("enable_graph")
            user_id = arguments.get("user_id")
            
            default_user = user_id or get_mem0_user_id()
            
            if not filters and not default_user:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: provide filters (or user_id) to scope the listing; no default user_id is configured",
                    )
                ]
            try:
                if default_user:
                    filters = _with_default_filters(default_user, filters)

                result = await get_memories(filters=filters, page=page, page_size=page_size, enable_graph=enable_graph)
                # Normalize the response
                normalized_result = normalize_memory_list(result)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(normalized_result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "mem0_search_memories":
            query = arguments.get("query")
            limit = arguments.get("limit", 20)
            filters = arguments.get("filters")
            enable_graph = arguments.get("enable_graph")
            user_id = arguments.get("user_id")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            default_user = user_id or get_mem0_user_id()
            
            if not filters and not default_user:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: provide filters or user_id to scope the search; no default user_id is configured",
                    )
                ]
            try:
                if default_user:
                    filters = _with_default_filters(default_user, filters)

                result = await search_memories(
                    query=query,
                    user_id=None,
                    filters=filters,
                    limit=limit,
                    enable_graph=enable_graph,
                )
                # Normalize the response
                normalized_result = normalize_memory_search(result)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(normalized_result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mem0_get_memory":
            memory_id = arguments.get("memory_id")
            if not memory_id:
                return [types.TextContent(type="text", text="Error: memory_id parameter is required")]
            try:
                result = await get_memory(memory_id)
                # Normalize the response - single memory from result field
                if result.get('success') and result.get('result'):
                    normalized_result = normalize_memory(result['result'])
                else:
                    normalized_result = normalize_memory_operation(result)
                return [types.TextContent(type="text", text=json.dumps(normalized_result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "mem0_list_entities":
            try:
                result = await list_entities()
                # Normalize the response
                normalized_result = normalize_entity_list(result)
                return [types.TextContent(type="text", text=json.dumps(normalized_result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "mem0_update_memory":
            memory_id = arguments.get("memory_id")
            text = arguments.get("text") or arguments.get("data")
            if not memory_id or not text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: memory_id and text/data parameters are required",
                    )
                ]
            try:
                result = await update_memory(memory_id, text)
                # Normalize the response
                normalized_result = normalize_memory_operation(result)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(normalized_result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mem0_delete_memory":
            memory_id = arguments.get("memory_id")
            if not memory_id:
                return [types.TextContent(type="text", text="Error: memory_id parameter is required")]
            try:
                result = await delete_memory(memory_id)
                # Normalize the response
                normalized_result = normalize_memory_operation(result)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(normalized_result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "mem0_delete_all_memories":
            try:
                result = await delete_all_memories(
                    user_id=arguments.get("user_id"),
                    agent_id=arguments.get("agent_id"),
                    app_id=arguments.get("app_id"),
                    run_id=arguments.get("run_id"),
                )
                # Normalize the response
                normalized_result = normalize_memory_operation(result)
                return [types.TextContent(type="text", text=json.dumps(normalized_result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "mem0_delete_entities":
            try:
                result = await delete_entities(
                    user_id=arguments.get("user_id"),
                    agent_id=arguments.get("agent_id"),
                    app_id=arguments.get("app_id"),
                    run_id=arguments.get("run_id"),
                )
                # Normalize the response
                normalized_result = normalize_memory_operation(result)
                return [types.TextContent(type="text", text=json.dumps(normalized_result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract API key and User ID
        api_key, user_id = extract_auth_info(request)
        
        # Set context
        token_key = mem0_api_key_context.set(api_key or "")
        token_user = mem0_user_id_context.set(user_id)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            mem0_api_key_context.reset(token_key)
            mem0_user_id_context.reset(token_user)
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract API key and User ID
        api_key, user_id = extract_auth_info(scope)
        
        # Set context
        token_key = mem0_api_key_context.set(api_key or "")
        token_user = mem0_user_id_context.set(user_id)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            mem0_api_key_context.reset(token_key)
            mem0_user_id_context.reset(token_user)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()
