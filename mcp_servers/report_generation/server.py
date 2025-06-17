import contextlib
import logging
import os
from collections.abc import AsyncIterator
from typing import List, Dict, Any, Optional, Annotated

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
import anthropic
import requests
from supabase import create_client, Client
from pydantic import Field

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")

SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY")
if not SUPABASE_API_KEY:
    raise ValueError("SUPABASE_API_KEY environment variable is required")

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
if not FIRECRAWL_API_KEY:
    raise ValueError("FIRECRAWL_API_KEY environment variable is required")

REPORT_GENERATION_MCP_SERVER_PORT = int(os.getenv("REPORT_GENERATION_MCP_SERVER_PORT", "5000"))

# Report generation prompt template
REPORT_GENERATION_PROMPT = """You are a world class web report generation agent build by Klavis AI.
I want you to create a visually appealing javascript web page that presents the key information from these articles in an organized, modern layout. 

Most importantly, the entire code will be dynamically rendered in a iframe, so it MUST be compatible with that.
To avoid long loading times, DO NOT use more than 4 external libraries.
To avoid output being too long, DO NOT use more than 4000 tokens in the code block.

Also, the page should:
1. Extract the main headline, subtitle, and key points from the article
2. Create a card-based layout with distinct sections (e.g. summary, details, implications, learnings, etc)
3. Include appropriate icons for each section (e.g. beaker for methodology, trophy for achievements, etc.)
4. Add a simple data visualization if the article contains statistics or comparative data
5. Use a clean color scheme with section color-coding
6. Be responsive and follow modern web design principle
7. When appropriate, add reference links to the original articles in the report content.
7. Only return one complete code block and start the code block with "```html" and end with "```"

Generate the complete javascript code including:
- All necessary component
- CSS styling (preferably using styled-components or CSS modules)
- Any JavaScript needed for interactivity
- Mock data implementation based on the article content
- Fit into an iframe directly.

Here are the articles to transform:
{article_content}
"""

async def generate_report_with_claude(article_content: str) -> str:
    """
    Generate web report using Claude 3.7

    Args:
        article_content: The content of the article

    Returns:
        The generated JavaScript code
    """
    try:
        prompt = REPORT_GENERATION_PROMPT.format(article_content=article_content)

        anthropic_client = anthropic.AsyncClient(api_key=ANTHROPIC_API_KEY)
        generated_text = ""

        # Anthropic recommends using streaming for long responses:
        # https://docs.anthropic.com/en/api/errors#long-requests
        async with anthropic_client.messages.stream(
            model="claude-3-7-sonnet-latest",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                generated_text += text

        # Extract code from markdown code blocks if present
        start_index = generated_text.find("```html") + 7
        end_index = generated_text.rfind("```")

        if start_index >= 7 and end_index > start_index:
            return generated_text[start_index:end_index].strip()

        # Fallback: if no code block is found, return the raw text
        logger.warning(
            f"No code block found in generated text: start_index: {start_index}, end_index: {end_index}"
        )
        return generated_text[start_index:].strip()

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise

async def store_report_in_supabase(html_content: str) -> Dict[str, Any]:
    """
    Store the generated report in Supabase

    Args:
        html_content: The generated HTML/JS content

    Returns:
        The database record
    """
    # Initialize clients
    supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
    if not supabase:
        logger.error("Supabase client not initialized")
        return {"id": None}

    try:
        result = (
            supabase.table("generated_reports")
            .insert(
                {
                    "content": html_content,
                }
            )
            .execute()
        )

        return result.data[0]["id"]

    except Exception as e:
        logger.error(f"Error storing report: {str(e)}")
        raise

def search_firecrawl(query: str, limit: int = 3) -> List[str]:
    """
    Search for URLs using Firecrawl search API

    Args:
        query: Search query
        limit: Maximum number of results to return

    Returns:
        List of URLs from search results
    """
    try:
        url = "https://api.firecrawl.dev/v1/search"

        payload = {
            "query": query,
            "limit": limit,
            "lang": "en",
            "country": "us",
            "timeout": 240000,
            "scrapeOptions": {
                "formats": ["markdown"],
            },
        }

        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        search_results = response.json()
        results = {}

        # Extract URLs from search results
        for data in search_results.get("data", []):
            url = data.get("url", "")
            results[url] = {}
            results[url]["title"] = data.get("title", "")
            results[url]["content"] = data.get("markdown", "")

        return results

    except Exception as e:
        logger.error(f"Error in search_firecrawl: {str(e)}")
        raise

async def generate_web_reports(
    query: Annotated[
        str,
        Field(description="Search query to find relevant articles for the report."),
    ],
) -> str:
    """Generate web reports based on a search query.

    Searches for relevant articles using the query, creates a visually appealing
    JavaScript web page that consolidates content from the top search results.

    Returns:
        A URL to the generated report. The url will be http://www.klavis.ai/generated-reports/{report_id}.
    """
    try:
        logger.info(f"Executing tool: generate_web_reports with query: {query}")
        
        # 1. Search for relevant URLs
        url_to_content = search_firecrawl(query)

        all_articles = ""
        for url, content in url_to_content.items():
            all_articles += f"Article URL: {url}\nArticle Title: {content['title']}\nArticle Content: {content['content']}\n\n"

        # 2. Generate report
        generated_code = await generate_report_with_claude(all_articles)

        # 3. Store in Supabase
        report_id = await store_report_in_supabase(generated_code)

        return f"Report generated successfully. Please return the url to the user so that they can view the report at http://www.klavis.ai/generated-reports/{report_id}"
    except Exception as e:
        logger.error(f"Error in generate_web_reports: {str(e)}")
        return f"Error generating report: {str(e)}"

@click.command()
@click.option("--port", default=REPORT_GENERATION_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("report-generation-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="generate_web_reports",
                description="Generate web reports based on a search query. Searches for relevant articles using the query, creates a visually appealing JavaScript web page that consolidates content from the top search results.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant articles for the report.",
                        },
                    },
                },
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        if name == "generate_web_reports":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            try:
                result = await generate_web_reports(query)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
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
