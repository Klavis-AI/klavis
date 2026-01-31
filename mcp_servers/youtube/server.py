import contextlib
import logging
import os
from collections.abc import AsyncIterator

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from tools.base import extract_access_token, auth_token_context
from tools.transcripts import get_youtube_video_transcript
from tools.account import get_liked_videos, get_user_subscriptions, get_my_videos, get_recent_uploads
from tools.channels import get_my_channel_info, get_channel_videos, search_channels, get_my_channel_analytics
from tools.videos import get_video_details, rate_video, search_videos, get_my_video_analytics
from tools.playlists import create_playlist, add_video_to_playlist, list_playlists, get_playlist_items

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

YOUTUBE_MCP_SERVER_PORT = int(os.getenv("YOUTUBE_MCP_SERVER_PORT", "5000"))

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
            ),
            types.Tool(
                name="youtube_get_liked_videos",
                description="Get the user's liked/favorite videos from their YouTube account. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (default: 25, max: 50)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_subscriptions",
                description="Get the user's channel subscriptions from their YouTube account. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of subscriptions to return (default: 25, max: 50)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_my_channel",
                description="Get information about the authenticated user's YouTube channel including subscriber count, video count, and total views. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_my_videos",
                description="Get the authenticated user's uploaded videos with statistics. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (default: 25, max: 50)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_search_videos",
                description="Search for YouTube videos by query, optionally filtered by channel or date range. Use this to find videos about specific topics from any YouTuber.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string (e.g., 'machine learning tutorial')",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10, max: 50)",
                            "default": 10
                        },
                        "channel_id": {
                            "type": "string",
                            "description": "Optional: Filter results to a specific channel ID",
                        },
                        "published_after": {
                            "type": "string",
                            "description": "Optional: Only return videos published after this date (ISO 8601 format, e.g., '2024-01-01T00:00:00Z')",
                        },
                        "published_before": {
                            "type": "string",
                            "description": "Optional: Only return videos published before this date (ISO 8601 format)",
                        },
                        "order": {
                            "type": "string",
                            "enum": ["relevance", "date", "viewCount", "rating"],
                            "description": "Sort order for results (default: 'relevance')",
                            "default": "relevance"
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_SEARCH", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_channel_videos",
                description="Get videos from a specific YouTube channel. Use this to browse a YouTuber's uploaded videos.",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The YouTube channel ID (e.g., 'UC_x5XG1OV2P6uZZ5FSM9Ttw')",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (default: 25, max: 50)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_CHANNEL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_search_channels",
                description="Search for YouTube channels by name or keywords. Use this to find a YouTuber's channel ID.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for channel name or keywords",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10, max: 50)",
                            "default": 10
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_SEARCH", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_my_analytics",
                description="Get analytics for the authenticated user's YouTube channel including views, watch time, likes, comments, and subscriber changes. Requires OAuth authentication with YouTube Analytics scope.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (default: 30 days ago)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (default: today)",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ANALYTICS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_video_analytics",
                description="Get analytics for a specific video on the authenticated user's channel. Requires OAuth authentication with YouTube Analytics scope.",
                inputSchema={
                    "type": "object",
                    "required": ["video_id"],
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "The YouTube video ID",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (default: 30 days ago)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (default: today)",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ANALYTICS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_recent_uploads",
                description="Get videos uploaded within the specified number of days from your subscribed channels. Great for seeing what's new from channels you follow. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 14)",
                            "default": 14
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 25)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_video_details",
                description="Get detailed information about a specific YouTube video including title, description, and statistics.",
                inputSchema={
                    "type": "object",
                    "required": ["video_id"],
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "The YouTube video ID",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_SEARCH", "readOnlyHint": True}),
            ),
            # NOTE: Commented out because it requires youtube.force-ssl scope
            # types.Tool(
            #     name="youtube_get_video_comments",
            #     description="Get top-level comments for a video. Useful for analyzing viewer sentiment and questions. Requires OAuth authentication.",
            #     inputSchema={
            #         "type": "object",
            #         "required": ["video_id"],
            #         "properties": {
            #             "video_id": {
            #                 "type": "string",
            #                 "description": "The YouTube video ID",
            #             },
            #             "max_results": {
            #                 "type": "integer",
            #                 "description": "Maximum number of comments to return (default: 20)",
            #                 "default": 20
            #             },
            #             "order": {
            #                 "type": "string",
            #                 "enum": ["relevance", "time"],
            #                 "description": "Sort order for comments (default: 'relevance')",
            #                 "default": "relevance"
            #             },
            #         },
            #     },
            #     annotations=types.ToolAnnotations(**{"category": "YOUTUBE_COMMUNITY", "readOnlyHint": True}),
            # ),
            types.Tool(
                name="youtube_list_playlists",
                description="List playlists for a channel or the authenticated user. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Optional channel ID to list playlists for. If not provided and 'mine' is false, defaults to authenticated user.",
                        },
                        "mine": {
                            "type": "boolean",
                            "description": "Whether to list the authenticated user's playlists (default: false, but implied if channel_id is missing)",
                            "default": False
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of playlists to return (default: 25)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_PLAYLISTS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_playlist_items",
                description="Get items (videos) from a specific playlist. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "required": ["playlist_id"],
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "The ID of the playlist",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of items to return (default: 25)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_PLAYLISTS", "readOnlyHint": True}),
            ),
            # Write tools
            types.Tool(
                name="youtube_rate_video",
                description="Rate a YouTube video (like, dislike, or remove rating). Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "required": ["video_id", "rating"],
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "The YouTube video ID to rate",
                        },
                        "rating": {
                            "type": "string",
                            "enum": ["like", "dislike", "none"],
                            "description": "The rating to apply: 'like' to like the video, 'dislike' to dislike it, or 'none' to remove your rating",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": False}),
            ),
            types.Tool(
                name="youtube_create_playlist",
                description="Create a new YouTube playlist on the authenticated user's channel. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the playlist",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the playlist (optional)",
                            "default": ""
                        },
                        "privacy_status": {
                            "type": "string",
                            "enum": ["public", "private", "unlisted"],
                            "description": "Privacy status of the playlist (default: 'private')",
                            "default": "private"
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_PLAYLISTS", "readOnlyHint": False}),
            ),
            types.Tool(
                name="youtube_add_video_to_playlist",
                description="Add a video to an existing YouTube playlist. Requires OAuth authentication and ownership of the playlist.",
                inputSchema={
                    "type": "object",
                    "required": ["playlist_id", "video_id"],
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "The ID of the playlist to add the video to",
                        },
                        "video_id": {
                            "type": "string",
                            "description": "The YouTube video ID to add to the playlist",
                        },
                        "position": {
                            "type": "integer",
                            "description": "The position in the playlist to insert the video (0-indexed). If not specified, the video is added to the end.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_PLAYLISTS", "readOnlyHint": False}),
            ),
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
        
        elif name == "youtube_get_liked_videos":
            try:
                max_results = arguments.get("max_results", 25)
                result = await get_liked_videos(max_results)
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
        
        elif name == "youtube_get_subscriptions":
            try:
                max_results = arguments.get("max_results", 25)
                result = await get_user_subscriptions(max_results)
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
        
        elif name == "youtube_get_my_channel":
            try:
                result = await get_my_channel_info()
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
        
        elif name == "youtube_get_my_videos":
            try:
                max_results = arguments.get("max_results", 25)
                result = await get_my_videos(max_results)
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
        
        elif name == "youtube_search_videos":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            try:
                result = await search_videos(
                    query=query,
                    max_results=arguments.get("max_results", 10),
                    channel_id=arguments.get("channel_id"),
                    published_after=arguments.get("published_after"),
                    published_before=arguments.get("published_before"),
                    order=arguments.get("order", "relevance")
                )
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
        
        elif name == "youtube_get_channel_videos":
            channel_id = arguments.get("channel_id")
            if not channel_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id parameter is required",
                    )
                ]
            
            try:
                result = await get_channel_videos(
                    channel_id=channel_id,
                    max_results=arguments.get("max_results", 25)
                )
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
        
        elif name == "youtube_search_channels":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            try:
                result = await search_channels(
                    query=query,
                    max_results=arguments.get("max_results", 10)
                )
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
        
        elif name == "youtube_get_my_analytics":
            try:
                result = await get_my_channel_analytics(
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date")
                )
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
        
        elif name == "youtube_get_video_analytics":
            video_id = arguments.get("video_id")
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            
            try:
                result = await get_my_video_analytics(
                    video_id=video_id,
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date")
                )
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
        
        elif name == "youtube_get_recent_uploads":
            try:
                result = await get_recent_uploads(
                    days=arguments.get("days", 14),
                    max_results=arguments.get("max_results", 25)
                )
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
        
        elif name == "youtube_get_video_details":
            video_id = arguments.get("video_id")
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            
            try:
                result = await get_video_details(video_id=video_id)
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
        
        # NOTE: Commented out because it requires youtube.force-ssl scope
        # elif name == "youtube_get_video_comments":
        #     video_id = arguments.get("video_id")
        #     if not video_id:
        #         return [
        #             types.TextContent(
        #                 type="text",
        #                 text="Error: video_id parameter is required",
        #             )
        #         ]
        #     
        #     try:
        #         result = await get_video_comments(
        #             video_id=video_id,
        #             max_results=arguments.get("max_results", 20),
        #             order=arguments.get("order", "relevance")
        #         )
        #         return [
        #             types.TextContent(
        #                 type="text",
        #                 text=str(result),
        #             )
        #         ]
        #     except Exception as e:
        #         logger.exception(f"Error executing tool {name}: {e}")
        #         return [
        #             types.TextContent(
        #                 type="text",
        #                 text=f"Error: {str(e)}",
        #             )
        #         ]
        
        elif name == "youtube_list_playlists":
            try:
                result = await list_playlists(
                    channel_id=arguments.get("channel_id"),
                    mine=arguments.get("mine", False),
                    max_results=arguments.get("max_results", 25)
                )
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
        
        elif name == "youtube_get_playlist_items":
            playlist_id = arguments.get("playlist_id")
            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: playlist_id parameter is required",
                    )
                ]
            
            try:
                result = await get_playlist_items(
                    playlist_id=playlist_id,
                    max_results=arguments.get("max_results", 25)
                )
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
        
        elif name == "youtube_rate_video":
            video_id = arguments.get("video_id")
            rating = arguments.get("rating")
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            if not rating:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: rating parameter is required",
                    )
                ]
            
            try:
                result = await rate_video(
                    video_id=video_id,
                    rating=rating
                )
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
        
        elif name == "youtube_create_playlist":
            title = arguments.get("title")
            if not title:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: title parameter is required",
                    )
                ]
            
            try:
                result = await create_playlist(
                    title=title,
                    description=arguments.get("description", ""),
                    privacy_status=arguments.get("privacy_status", "private")
                )
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
        
        elif name == "youtube_add_video_to_playlist":
            playlist_id = arguments.get("playlist_id")
            video_id = arguments.get("video_id")
            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: playlist_id parameter is required",
                    )
                ]
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            
            try:
                result = await add_video_to_playlist(
                    playlist_id=playlist_id,
                    video_id=video_id,
                    position=arguments.get("position")
                )
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

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract auth token from headers
        auth_token = extract_access_token(request)
        
        # Set the auth token in context for this request
        token = auth_token_context.set(auth_token)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)
        
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
        
        # Extract auth token from headers
        auth_token = extract_access_token(scope)
        
        # Set the auth token in context for this request
        token = auth_token_context.set(auth_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

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
