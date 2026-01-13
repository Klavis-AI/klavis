from typing import Any, Dict, Optional, List
import logging
import os
from .base import RazorpayClient
from .Constants import Version

logger = logging.getLogger(__name__)

version = Version.V1

    
async def fetch_document_information(
        document_id:str
)->Dict[str,Any]:
    
    """
    Use this endpoint to retrieve the details of any document that was uploaded earlier.
    Args:
        document_id:str
    Returns:
        fetched document dictionary 
    """
    
    if(not document_id or not isinstance(document_id,str)):
        raise ValueError('document id must be a non-empty string')
    
    try:
        result = await RazorpayClient.make_request(
            method="GET",
            endpoint=f"/documents/{document_id}",
            data=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while fetching document: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while fetching document",
            "details": str(e),
        }
    

async def fetch_document_content(
        document_id:str
)->Dict[str,Any]:
    
    """
    Use this endpoint to download an earlier uploaded document.
    Args:
        document_id:str
    Returns:
        Error dictionary if failure
    """
    
    if(not document_id or not isinstance(document_id,str)):
        raise ValueError('document id must be a non-empty string')
    
    try:
        result = await RazorpayClient.make_request(
            method="POST",
            endpoint=f"/documents/{document_id}/content",
            data=None,
            version=version
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.exception(f"Razorpay API call failed while downloading document: {e}")
        return {
            "success": False,
            "error": "An external API error occurred while downloading document",
            "details": str(e),
        }