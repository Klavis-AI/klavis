import logging
from typing import Any, Dict

from ..utils import _extract_video_id, _format_time, youtube_transcript_api, TRANSCRIPT_LANGUAGES
from .videos import get_video_details

logger = logging.getLogger(__name__)

async def get_youtube_video_transcript(url: str) -> Dict[str, Any]:
    """
    Retrieve the transcript or video details for a given YouTube video.
    The 'start' time in the transcript is formatted as MM:SS or HH:MM:SS.
    """
    try:
        video_id = _extract_video_id(url)
        logger.info(f"Executing tool: get_video_transcript with video_id: {video_id}")
        
        try:
            # Use the initialized API with or without proxy
            raw_transcript = youtube_transcript_api.fetch(video_id, languages=TRANSCRIPT_LANGUAGES).to_raw_data()

            # Format the start time for each segment
            formatted_transcript = [
                {**segment, 'start': _format_time(segment['start'])} 
                for segment in raw_transcript
            ]

            return {
                "video_id": video_id,
                "transcript": formatted_transcript
            }
        except Exception as transcript_error:
            logger.warning(f"Error fetching transcript: {transcript_error}. Falling back to video details.")
            # Fall back to get_video_details
            video_details = await get_video_details(video_id)
            return {
                "video_id": video_id,
                "video_details": video_details,
            }
    except ValueError as e:
        logger.exception(f"Invalid YouTube URL: {e}")
        return {
            "error": f"Invalid YouTube URL: {str(e)}"
        }
    except Exception as e:
        error_message = str(e)
        logger.exception(f"Error processing video URL {url}: {error_message}")
        return {
            "error": f"Failed to process request: {error_message}"
        }
