"""
Video generation tools for HeyGen API.
"""

from typing import Dict, Any, Optional
from .base import make_request

async def heygen_generate_avatar_video(
    avatar_id: str,
    text: str,
    voice_id: str,
    background_color: Optional[str] = "#ffffff",
    width: Optional[int] = 1280,
    height: Optional[int] = 720,
    avatar_style: Optional[str] = "normal"
) -> Dict[str, Any]:
    """
    Generate a new avatar video with the specified avatar, text, and voice.
    
    Args:
        avatar_id: The ID of the avatar to use
        text: The text for the avatar to speak (max 1500 characters)
        voice_id: The ID of the voice to use
        background_color: Background color in hex format (default: #ffffff)
        width: Video width in pixels (default: 1280)
        height: Video height in pixels (default: 720)
        avatar_style: Avatar style (default: normal)
        
    Returns:
        Dict containing video generation response with video_id
    """
    if len(text) > 1500:
        raise ValueError("Text input must be less than 1500 characters")
    
    video_data = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": avatar_style
                },
                "voice": {
                    "type": "text",
                    "input_text": text,
                    "voice_id": voice_id
                },
                "background": {
                    "type": "color",
                    "value": background_color
                }
            }
        ],
        "dimension": {
            "width": width,
            "height": height
        }
    }
    
    return await make_request("POST", "/v2/video/generate", data=video_data)

async def heygen_get_avatar_video_status(video_id: str) -> Dict[str, Any]:
    """
    Retrieve the status of a video generated via the HeyGen API.
    
    Args:
        video_id: The ID of the video to check status for
        
    Returns:
        Dict containing video status information
    """
    return await make_request("GET", "/v1/video_status.get", params={"video_id": video_id})