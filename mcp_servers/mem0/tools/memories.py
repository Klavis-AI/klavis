import logging
from typing import Any, Dict
from .base import get_mem0_client, get_user_id

# Configure logging
logger = logging.getLogger(__name__)

async def add_memory(content: str, user_id: str = None) -> Dict[str, Any]:
    """Add a new memory to mem0."""
    if not user_id:
        user_id = get_user_id()
    
    logger.info(f"Adding memory for user: {user_id}")
    try:
        mem0_client = get_mem0_client()
        messages = [{"role": "user", "content": content}]
        result = mem0_client.add(messages, user_id=user_id, output_format="v1.1")
        logger.info(f"Successfully added memory for user {user_id}")
        return {
            "success": True,
            "message": f"Successfully added memory: {content[:100]}{'...' if len(content) > 100 else ''}",
            "user_id": user_id
        }
        
    except Exception as e:
        logger.exception(f"Error adding memory: {e}")
        raise e

async def get_all_memories(user_id: str = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
    """Get all memories for a user."""
    if not user_id:
        user_id = get_user_id()
        
    logger.info(f"Getting all memories for user: {user_id}")
    try:
        mem0_client = get_mem0_client()
        memories = mem0_client.get_all(user_id=user_id, page=page, page_size=page_size)
        flattened_memories = [memory["memory"] for memory in memories["results"]]
        
        logger.info(f"Retrieved {len(flattened_memories)} memories for user {user_id}")
        return {
            "success": True,
            "memories": flattened_memories,
            "user_id": user_id,
            "total_results": len(flattened_memories),
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.exception(f"Error getting memories: {e}")
        raise e

async def search_memories(query: str, user_id: str = None, limit: int = 20) -> Dict[str, Any]:
    """Search memories using semantic search."""
    if not user_id:
        user_id = get_user_id()
        
    logger.info(f"Searching memories for user {user_id} with query: {query}")
    try:
        mem0_client = get_mem0_client()
        memories = mem0_client.search(query, user_id=user_id, output_format="v1.1")
        flattened_memories = [memory["memory"] for memory in memories["results"][:limit]]
        
        logger.info(f"Found {len(flattened_memories)} matching memories for user {user_id}")
        return {
            "success": True,
            "memories": flattened_memories,
            "user_id": user_id,
            "query": query,
            "total_results": len(flattened_memories)
        }
    except Exception as e:
        logger.exception(f"Error searching memories: {e}")
        raise e