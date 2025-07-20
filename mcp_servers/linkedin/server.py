import os
import logging
import contextlib
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, Annotated

import click
import aiohttp
import urllib.parse
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from pydantic import Field

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("linkedin-mcp-server")

# LinkedIn API constants and configuration
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
if not LINKEDIN_ACCESS_TOKEN:
    raise ValueError("LINKEDIN_ACCESS_TOKEN environment variable is required")

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
LINKEDIN_MCP_SERVER_PORT = int(os.getenv("LINKEDIN_MCP_SERVER_PORT", "5000"))

# Helper function to create standard headers for LinkedIn API calls
def _get_linkedin_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

# Helper to make API requests and handle errors
async def _make_linkedin_request(method: str, endpoint: str, json_data: Optional[Dict] = None, expect_empty_response: bool = False) -> Any:
    """
    Makes an HTTP request to the LinkedIn API.
    """
    url = f"{LINKEDIN_API_BASE}{endpoint}"
    headers = _get_linkedin_headers()
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.request(method, url, json=json_data) as response:
                response.raise_for_status()
                if expect_empty_response:
                    if response.status in [200, 201, 204]:
                        return None
                    else:
                        logger.warning(f"Expected empty response for {method} {endpoint}, but got status {response.status}")
                        try:
                            return await response.json()
                        except aiohttp.ContentTypeError:
                            return await response.text()
                else:
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        return await response.json()
                    else:
                        text_content = await response.text()
                        logger.warning(f"Received non-JSON response for {method} {endpoint}: {text_content[:100]}...")
                        return {"raw_content": text_content}
        except aiohttp.ClientResponseError as e:
            logger.error(f"LinkedIn API request failed: {e.status} {e.message} for {method} {url}")
            error_details = e.message
            try:
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                pass
            raise RuntimeError(f"LinkedIn API Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during LinkedIn API request: {e}")
            raise RuntimeError(f"Unexpected error during API call to {method} {url}") from e

async def get_profile_info(person_id: Optional[str] = None) -> Dict[str, Any]:
    """Get LinkedIn profile information. If person_id is None, gets current user's profile."""
    logger.info(f"Executing tool: get_profile_info with person_id: {person_id}")
    try:
        if person_id:
            endpoint = f"/people/id={person_id}"
        else:
            endpoint = "/people/~"
        
        # Get basic profile info
        profile_data = await _make_linkedin_request("GET", endpoint)
        
        profile_info = {
            "id": profile_data.get("id"),
            "firstName": profile_data.get("localizedFirstName"),
            "lastName": profile_data.get("localizedLastName"),
            "headline": profile_data.get("localizedHeadline"),
            "location": profile_data.get("geoLocation", {}).get("geoUrn"),
            "industry": profile_data.get("industryName"),
            "profilePicture": profile_data.get("profilePicture", {}).get("displayImage")
        }
        
        return profile_info
    except Exception as e:
        logger.exception(f"Error executing tool get_profile_info: {e}")
        raise e

async def create_text_post(text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
    """Create a text post on LinkedIn."""
    logger.info(f"Executing tool: create_text_post")
    try:
        # First get the current user's person URN
        profile = await _make_linkedin_request("GET", "/people/~")
        person_urn = f"urn:li:person:{profile.get('id')}"
        
        endpoint = "/ugcPosts"
        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        post_data = await _make_linkedin_request("POST", endpoint, json_data=payload)
        return {
            "id": post_data.get("id"),
            "created": post_data.get("created"),
            "lastModified": post_data.get("lastModified"),
            "lifecycleState": post_data.get("lifecycleState")
        }
    except Exception as e:
        logger.exception(f"Error executing tool create_text_post: {e}")
        raise e

async def create_article_post(title: str, text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
    """Create an article post on LinkedIn."""
    logger.info(f"Executing tool: create_article_post")
    try:
        # Get the current user's person URN
        profile = await _make_linkedin_request("GET", "/people/~")
        person_urn = f"urn:li:person:{profile.get('id')}"
        
        endpoint = "/ugcPosts"
        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": f"{title}\n\n{text}"
                    },
                    "shareMediaCategory": "ARTICLE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        post_data = await _make_linkedin_request("POST", endpoint, json_data=payload)
        return {
            "id": post_data.get("id"),
            "created": post_data.get("created"),
            "lastModified": post_data.get("lastModified"),
            "lifecycleState": post_data.get("lifecycleState")
        }
    except Exception as e:
        logger.exception(f"Error executing tool create_article_post: {e}")
        raise e

async def get_user_posts(person_id: Optional[str] = None, count: int = 10) -> List[Dict[str, Any]]:
    """Get recent posts from a user's profile."""
    logger.info(f"Executing tool: get_user_posts with person_id: {person_id}, count: {count}")
    try:
        if person_id:
            author_urn = f"urn:li:person:{person_id}"
        else:
            profile = await _make_linkedin_request("GET", "/people/~")
            author_urn = f"urn:li:person:{profile.get('id')}"
        
        count = max(1, min(count, 50))  # Clamp between 1 and 50
        endpoint = f"/ugcPosts?q=authors&authors={urllib.parse.quote(author_urn)}&count={count}"
        
        posts_data = await _make_linkedin_request("GET", endpoint)
        
        if not isinstance(posts_data.get("elements"), list):
            logger.error(f"Unexpected response type for get_user_posts: {type(posts_data)}")
            return [{"error": "Received unexpected data format for posts."}]
        
        posts_list = []
        for post in posts_data.get("elements", []):
            specific_content = post.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {})
            commentary = specific_content.get("shareCommentary", {})
            
            posts_list.append({
                "id": post.get("id"),
                "text": commentary.get("text", ""),
                "created": post.get("created", {}).get("time"),
                "lastModified": post.get("lastModified", {}).get("time"),
                "lifecycleState": post.get("lifecycleState"),
                "mediaCategory": specific_content.get("shareMediaCategory"),
                "visibility": post.get("visibility", {})
            })
        
        return posts_list
    except Exception as e:
        logger.exception(f"Error executing tool get_user_posts: {e}")
        raise e

async def get_network_updates(count: int = 20) -> List[Dict[str, Any]]:
    """Get network updates from LinkedIn feed."""
    logger.info(f"Executing tool: get_network_updates with count: {count}")
    try:
        count = max(1, min(count, 50))  # Clamp between 1 and 50
        endpoint = f"/networkUpdates?count={count}"
        
        updates_data = await _make_linkedin_request("GET", endpoint)
        
        if not isinstance(updates_data.get("elements"), list):
            logger.error(f"Unexpected response type for get_network_updates: {type(updates_data)}")
            return [{"error": "Received unexpected data format for network updates."}]
        
        updates_list = []
        for update in updates_data.get("elements", []):
            update_content = update.get("updateContent", {})
            
            updates_list.append({
                "updateType": update.get("updateType"),
                "timestamp": update.get("timestamp"),
                "actor": update.get("updateContent", {}).get("person"),
                "content": update_content
            })
        
        return updates_list
    except Exception as e:
        logger.exception(f"Error executing tool get_network_updates: {e}")
        raise e

async def search_people(keywords: str, count: int = 10) -> List[Dict[str, Any]]:
    """Search for people on LinkedIn."""
    logger.info(f"Executing tool: search_people with keywords: {keywords}")
    try:
        count = max(1, min(count, 50))  # Clamp between 1 and 50
        encoded_keywords = urllib.parse.quote(keywords)
        endpoint = f"/peopleSearch?keywords={encoded_keywords}&count={count}"
        
        search_data = await _make_linkedin_request("GET", endpoint)
        
        if not isinstance(search_data.get("elements"), list):
            logger.error(f"Unexpected response type for search_people: {type(search_data)}")
            return [{"error": "Received unexpected data format for people search."}]
        
        people_list = []
        for person in search_data.get("elements", []):
            people_list.append({
                "id": person.get("id"),
                "firstName": person.get("localizedFirstName"),
                "lastName": person.get("localizedLastName"),
                "headline": person.get("localizedHeadline"),
                "location": person.get("geoLocation", {}).get("geoUrn"),
                "industry": person.get("industryName"),
                "profilePicture": person.get("profilePicture", {}).get("displayImage")
            })
        
        return people_list
    except Exception as e:
        logger.exception(f"Error executing tool search_people: {e}")
        raise e

async def get_company_info(company_id: str) -> Dict[str, Any]:
    """Get information about a company."""
    logger.info(f"Executing tool: get_company_info with company_id: {company_id}")
    try:
        endpoint = f"/companies/{company_id}"
        company_data = await _make_linkedin_request("GET", endpoint)
        
        company_info = {
            "id": company_data.get("id"),
            "name": company_data.get("localizedName"),
            "description": company_data.get("localizedDescription"),
            "website": company_data.get("localizedWebsite"),
            "industry": company_data.get("industries"),
            "companyType": company_data.get("companyType"),
            "headquarter": company_data.get("headquarter"),
            "foundedOn": company_data.get("foundedOn"),
            "specialities": company_data.get("specialities"),
            "logo": company_data.get("logoV2", {}).get("original")
        }
        
        return company_info
    except Exception as e:
        logger.exception(f"Error executing tool get_company_info: {e}")
        raise e

@click.command()
@click.option("--port", default=LINKEDIN_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("linkedin-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="linkedin_get_profile_info",
                description="Get LinkedIn profile information. If person_id is not provided, gets current user's profile.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "person_id": {
                            "type": "string",
                            "description": "The LinkedIn person ID to retrieve information for. Leave empty for current user."
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_create_text_post",
                description="Create a text post on LinkedIn.",
                inputSchema={
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text content of the post."
                        },
                        "visibility": {
                            "type": "string",
                            "description": "Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN_USERS).",
                            "default": "PUBLIC"
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_create_article_post",
                description="Create an article post on LinkedIn.",
                inputSchema={
                    "type": "object",
                    "required": ["title", "text"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the article."
                        },
                        "text": {
                            "type": "string",
                            "description": "The content/body of the article."
                        },
                        "visibility": {
                            "type": "string",
                            "description": "Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN_USERS).",
                            "default": "PUBLIC"
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_get_user_posts",
                description="Get recent posts from a user's profile (default 10, max 50).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "person_id": {
                            "type": "string",
                            "description": "The LinkedIn person ID. Leave empty for current user's posts."
                        },
                        "count": {
                            "type": "integer",
                            "description": "The number of posts to retrieve (1-50).",
                            "default": 10
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_get_network_updates",
                description="Get network updates from LinkedIn feed (default 20, max 50).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "The number of updates to retrieve (1-50).",
                            "default": 20
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_search_people",
                description="Search for people on LinkedIn.",
                inputSchema={
                    "type": "object",
                    "required": ["keywords"],
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords to search for in people's profiles."
                        },
                        "count": {
                            "type": "integer",
                            "description": "The number of results to return (1-50).",
                            "default": 10
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_get_company_info",
                description="Get information about a LinkedIn company.",
                inputSchema={
                    "type": "object",
                    "required": ["company_id"],
                    "properties": {
                        "company_id": {
                            "type": "string",
                            "description": "The LinkedIn company ID to retrieve information for."
                        }
                    }
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        if name == "linkedin_get_profile_info":
            person_id = arguments.get("person_id")
            result = await get_profile_info(person_id)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "linkedin_create_text_post":
            text = arguments.get("text")
            visibility = arguments.get("visibility", "PUBLIC")
            result = await create_text_post(text, visibility)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "linkedin_create_article_post":
            title = arguments.get("title")
            text = arguments.get("text")
            visibility = arguments.get("visibility", "PUBLIC")
            result = await create_article_post(title, text, visibility)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "linkedin_get_user_posts":
            person_id = arguments.get("person_id")
            count = arguments.get("count", 10)
            result = await get_user_posts(person_id, count)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "linkedin_get_network_updates":
            count = arguments.get("count", 20)
            result = await get_network_updates(count)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "linkedin_search_people":
            keywords = arguments.get("keywords")
            count = arguments.get("count", 10)
            result = await search_people(keywords, count)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "linkedin_get_company_info":
            company_id = arguments.get("company_id")
            result = await get_company_info(company_id)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
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