import logging
from typing import Any, Dict, Optional

from .base import (
    default_enable_graph, 
    get_mem0_client, 
    mem0_call, 
    with_default_filters, 
    get_mem0_user_id
)

# Configure logging
logger = logging.getLogger(__name__)

async def add_memory(
    text: str,
    messages: Optional[list[Dict[str, str]]] = None,
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    app_id: Optional[str] = None,
    run_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    enable_graph: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Official-style add_memory:
    - Accept either `messages` (role/content list) or derive from `text`
    - Scope can be by user_id OR agent_id/run_id (if those are provided, user_id can be omitted)
    """
    if not any([user_id, agent_id, run_id]) and not get_mem0_user_id():
        return {
            "success": False,
            "error": "scope_missing",
            "detail": "Provide at least one of user_id, agent_id, or run_id.",
        }
    resolved_user_id = user_id or get_mem0_user_id()

    logger.info(
        "Adding memory (user_id=%s agent_id=%s app_id=%s run_id=%s)",
        resolved_user_id,
        agent_id,
        app_id,
        run_id,
    )

    if not messages and not text:
        return {
            "success": False,
            "error": "messages_missing",
            "detail": "Provide either `text` or `messages` so Mem0 knows what to store.",
        }
    conversation = messages if messages else [{"role": "user", "content": text}]
    payload: Dict[str, Any] = {
        "user_id": resolved_user_id,
        "agent_id": agent_id,
        "app_id": app_id,
        "run_id": run_id,
        "metadata": metadata,
        "enable_graph": default_enable_graph(enable_graph),
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    mem0_client = get_mem0_client()
    result = mem0_call(mem0_client.add, conversation, **payload)
    if result.get("success"):
        result["scope"] = {
            "user_id": resolved_user_id,
            "agent_id": agent_id,
            "app_id": app_id,
            "run_id": run_id,
        }
    return result

async def get_memories(
    filters: Optional[Dict[str, Any]] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    enable_graph: Optional[bool] = None,
) -> Dict[str, Any]:
    """List memories with filters + pagination. No implicit user_id is injected."""
    if not filters and not get_mem0_user_id():
        return {
            "success": False,
            "error": "filters_missing",
            "detail": "Provide `filters` (for example: {\"AND\": [{\"user_id\": \"...\"}]}) to list memories.",
        }
    resolved_filters = with_default_filters(filters, user_id=get_mem0_user_id())

    logger.info("Getting memories (page=%s page_size=%s)", page, page_size)
    mem0_client = get_mem0_client()
    payload: Dict[str, Any] = {
        "filters": resolved_filters,
        "page": page,
        "page_size": page_size,
        "enable_graph": default_enable_graph(enable_graph),
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return mem0_call(mem0_client.get_all, **payload)

async def search_memories(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    enable_graph: Optional[bool] = None,
    # Back-compat: allow passing user_id directly (converted into filters)
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Search memories. No implicit user_id is injected."""
    resolved_user_id = user_id or get_mem0_user_id()
    
    if not filters and not resolved_user_id:
        return {
            "success": False,
            "error": "scope_missing",
            "detail": "Provide either `filters` or `user_id` to scope the search.",
        }
    resolved_filters = filters if filters else {"AND": [{"user_id": resolved_user_id}]}
    resolved_filters = with_default_filters(resolved_filters, user_id=resolved_user_id)

    logger.info("Searching memories (query=%s limit=%s)", query, limit)
    mem0_client = get_mem0_client()
    payload: Dict[str, Any] = {
        "query": query,
        "filters": resolved_filters,
        "limit": limit,
        "enable_graph": default_enable_graph(enable_graph),
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return mem0_call(mem0_client.search, **payload)

async def get_memory(memory_id: str) -> Dict[str, Any]:
    """Retrieve a single memory once the user has picked an exact ID."""
    logger.info("Getting memory %s", memory_id)
    mem0_client = get_mem0_client()
    if not hasattr(mem0_client, "get"):
        return {
            "success": False,
            "error": "unsupported_client_method",
            "detail": "Mem0 client does not support `get(memory_id)`. Please upgrade mem0ai.",
        }
    return mem0_call(mem0_client.get, memory_id)

async def update_memory(memory_id: str, text: str) -> Dict[str, Any]:
    """Overwrite an existing memory’s text after the user confirms the exact memory_id."""
    logger.info("Updating memory %s", memory_id)
    mem0_client = get_mem0_client()
    return mem0_call(mem0_client.update, memory_id=memory_id, text=text)

async def delete_memory(
    memory_id: str,
) -> Dict[str, Any]:
    """Delete a memory once the user explicitly confirms the memory_id to remove."""
    logger.info("Deleting memory %s", memory_id)
    mem0_client = get_mem0_client()
    return mem0_call(mem0_client.delete, memory_id)

async def delete_all_memories(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    app_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Bulk-delete every memory in the confirmed scope."""
    resolved_user_id = user_id or get_mem0_user_id()
    
    if not any([resolved_user_id, agent_id, app_id, run_id]):
        return {
            "success": False,
            "error": "scope_missing",
            "detail": "Provide at least one of user_id, agent_id, app_id, or run_id.",
        }
    logger.info(
        "Deleting all memories (user_id=%s agent_id=%s app_id=%s run_id=%s)",
        resolved_user_id,
        agent_id,
        app_id,
        run_id,
    )
    mem0_client = get_mem0_client()
    payload: Dict[str, Any] = {
        "user_id": resolved_user_id,
        "agent_id": agent_id,
        "app_id": app_id,
        "run_id": run_id,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return mem0_call(mem0_client.delete_all, **payload)

async def list_entities() -> Dict[str, Any]:
    """List users/agents/apps/runs with stored memories."""
    logger.info("Listing entities")
    mem0_client = get_mem0_client()
    if not hasattr(mem0_client, "users"):
        return {
            "success": False,
            "error": "unsupported_client_method",
            "detail": "Mem0 client does not support `users()`. Please upgrade mem0ai.",
        }
    return mem0_call(mem0_client.users)

async def delete_entities(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    app_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete a user/agent/app/run (and its memories) once the user confirms the scope."""
    logger.info(
        "Deleting entities (user_id=%s agent_id=%s app_id=%s run_id=%s)",
        user_id,
        agent_id,
        app_id,
        run_id,
    )
    if not any([user_id, agent_id, app_id, run_id]):
        return {
            "success": False,
            "error": "scope_missing",
            "detail": "Provide user_id, agent_id, app_id, or run_id before calling delete_entities.",
        }
    mem0_client = get_mem0_client()
    if not hasattr(mem0_client, "delete_users"):
        return {
            "success": False,
            "error": "unsupported_client_method",
            "detail": "Mem0 client does not support `delete_users(...)`. Please upgrade mem0ai.",
        }
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "agent_id": agent_id,
        "app_id": app_id,
        "run_id": run_id,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return mem0_call(mem0_client.delete_users, **payload)