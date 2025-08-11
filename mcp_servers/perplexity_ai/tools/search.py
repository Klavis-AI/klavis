import logging
from typing import Any, Dict, List, Optional
from .base import make_perplexity_request

# Configure logging
logger = logging.getLogger(__name__)

async def perform_chat_completion(
    messages: List[Dict[str, str]],
    model: str = "sonar-pro"
) -> str:
    """
    Performs a chat completion by sending a request to the Perplexity API.
    Appends citations to the returned message content if they exist.
    
    Args:
        messages: An array of message objects with role and content
        model: The model to use for the completion
    
    Returns:
        The chat completion result with appended citations
    """
    try:
        data = {
            "model": model,
            "messages": messages
        }
        
        result = await make_perplexity_request("chat/completions", "POST", data)
        
        # Get the main message content from the response
        message_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # If citations are provided, append them to the message content
        citations = result.get("citations", [])
        if citations and isinstance(citations, list) and len(citations) > 0:
            message_content += "\n\nCitations:\n"
            for index, citation in enumerate(citations):
                message_content += f"[{index + 1}] {citation}\n"
        
        return message_content
        
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise e

async def perplexity_ask(messages: List[Dict[str, str]]) -> str:
    """
    Engages in a conversation using the Sonar API.
    Accepts an array of messages (each with a role and content)
    and returns a chat completion response from the Perplexity model.
    
    Args:
        messages: Array of conversation messages with role and content
    
    Returns:
        Chat completion response with citations if available
    """
    return await perform_chat_completion(messages, "sonar-pro")

async def perplexity_research(messages: List[Dict[str, str]]) -> str:
    """
    Performs deep research using the Perplexity API.
    Accepts an array of messages (each with a role and content)
    and returns a comprehensive research response with citations.
    
    Args:
        messages: Array of conversation messages with role and content
    
    Returns:
        Comprehensive research response with citations
    """
    return await perform_chat_completion(messages, "sonar-deep-research")

async def perplexity_reason(messages: List[Dict[str, str]]) -> str:
    """
    Performs reasoning tasks using the Perplexity API.
    Accepts an array of messages (each with a role and content)
    and returns a well-reasoned response using the sonar-reasoning-pro model.
    
    Args:
        messages: Array of conversation messages with role and content
    
    Returns:
        Well-reasoned response using reasoning model
    """
    return await perform_chat_completion(messages, "sonar-reasoning-pro")
