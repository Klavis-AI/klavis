import os
import logging
import contextlib
import ssl
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

# Create SSL context that doesn't verify certificates (for development/testing)
def _get_ssl_context():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context

# Helper to make API requests and handle errors
async def _make_linkedin_request(method: str, endpoint: str, json_data: Optional[Dict] = None, expect_empty_response: bool = False) -> Any:
    """
    Makes an HTTP request to the LinkedIn API.
    """
    url = f"{LINKEDIN_API_BASE}{endpoint}"
    headers = _get_linkedin_headers()
    
    connector = aiohttp.TCPConnector(ssl=_get_ssl_context())
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
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
            # Note: Getting other users' profile info requires additional permissions
            return {"error": "Getting other users' profile information requires elevated LinkedIn API permissions"}
        else:
            # Use the working userinfo endpoint for current user
            endpoint = "/userinfo"
        
        # Get basic profile info
        profile_data = await _make_linkedin_request("GET", endpoint)
        
        profile_info = {
            "id": profile_data.get("sub"),
            "firstName": profile_data.get("given_name"),
            "lastName": profile_data.get("family_name"),
            "name": profile_data.get("name"),
            "email": profile_data.get("email"),
            "email_verified": profile_data.get("email_verified"),
            "locale": profile_data.get("locale")
        }
        
        return profile_info
    except Exception as e:
        logger.exception(f"Error executing tool get_profile_info: {e}")
        raise e

async def create_text_post(text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
    """Create a text post on LinkedIn."""
    logger.info(f"Executing tool: create_text_post")
    try:
        # Check if we have w_member_social scope by trying to post
        profile = await _make_linkedin_request("GET", "/userinfo")
        person_id = profile.get('sub')
        
        endpoint = "/ugcPosts"
        payload = {
            "author": f"urn:li:person:{person_id}",
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
        return {
            "error": "Post creation failed - likely due to insufficient permissions",
            "text": text,
            "note": "Requires 'w_member_social' scope in LinkedIn app settings",
            "exception": str(e)
        }

async def create_article_post(title: str, text: str, visibility: str = "PUBLIC") -> Dict[str, Any]:
    """Create an article post on LinkedIn."""
    logger.info(f"Executing tool: create_article_post")
    try:
        # Get current user info
        profile = await _make_linkedin_request("GET", "/userinfo")
        person_id = profile.get('sub')
        
        # Use the same format as text posts but with longer content
        endpoint = "/ugcPosts"
        payload = {
            "author": f"urn:li:person:{person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": f"{title}\n\n{text}"
                    },
                    "shareMediaCategory": "NONE"  # Changed from "ARTICLE" to "NONE"
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
            "lifecycleState": post_data.get("lifecycleState"),
            "title": title,
            "note": "Created as text post with article format (title + content)"
        }
    except Exception as e:
        logger.exception(f"Error executing tool create_article_post: {e}")
        return {
            "error": "Article creation failed - trying alternative approach",
            "title": title,
            "text": text,
            "note": "Will attempt to create as formatted text post",
            "exception": str(e)
        }

async def get_user_posts(person_id: Optional[str] = None, count: int = 10) -> List[Dict[str, Any]]:
    """Get recent posts from a user's profile."""
    logger.info(f"Executing tool: get_user_posts with person_id: {person_id}, count: {count}")
    try:
        if person_id:
            author_urn = f"urn:li:person:{person_id}"
        else:
            # Get current user's info
            profile = await _make_linkedin_request("GET", "/userinfo")
            author_urn = f"urn:li:person:{profile.get('sub')}"
        
        count = max(1, min(count, 50))  # Clamp between 1 and 50
        
        # Try the ugcPosts endpoint first
        endpoint = f"/ugcPosts?q=authors&authors={urllib.parse.quote(author_urn)}&count={count}"
        
        try:
            posts_data = await _make_linkedin_request("GET", endpoint)
            
            if not isinstance(posts_data.get("elements"), list):
                # If ugcPosts doesn't work, try shares endpoint
                endpoint = f"/shares?q=owners&owners={urllib.parse.quote(author_urn)}&count={count}"
                posts_data = await _make_linkedin_request("GET", endpoint)
            
            if not isinstance(posts_data.get("elements"), list):
                return [{
                    "error": "No posts found or API format changed",
                    "note": "The LinkedIn API may have changed or no posts are available",
                    "requested_person_id": person_id,
                    "requested_count": count,
                    "attempted_endpoints": ["/ugcPosts", "/shares"]
                }]
            
            posts_list = []
            for post in posts_data.get("elements", []):
                # Handle both ugcPosts and shares format
                if "specificContent" in post:  # ugcPosts format
                    specific_content = post.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {})
                    commentary = specific_content.get("shareCommentary", {})
                    text = commentary.get("text", "")
                else:  # shares format
                    text_content = post.get("text", {})
                    text = text_content.get("text", "") if isinstance(text_content, dict) else ""
                
                posts_list.append({
                    "id": post.get("id"),
                    "text": text,
                    "created": post.get("created", {}).get("time") if isinstance(post.get("created"), dict) else post.get("created"),
                    "lastModified": post.get("lastModified", {}).get("time") if isinstance(post.get("lastModified"), dict) else post.get("lastModified"),
                    "lifecycleState": post.get("lifecycleState"),
                    "activity": post.get("activity")
                })
            
            return posts_list if posts_list else [{
                "info": "No posts found for this user",
                "note": "User may not have any posts or posts may not be publicly accessible"
            }]
            
        except Exception as api_error:
            return [{
                "error": "Getting user posts failed with current permissions",
                "note": "This feature may require elevated LinkedIn API access",
                "requested_person_id": person_id,
                "requested_count": count,
                "api_error": str(api_error)
            }]
            
    except Exception as e:
        logger.exception(f"Error executing tool get_user_posts: {e}")
        return [{
            "error": "Function execution failed",
            "exception": str(e),
            "requested_person_id": person_id,
            "requested_count": count
        }]

async def get_network_updates(count: int = 20) -> List[Dict[str, Any]]:
    """Get network updates from LinkedIn feed."""
    logger.info(f"Executing tool: get_network_updates with count: {count}")
    try:
        return [{
            "error": "Getting network updates is not available with current LinkedIn API permissions",
            "note": "This feature requires elevated LinkedIn API access or LinkedIn Marketing API",
            "requested_count": count
        }]
    except Exception as e:
        logger.exception(f"Error executing tool get_network_updates: {e}")
        raise e

async def search_people(keywords: str, count: int = 10) -> List[Dict[str, Any]]:
    """Search for people on LinkedIn (Note: LinkedIn has restricted search APIs)."""
    logger.info(f"Executing tool: search_people with keywords: {keywords}")
    try:
        # Note: LinkedIn's people search API is heavily restricted and may not be available
        # with standard access tokens. This function may return limited results or errors.
        return [{"info": f"LinkedIn people search is restricted. Searched for: {keywords}", "note": "This feature requires special LinkedIn partnership access."}]
    except Exception as e:
        logger.exception(f"Error executing tool search_people: {e}")
        raise e

async def get_company_info(company_id: str) -> Dict[str, Any]:
    """Get information about a company."""
    logger.info(f"Executing tool: get_company_info with company_id: {company_id}")
    try:
        # Try different company endpoint formats
        endpoints_to_try = [
            f"/companies/{company_id}",
            f"/companies/{company_id}:(id,name,description,website-url,industry,company-type,headquarter,founded-on,specialities,logo)",
            f"/companies/{company_id}:(id,localizedName,localizedDescription,localizedWebsite)",
            f"/organizations/{company_id}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                company_data = await _make_linkedin_request("GET", endpoint)
                
                # If we get data, format it nicely
                company_info = {
                    "id": company_data.get("id"),
                    "name": company_data.get("localizedName") or company_data.get("name"),
                    "description": company_data.get("localizedDescription") or company_data.get("description"),
                    "website": company_data.get("localizedWebsite") or company_data.get("website-url"),
                    "industry": company_data.get("industries") or company_data.get("industry"),
                    "companyType": company_data.get("companyType") or company_data.get("company-type"),
                    "headquarter": company_data.get("headquarter"),
                    "foundedOn": company_data.get("foundedOn") or company_data.get("founded-on"),
                    "specialities": company_data.get("specialities"),
                    "logo": company_data.get("logoV2", {}).get("original") if company_data.get("logoV2") else company_data.get("logo"),
                    "endpoint_used": endpoint,
                    "raw_data": company_data
                }
                
                return company_info
                
            except Exception as endpoint_error:
                logger.debug(f"Endpoint {endpoint} failed: {endpoint_error}")
                continue
        
        # If all endpoints failed, return informative error
        return {
            "error": "Could not retrieve company information",
            "note": "Company API may require elevated permissions or company ID may be invalid",
            "requested_company_id": company_id,
            "attempted_endpoints": endpoints_to_try,
            "suggestion": "Try using a known company ID like '1035' (Microsoft) or check LinkedIn Developer documentation"
        }
        
    except Exception as e:
        logger.exception(f"Error executing tool get_company_info: {e}")
        return {
            "error": "Function execution failed",
            "requested_company_id": company_id,
            "exception": str(e),
            "note": "Check if company ID is valid and API permissions are sufficient"
        }

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
