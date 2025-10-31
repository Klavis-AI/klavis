import contextlib
import logging
import os
import re
from collections.abc import AsyncIterator
from typing import Any, Dict
from urllib.parse import urlparse, parse_qs

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from pydantic import Field
from dotenv import load_dotenv
import aiohttp
import asyncio
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# YouTube API constants and configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY environment variable is required")

# Proxy configuration
WEBSHARE_PROXY_USERNAME = os.getenv("WEBSHARE_PROXY_USERNAME")
WEBSHARE_PROXY_PASSWORD = os.getenv("WEBSHARE_PROXY_PASSWORD")

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_MCP_SERVER_PORT = int(os.getenv("YOUTUBE_MCP_SERVER_PORT", "5000"))
TRANSCRIPT_LANGUAGES = [lang.strip() for lang in os.getenv("TRANSCRIPT_LANGUAGE", "en").split(',')]

# Initialize YouTube Transcript API with proxy if credentials are available
if WEBSHARE_PROXY_USERNAME and WEBSHARE_PROXY_PASSWORD:
    logger.info("Initializing YouTubeTranscriptApi with Webshare proxy")
    youtube_transcript_api = YouTubeTranscriptApi(
        proxy_config=WebshareProxyConfig(
            proxy_username=WEBSHARE_PROXY_USERNAME,
            proxy_password=WEBSHARE_PROXY_PASSWORD,
            retries_when_blocked=50
        )
    )
else:
    logger.info("Initializing YouTubeTranscriptApi without proxy")
    youtube_transcript_api = YouTubeTranscriptApi()

def _format_time(seconds: float) -> str:
    """Converts seconds into HH:MM:SS or MM:SS format."""
    total_seconds = int(seconds)
    minutes, sec = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    else:
        return f"{minutes:02d}:{sec:02d}"

def _extract_video_id(url: str) -> str:
    """
    Extract the YouTube video ID from various URL formats.
    Supports standard youtube.com URLs and youtu.be short URLs.
    
    Args:
        url: YouTube URL in various formats
        
    Returns:
        The video ID extracted from the URL
        
    Raises:
        ValueError: If the URL is not a valid YouTube URL or if video ID couldn't be extracted
    """
    if not url:
        raise ValueError("Empty URL provided")
        
    # Pattern 1: Standard YouTube URL (youtube.com/watch?v=VIDEO_ID)
    if "youtube.com/watch" in url:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        video_ids = query_params.get("v")
        if video_ids and len(video_ids[0]) > 0:
            return video_ids[0]
            
    # Pattern 2: Short YouTube URL (youtu.be/VIDEO_ID)
    if "youtu.be/" in url:
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and path.startswith("/"):
            return path[1:].split("?")[0]
            
    # Pattern 3: Embedded YouTube URL (youtube.com/embed/VIDEO_ID)
    if "youtube.com/embed/" in url:
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and path.startswith("/embed/"):
            return path[7:].split("?")[0]
            
    # Pattern 4: YouTube shorts URL (youtube.com/shorts/VIDEO_ID)
    if "youtube.com/shorts/" in url:
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and path.startswith("/shorts/"):
            return path[8:].split("?")[0]
    
    raise ValueError(f"Could not extract video ID from URL: {url}")

async def _make_youtube_request(endpoint: str, params: Dict[str, Any], headers: Dict[str, Any] = None) -> Any:
    """
    Makes an HTTP request to the YouTube Data API.
    """
    params["key"] = YOUTUBE_API_KEY
    url = f"{YOUTUBE_API_BASE}/{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                if endpoint == "captions/download":
                    return await response.text()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"YouTube API request failed: {e.status} {e.message} for GET {url}")
            error_details = e.message
            try:
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                pass
            raise RuntimeError(f"YouTube API Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during YouTube API request: {e}")
            raise RuntimeError(f"Unexpected error during API call to {url}") from e

async def get_video_details(video_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific YouTube video."""
    logger.info(f"Executing tool: get_video_details with video_id: {video_id}")
    try:
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id
        }
        
        result = await _make_youtube_request("videos", params)
        
        if not result.get("items"):
            return {"error": f"No video found with ID: {video_id}"}
        
        video = result["items"][0]
        snippet = video.get("snippet", {})
        content_details = video.get("contentDetails", {})
        statistics = video.get("statistics", {})
        
        return {
            "id": video.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "publishedAt": snippet.get("publishedAt"),
            "channelId": snippet.get("channelId"),
            "channelTitle": snippet.get("channelTitle"),
            "thumbnailUrl": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "tags": snippet.get("tags", []),
            "categoryId": snippet.get("categoryId"),
            "duration": content_details.get("duration"),
            "viewCount": statistics.get("viewCount"),
            "likeCount": statistics.get("likeCount"),
            "commentCount": statistics.get("commentCount"),
            "url": f"https://www.youtube.com/watch?v={video_id}"
        }
    except Exception as e:
        logger.exception(f"Error executing tool get_video_details: {e}")
        raise e


@click.command()
@click.option("--port", default=YOUTUBE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("youtube-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="get_youtube_video_transcript",
                description="Retrieve the transcript or video details for a given YouTube video. The 'start' time in the transcript is formatted as MM:SS or HH:MM:SS.",
                inputSchema={
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the YouTube video to retrieve the transcript/subtitles for. (e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ)",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_TRANSCRIPT", "readOnlyHint": True}),
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        if name == "get_youtube_video_transcript":
            url = arguments.get("url")
            if not url:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: URL parameter is required",
                    )
                ]
            
            try:
                result = await get_youtube_video_transcript(url)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
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
        
        return [
            types.TextContent(
                type="text",
                text=f"Unknown tool: {name}",
            )
        ]

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

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )
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
        await session_manager.handle_request(scope, receive, send)

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