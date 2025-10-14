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

async def perplexity_search(messages: List[Dict[str, str]]) -> str:
    """
    Performs web search using the Sonar API.
    Accepts an array of messages (each with a role and content)
    and returns a search completion response from the Perplexity model.
    
    Args:
        messages: Array of conversation messages with role and content
    
    Returns:
        Search completion response with citations if available
    """
    return await perform_chat_completion(messages, "sonar-pro")



async def perplexity_reason(messages: List[Dict[str, str]]) -> str:
    """
    Performs reasoning tasks using Perplexity's reasoning-optimized model.
    Accepts an array of messages and returns a reasoned response.
    
    Args:
        messages: Array of conversation messages with role and content
    
    Returns:
        Reasoned response with citations if available
    """
    return await perform_chat_completion(messages, "sonar-reasoning-pro")
